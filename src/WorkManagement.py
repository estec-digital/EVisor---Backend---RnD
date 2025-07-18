import pandas as pd
from io import BytesIO
from minio import Minio
from pydantic import BaseModel
from typing import List, Optional
import numpy as np
import openpyxl
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
from datetime import datetime, timedelta
from openpyxl.styles import PatternFill, Border, Side
from fastapi.responses import JSONResponse
from openpyxl.styles import Alignment
from dateutil import parser

def WorkManagement_Processing_function(content: bytes, conn, user_id):
    try:
        df = pd.read_excel(BytesIO(content))
        date_columns = df.columns[8:]
        df["Số giờ"] = df[date_columns].max(axis=1)
        df_workmanagement = pd.DataFrame({
            "owner": user_id,
            "full_name": df["Tên nhân sự - filter"],
            "project_code": df["Mã dự án - filter"],
            "description": df["Mô tả công việc"],
            "start_date": df["Thời gian bắt đầu"],
            "end_date": df["Thời gian kết thúc"],
            "QTY": df["Số giờ"]
        })
        print(df_workmanagement)

        with conn.cursor() as cursor:
            cursor.execute('SELECT MAX("task_id") FROM "WorkManagement"')
            result = cursor.fetchone()
        max_task_id = result[0] if result[0] is not None else 0
        task_id = max_task_id + 1

        for _, row in df_workmanagement.iterrows():
            with conn.cursor() as cursor:
                # Kiểm tra xem bản ghi đã tồn tại chưa
                cursor.execute("""
                    SELECT task_id FROM "WorkManagement"
                    WHERE owner = %s AND full_name = %s AND project_code = %s AND start_date = %s AND end_date = %s
                """, (row['owner'], row['full_name'], row['project_code'], row['start_date'], row['end_date']))
                existing = cursor.fetchone()

                if existing:
                    # Nếu tồn tại → cập nhật
                    cursor.execute("""
                        UPDATE "WorkManagement"
                        SET full_name = %s,
                            project_code = %s,
                            description = %s,
                            start_date = %s,
                            end_date = %s,
                            QTY = %s
                        WHERE task_id = %s
                    """, (
                        row['full_name'],
                        row['project_code'],
                        row['description'],
                        row['start_date'],
                        row['end_date'],
                        row['QTY'],
                        existing[0]
                    ))
                else:
                    # Nếu chưa tồn tại → thêm mới
                    cursor.execute('SELECT MAX("task_id") FROM "WorkManagement"')
                    max_id = cursor.fetchone()[0] or 0
                    task_id = max_id + 1

                    cursor.execute("""
                        INSERT INTO "WorkManagement" 
                        ("task_id", "owner", "full_name", "project_code", "description", "start_date", "end_date", "QTY")
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        task_id,
                        row['owner'],
                        row['full_name'],
                        row['project_code'],
                        row['description'],
                        row['start_date'],
                        row['end_date'],
                        row['QTY']
                    ))
                conn.commit()

        return df_workmanagement.head(50)
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

def WorkManagement_View_function(input: BaseModel, conn):
    try:
        query = """
            SELECT "task_id", "full_name", "project_code", "description", "start_date", "end_date", "QTY"
            FROM "WorkManagement"
            WHERE "owner" = %s
        """
        filter = input.filter
        params = [input.owner]

        if filter.full_name:
            query += f" AND \"full_name\" = ANY(%s)"
            params.append(filter.full_name)

        if filter.project_code:
            query += f" AND \"project_code\" = ANY(%s)"
            params.append(filter.project_code)

        if filter.start_date and filter.end_date:
            start_date = str(filter.start_date.replace(tzinfo=None))
            end_date = str(filter.end_date.replace(tzinfo=None))
            print(start_date, end_date)
            query += ' AND "end_date" <= %s AND "start_date" >= %s'
            params.extend([end_date, start_date])
        
        print("query", query)
        print("params:", params)
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            result = cursor.fetchall()
            if result:
                df = pd.DataFrame(result, columns=["task_id", "full_name", "project_code", "description", "start_date", "end_date", "QTY"])
            else:
                return {
                    "status": "error",
                    "message": "Không có dữ liệu"
                }
        start_idx = (input.pagination - 1) * input.page_size
        end_idx = input.pagination * input.page_size
        return df.iloc[start_idx:end_idx].to_dict(orient="records")
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }