import os
import pandas as pd
import numpy as np
from datetime import datetime

def Statistical_View_function(input, conn):
    try:
        cursor = conn.cursor()
        query = """ 
            SELECT * FROM "WS_Statistical" 
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        items = []
        for row in rows:
            item = {
                "id": row[0],
                "product_name": row[1],
                "description": row[2],
                "time": row[3],
                "part_no": row[4],
                "origin": row[5],
                "unit": row[6],
                "quantity": row[7],
                "seri_number": row[8],
                "status": row[9]
            }
            items.append(item)
        return {
            "status": "success",
            "data": items
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
    finally:
        cursor.close()

def Statistical_View_Detail_function(input, conn):
    try:
        cursor = conn.cursor()
        query = """ 
            SELECT * FROM "WS_Statistical" WHERE id = %s
        """
        cursor.execute(query, (input.id,))
        row = cursor.fetchone()
        if row:
            item = {
                "id": row[0],
                "product_name": row[1],
                "description": row[2],
                "time": row[3],
                "part_no": row[4],
                "origin": row[5],
                "unit": row[6],
                "quantity": row[7],
                "seri_number": row[8],
                "status": row[9]
            }
            return {
                "status": "success",
                "data": item
            }
        else:
            return {
                "status": "error",
                "message": f"Item with ID {input.id} not found."
            }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
    finally:
        cursor.close()

def Statistical_DML_Insert_function(input, conn):
    try:
        cursor = conn.cursor()
        query = """ 
            INSERT INTO "WS_Statistical" 
            ("product_name", "description", "time", "part_no", "origin", "unit", "quantity", "seri_number", "status") 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) 
            RETURNING id
        """
        cursor.execute(query, (
            input.form.product_name,
            input.form.description,
            input.form.time,
            input.form.part_no,
            input.form.origin,
            input.form.unit,
            input.form.quantity,
            input.form.seri_number,
            input.form.status
        ))
        new_id = cursor.fetchone()[0]
        conn.commit()
        return {
            "status": "success",
            "message": f"Đã thêm danh mục ID {new_id}.",
            "ID": new_id
        }
    except Exception as e:
        conn.rollback()
        return {
            "status": "error",
            "message": str(e)
        }
    finally:
        cursor.close()

def Statistical_DML_Update_function(input, conn):
    try:
        cursor = conn.cursor()
        query = """ 
            UPDATE "WS_Statistical" 
            SET "product_name" = %s, "description" = %s, "time" = %s, "part_no" = %s, "origin" = %s, "unit" = %s, "quantity" = %s, "seri_number" = %s, "status" = %s 
            WHERE id = %s
        """
        cursor.execute(query, (
            input.form.product_name,
            input.form.description,
            input.form.time,
            input.form.part_no,
            input.form.origin,
            input.form.unit,
            input.form.quantity,
            input.form.seri_number,
            input.form.status,
            input.form.id
        ))
        if cursor.rowcount == 0:
            return {
                "status": "error",
                "message": f"ID {input.form.id} không tồn tại."
            }
        conn.commit()
        return {
            "status": "success",
            "message": f"Đã cập nhật danh mục ID {input.form.id}."
        }
    except Exception as e:
        conn.rollback()
        return {
            "status": "error",
            "message": str(e)
        }
    finally:
        cursor.close()

def Statistical_DML_Delete_function(input, conn):
    try:
        cursor = conn.cursor()
        query = """ 
            DELETE FROM "WS_Statistical" WHERE id = %s
        """
        cursor.execute(query, (input.form.id,))
        if cursor.rowcount == 0:
            return {
                "status": "error",
                "message": f"ID {input.form.id} không tồn tại."
            }
        conn.commit()
        return {
            "status": "success",
            "message": f"Đã xóa danh mục ID {input.form.id}."
        }
    except Exception as e:
        conn.rollback()
        return {
            "status": "error",
            "message": str(e)
        }
    finally:
        cursor.close()

def Statistical_By_Date_function(input, conn):
    try:
        cursor = conn.cursor()
        query = """ 
            SELECT * 
            FROM "WS_Statistical"
            WHERE DATE(time) = %s; 
        """
        cursor.execute(query, (input.date,))
        rows = cursor.fetchall()  

        items = []
        for row in rows:
            item = {
                "id": row[0],
                "product_name": row[1],
                "description": row[2],
                "time": row[3],
                "part_no": row[4],
                "origin": row[5],
                "unit": row[6],
                "quantity": row[7],
                "seri_number": row[8],
                "status": row[9]
            }
            items.append(item)

        if items:
            return {
                "status": "success",
                "count": len(items),
                "data": items
            }
        else:
            return {
                "status": "error",
                "message": f"No items found for date {input.date}"
            }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
    finally:
        cursor.close()

def Statistical_Import_Excel_function(conn, file):
    try:
        filename = file.filename
        ext = os.path.splitext(filename)[1].lower()

        # Đọc file Excel/CSV
        if ext == ".xlsx":
            df = pd.read_excel(file.file, engine="openpyxl", header=1) 
        elif ext == ".xls":
            df = pd.read_excel(file.file, engine="xlrd", header=1)
        elif ext == ".csv":
            try:
                df = pd.read_csv(file.file, encoding="utf-8", header=0)
            except UnicodeDecodeError:
                df = pd.read_csv(file.file, encoding="latin1", header=0)
        else:
            return {"status": "error", "message": "Định dạng file không được hỗ trợ"}

        # Chuẩn hóa dữ liệu
        df = df.replace({np.nan: None})

        # Map lại cột Excel -> DB (tuỳ thuộc file Excel của bạn)
        df = df.rename(columns={
            "Descripton": "description",
            "Part No.": "part_no",
            "Origin": "origin",
            "Unit": "unit",
            "Qty": "quantity",
            "Seri number": "seri_number"
        })

        # Thêm cột auto
        if "time" in df.columns:
            df["time"] = pd.to_datetime(df["time"], dayfirst=True, errors="coerce")
            df["time"] = df["time"].where(df["time"].notnull(), None)
        else:
            df["time"] = datetime.now()

        df["status"] = 0

        # Insert vào DB
        cursor = conn.cursor()
        for _, row in df.iterrows():
            cursor.execute("""
                INSERT INTO "WS_Statistical"
                (product_name, description, time, part_no, origin, unit, quantity, seri_number, status)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                row.get("product_name"),
                row.get("description"),
                row.get("time"),
                row.get("part_no"),
                row.get("origin"),
                row.get("unit"),
                row.get("quantity"),
                row.get("seri_number"),
                row.get("status")
            ))

        conn.commit()

        return {
            "status": "success",
            "message": "Import dữ liệu thành công"
        }

    except Exception as e:
        return {
            "status": "error", 
            "message": str(e)
        }
    finally:
        cursor.close()