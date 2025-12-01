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
from decimal import Decimal
import os
from src.POD_TimeTracker import save_file_local, save_file_minio, generate_dataframe

def WorkManagement_Processing_function(content: bytes, conn, user_id, filename):
    try:
        # filename = os.path.splitext(filename)[0]
        df = pd.read_excel(BytesIO(content))
        print("DF:",df.tail(10))
        date_columns = df.columns[8:]
        # Tách số trước dấu |, chuyển về float
        df_numeric = df[date_columns].apply(
            lambda col: col.astype(str).str.split("|").str[0].str.strip()
        ).apply(pd.to_numeric, errors="coerce")
        df["Số giờ"] = df_numeric.max(axis=1, skipna=True).fillna(0)

        # Tách chữ sau dấu |, giữ nguyên dạng string
        df_location = df[date_columns].apply(lambda col: col.astype(str).str.split("|").str[-1].str.strip())
        # Lấy giá trị chữ đầu tiên không rỗng trong từng hàng
        df["Nơi làm việc"] = df_location.apply(lambda row: next((x for x in row if x and x != "nan"), None), axis=1)

        df_workmanagement = pd.DataFrame({
            "owner": user_id,
            "full_name": df["Tên nhân sự - filter"],
            "project_code": df["Mã dự án - filter"],
            "description": df["Mô tả công việc"],
            "start_date": df["Thời gian bắt đầu"],
            "end_date": df["Thời gian kết thúc"],
            "QTY": df["Số giờ"],
            "site": df["Nơi làm việc"],
            "status": 0
        })
        print("df_workmanagement:", df_workmanagement)

        with conn.cursor() as cursor:
            cursor.execute('SELECT MAX("task_id") FROM "WorkManagement"')
            result = cursor.fetchone()
        max_task_id = result[0] if result[0] is not None else 0
        task_id = max_task_id + 1

        # Check version
        with conn.cursor() as cursor:
            query_version = """
                SELECT "version" FROM "WorkManagement"
                WHERE "owner" = %s 
                ORDER BY "version" DESC
                LIMIT 1
            """
            cursor.execute(query_version, (df_workmanagement['owner'][0],))
            version_lastest = cursor.fetchone()
            if version_lastest is None:
                version = 1
            else:
                version = version_lastest[0] + 1
            print("version:", version)

        
        for _, row in df_workmanagement.iterrows():
            with conn.cursor() as cursor:
                query_insert = """
                    INSERT INTO "WorkManagement" 
                    ("owner", "full_name", "project_code", "description", "start_date", "end_date", "QTY", "site", "status", "version")
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING "task_id"
                """
                cursor.execute(query_insert, (
                    row['owner'],
                    row['full_name'],
                    row['project_code'],
                    row['description'],
                    row['start_date'],
                    row['end_date'],
                    row['QTY'],
                    row['site'], 
                    row['status'],
                    version
                ))
                task_id = cursor.fetchone()[0]
                print("task_id:", task_id)
        conn.commit()

        if version != 1:
            with conn.cursor() as cursor:
                query_last_version = '''
                    SELECT "owner", "full_name", "project_code", "description", "start_date", "end_date", "QTY", "site", "version"
                    FROM "WorkManagement"
                    WHERE "owner" = %s AND "version" = %s 
                '''
                cursor.execute(query_last_version, (user_id, version_lastest))
                df_last_version = pd.DataFrame(cursor.fetchall(), columns=["owner", "full_name", "project_code", "description", "start_date", "end_date", "QTY", "site", "version"])

                query_new_version = '''
                    SELECT "owner", "full_name", "project_code", "description", "start_date", "end_date", "QTY", "site", "version"
                    FROM "WorkManagement"
                    WHERE "owner" = %s AND "version" = %s 
                '''
                cursor.execute(query_new_version, (user_id, version))
                df_new_version = pd.DataFrame(cursor.fetchall(), columns=["owner", "full_name", "project_code", "description", "start_date", "end_date", "QTY", "site", "version"])

                df_group = pd.concat([df_last_version, df_new_version], ignore_index=True)
                df_updated = df_group[~df_group.duplicated(
                    subset=["full_name", "project_code", "description", "start_date", "end_date", "QTY", "site"],
                    keep=False
                )]
                print("df_updated", df_updated)     
            
            for _, row in df_updated.iterrows():
                print("row:", row['version'])
                print("version_lastest:", version_lastest)
                status = 5 if int(row['version']) == version_lastest[0] else 6
                print("status:", status)
                with conn.cursor() as cursor:
                    query_update_status = """
                        UPDATE "WorkManagement"
                        SET "status" = %s
                        WHERE "owner" = %s AND "full_name" = %s AND "project_code" = %s AND "start_date" = %s AND "end_date" = %s AND "QTY" = %s AND "site" = %s AND "version" = %s
                    """
                    cursor.execute(query_update_status, (
                        status,
                        row['owner'],
                        row['full_name'],
                        row['project_code'],
                        row['start_date'],
                        row['end_date'],
                        row['QTY'],
                        row['site'],
                        row['version']
                    ))
                    conn.commit()

        # for _, row in df_workmanagement.iterrows():
        #     with conn.cursor() as cursor:
        #         # Kiểm tra xem bản ghi đã tồn tại chưa
        #         cursor.execute("""
        #             SELECT "task_id", "full_name", "project_code", "start_date", "end_date", "QTY", "site", "description"  FROM "WorkManagement"
        #             WHERE "owner" = %s AND "full_name" = %s AND "project_code" = %s AND "description" = %s 
        #         """, (row['owner'], row['full_name'], row['project_code'], row['description']))
        #         existing = cursor.fetchone()
        #         print(existing)

        #         if existing:
        #             # Nếu tồn tại → cập nhật
        #             task_id_db, full_name_db, project_code_db, start_date_db, end_date_db, QTY_db, site_db, description_db = existing
        #             # Ep kieu de so sanh
        #             start_date_file = pd.to_datetime(row["start_date"]).date()
        #             end_date_file = pd.to_datetime(row["end_date"]).date()
        #             start_date_db = start_date_db.date()
        #             end_date_db = end_date_db.date()
        #             QTY_file = Decimal(str(row["QTY"])) 

        #             print(full_name_db, project_code_db, start_date_db, end_date_db, QTY_db, site_db)
        #             print(row["full_name"] != full_name_db , row["project_code"] != project_code_db , start_date_file != start_date_db , end_date_file != end_date_db , 
        #             QTY_file != QTY_db , row["site"] != site_db, row["description"] != description_db)
                    
        #             # Kiểm tra thay đổi
        #             changed = (
        #                 row["full_name"] != full_name_db or
        #                 row["project_code"] != project_code_db or
        #                 start_date_file != start_date_db or
        #                 end_date_file != end_date_db or
        #                 QTY_file != QTY_db or
        #                 (row["site"] or "").strip() != (site_db or "").strip() or
        #                 (row["description"] or "").strip() != (description_db or "").strip()
        #             )

        #             if changed:
        #                 # Nếu có thay đổi → status = 5
        #                 cursor.execute("""
        #                     INSERT INTO "WorkManagement" 
        #                     ("owner", "full_name", "project_code", "description", "start_date", "end_date", 
        #                     "QTY", "site", "status", "version")
        #                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        #                     RETURNING "task_id"
        #                 """, (
        #                     row['owner'], row['full_name'], row['project_code'], row['description'],
        #                     row['start_date'], row['end_date'], row['QTY'], row['site'],
        #                     5, version
        #                 ))
        #             else:
        #                 # Nếu không thay đổi → status = 0
        #                 cursor.execute("""
        #                     INSERT INTO "WorkManagement" 
        #                     ("owner", "full_name", "project_code", "description", "start_date", "end_date", 
        #                     "QTY", "site", "status", "version")
        #                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        #                     RETURNING "task_id"
        #                 """, (
        #                     row['owner'], row['full_name'], row['project_code'], row['description'],
        #                     row['start_date'], row['end_date'], row['QTY'], row['site'],
        #                     row['status'], version
        #                 ))
        #         else:
        #             cursor.execute("""
        #                 INSERT INTO "WorkManagement" 
        #                 ("owner", "full_name", "project_code", "description", "start_date", "end_date", "QTY", "site", "status", "version")
        #                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        #                 RETURNING "task_id"
        #             """, (
        #                 row['owner'],
        #                 row['full_name'],
        #                 row['project_code'],
        #                 row['description'],
        #                 row['start_date'],
        #                 row['end_date'],
        #                 row['QTY'],
        #                 row['site'], 
        #                 row['status'],
        #                 version
        #             ))
        #             new_id = cursor.fetchone()[0]
        #             print("Inserted new task_id:", new_id)
        #         conn.commit()
        

        return df_workmanagement.head(50)
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

def WorkManagement_View_function(input: BaseModel, conn):
    try:
        query = """
            SELECT "task_id", "full_name", "project_code", "description", "start_date", "end_date", "QTY", "site", "status", "version"
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

        # if filter.start_date and filter.end_date:
        #     start_date = str(filter.start_date.replace(tzinfo=None))
        #     end_date = str(filter.end_date.replace(tzinfo=None))
        #     print(start_date, end_date)
        #     query += ' AND "end_date" <= %s AND "start_date" >= %s'
        #     params.extend([end_date, start_date])

        if filter.start_date and filter.end_date:
            start_date = str(filter.start_date.replace(tzinfo=None))
            end_date = str(filter.end_date.replace(tzinfo=None))
            print(start_date, end_date)
            query += ' AND "start_date" <= %s AND "end_date" >= %s'
            params.extend([end_date, start_date])
        
        if filter.version:
            query += f" AND \"version\" = %s"
            params.append(filter.version)

        print("query", query)
        print("params:", params)
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            result = cursor.fetchall()
            if result:
                df = pd.DataFrame(result, columns=["task_id", "full_name", "project_code", "description", "start_date", "end_date", "QTY", "site", "status", "version"])
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

def WorkManagement_DML_Delete_function(input: BaseModel, conn):
    try:
        if input.form.id:
            for id in input.form.id:
                with conn.cursor() as cursor:
                    query = """DELETE FROM "WorkManagement" WHERE "task_id"=%s AND "owner"=%s"""
                    cursor.execute(query, (id, input.owner))
                    conn.commit()

            return {
                "status": "success",
                "message": f"Xóa WorkManagement task {input.form.id} thành công"
            }
        if input.form.full_name:
            with conn.cursor() as cursor:
                query = """DELETE FROM "WorkManagement" WHERE "full_name"=%s AND "owner"=%s"""
                cursor.execute(query, (input.form.full_name, input.owner))
                conn.commit()

            return {
                "status": "success",
                "message": f"Xóa WorkManagement {input.form.full_name} thành công"
            }
        if input.form.project_code:
            with conn.cursor() as cursor:
                query = """DELETE FROM "WorkManagement" WHERE "project_code"=%s AND "owner"=%s"""
                cursor.execute(query, (input.form.project_code, input.owner))
                conn.commit()

            return {
                "status": "success",
                "message": f"Xóa WorkManagement {input.form.project_code} thành công"
            }
        else:
            return {
                "status": "error",
                "message": f"Không có trường task_id"
            }
    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}

def WorkManagement_DML_Insert_function(input: BaseModel, conn):
    # try:
        with conn.cursor() as cursor:
            # Check version
            query_current_version = """
                SELECT MAX("version") FROM "WorkManagement" WHERE "owner" = %s
            """
            cursor.execute(query_current_version, (input.form.owner,))
            row = cursor.fetchone()
            current_version = row[0] if row and row[0] is not None else 1
            print("current_version:", current_version)

            # Check tồn tại
            query = """
                SELECT 1
                FROM "WorkManagement"
                WHERE "owner" = %s AND "full_name" = %s AND "project_code" = %s 
                      AND "description" = %s AND "start_date" = %s AND "end_date" = %s 
                      AND "QTY" = %s AND "site" = %s AND "status" = %s
                LIMIT 1
            """
            cursor.execute(query, (
                input.form.owner,
                input.form.full_name,
                input.form.project_code,
                input.form.description,
                input.form.start_date,
                input.form.end_date,
                input.form.QTY,
                input.form.site,
                input.form.status
            ))
            if cursor.fetchone():
                return {
                    "status": "error",
                    "message": "Task này đã tồn tại",
                }

            # Insert và lấy task_id tự động
            query = """
                INSERT INTO "WorkManagement" 
                ("owner", "full_name", "project_code", "description", 
                 "start_date", "end_date", "QTY", "site", "status", "version")
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING "task_id"
            """
            cursor.execute(query, (
                input.form.owner,
                input.form.full_name,
                input.form.project_code,
                input.form.description,
                input.form.start_date,
                input.form.end_date,
                input.form.QTY,
                input.form.site,
                input.form.status,
                current_version
            ))
            new_id = cursor.fetchone()[0]
            conn.commit()

            return {
                "status": "success",
                "message": "Thêm mới WorkManagement thành công",
                "id": new_id
            }

    # except Exception as e:
    #     conn.rollback()
    #     return {"status": "error", "message": str(e)}

    
def WorkManagement_DML_Update_function(input: BaseModel, conn):
    try:
        if input.form.id:
            for id in input.form.id:
                with conn.cursor() as cursor:
                    query = """
                        UPDATE "WorkManagement"
                        SET "owner" = %s,
                            "full_name" = %s,
                            "project_code" = %s,
                            "description" = %s,
                            "start_date" = %s,
                            "end_date" = %s,
                            "QTY" = %s,
                            "site" = %s,
                            "status" = %s
                        WHERE "task_id" = %s
                    """
                    cursor.execute(query, (
                        input.form.owner,
                        input.form.full_name,
                        input.form.project_code,
                        input.form.description,
                        input.form.start_date,
                        input.form.end_date,
                        input.form.QTY,
                        input.form.site,
                        input.form.status,
                        id
                    ))
                    conn.commit()

            return {
                "status": "success",
                "message": f"Cập nhật WorkManagement task {input.form.id} thành công"
            }
        else:
            return {
                "status": "error",
                "message": "Không có trường task_id"
            }

    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}


def WorkManagement_Download_function(input, conn, MINIO_BUCKET, minio_client):
    try:
        with conn.cursor() as cursor:
            query = """
                SELECT 
                    "full_name", 
                    "description", 
                    "start_date", 
                    "end_date", 
                    "QTY", 
                    "site", 
                    "project_code", 
                    "status"
                FROM "WorkManagement"
                WHERE "owner" = %s AND "version" = %s
            """
            cursor.execute(query, (input.owner, input.version))
            rows = cursor.fetchall()

        if not rows:    
            return {
                "status": "error",
                "message": "Không có bản ghi nào trong hệ thống."
            }

        # Lấy column name
        cols = [desc[0] for desc in cursor.description]

        # rows = list of tuples → convert to list of dict
        data = [dict(zip(cols, r)) for r in rows]

        # Group theo full_name → project_code → list task
        grouped = {}

        for row in data:
            name = row["full_name"]
            project = row["project_code"]

            if name not in grouped:
                grouped[name] = {}

            if project not in grouped[name]:
                grouped[name][project] = []

            grouped[name][project].append({
                "Mô tả công việc": row["description"],
                "Kế hoạch - Từ": row["start_date"].strftime("%Y-%m-%d") if isinstance(row["start_date"], datetime) else row["start_date"],
                "Kế hoạch - Đến": row["end_date"].strftime("%Y-%m-%d") if isinstance(row["end_date"], datetime) else row["end_date"],
                "QTY": row["QTY"],
                "Nơi làm việc": row["site"]
            })

        # Convert grouped → JSON output
        json_output = []
        for name, projects in grouped.items():
            json_output.append({
                "Tên nhân sự": name,
                "Dự án": [
                    {"Mã dự án": code, "Thông tin": tasks}
                    for code, tasks in projects.items()
                ]
            })

        print("json_output:", json_output)
        df = generate_dataframe(json_output, 0)
        df = df.sort_values(by=["Tên nhân sự", "Mã dự án", "Thời gian bắt đầu"]).reset_index(drop=True)
        df = df.drop_duplicates(subset=["Tên nhân sự", "Mã dự án", "Mô tả công việc", "Thời gian bắt đầu", "Thời gian kết thúc"]).reset_index(drop=True)
        output_path_local, overwork = save_file_local(df)
        output_path_minio = save_file_minio(minio_client, output_path_local)
        print("df_final:", df.head())
        path_file = output_path_minio.split(f"{MINIO_BUCKET}/")[-1] if f"{MINIO_BUCKET}/" in output_path_minio else output_path_minio
        url = minio_client.presigned_get_object(MINIO_BUCKET, path_file, expires=timedelta(seconds=3600))
        return {
            "status": "success",
            "data": url
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
