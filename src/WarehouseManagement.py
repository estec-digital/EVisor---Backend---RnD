import os
import pandas as pd
import numpy as np
from datetime import datetime

def WarehouseStatistical_View_function(input, conn):
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
                "location": row[9],
                "entered_by": row[10],
                "status": row[11]
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

def WarehouseStatistical_View_Detail_function(input, conn):
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
                "location": row[9],
                "entered_by": row[10],
                "status": row[11]
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

def WarehouseStatistical_DML_Insert_function(input, conn):
    try:
        cursor = conn.cursor()
        query = """ 
            INSERT INTO "WS_Statistical" 
            ("product_name", "description", "time", "part_no", "origin", "unit", "quantity", "seri_number", "location", "entered_by", "status") 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
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
            input.form.location,
            input.form.entered_by,
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

def WarehouseStatistical_DML_Update_function(input, conn):
    try:
        cursor = conn.cursor()
        query = """ 
            UPDATE "WS_Statistical" 
            SET "product_name" = %s, "description" = %s, "time" = %s, "part_no" = %s, "origin" = %s, "unit" = %s, "quantity" = %s, "seri_number" = %s, "location" = %s, "entered_by" = %s, "status" = %s 
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
            input.form.location,
            input.form.entered_by,
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

def WarehouseStatistical_DML_Delete_function(input, conn):
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

def WarehouseStatistical_Upload_function(conn, file):
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
                df = pd.read_csv(file.file, encoding="utf-8", header=1)
            except UnicodeDecodeError:
                df = pd.read_csv(file.file, encoding="latin1", header=1)
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
                (product_name, description, time, part_no, origin, unit, quantity, seri_number, location, entered_by, status)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                row.get("product_name"),
                row.get("description"),
                row.get("time"),
                row.get("part_no"),
                row.get("origin"),
                row.get("unit"),
                row.get("quantity"),
                row.get("seri_number"),
                row.get("location"),
                row.get("entered_by"),
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

### Warehouse - Import ###

def WarehouseImport_View_function(input, conn):
    try:
        cursor = conn.cursor()
        query = """ 
            SELECT * FROM "WS_Import" 
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        items = []
        for row in rows:
            item = {
                "id": row[0],
                "import_id": row[1],
                "time": row[2],
                "import_time": row[3],
                "project_code": row[4],
                "product_name": row[5],
                "part_no": row[6],
                "origin": row[7],
                "quantity": row[8],
                "seri_number": row[9]
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

def WarehouseImport_View_Detail_function(input, conn):
    try:
        cursor = conn.cursor()
        query = """ 
            SELECT * FROM "WS_Import" WHERE id = %s
        """
        cursor.execute(query, (input.id,))
        row = cursor.fetchone()
        if row:
            item = {
                "id": row[0],
                "import_id": row[1],
                "time": row[2],
                "import_time": row[3],
                "project_code": row[4],
                "product_name": row[5],
                "part_no": row[6],
                "origin": row[7],
                "quantity": row[8],
                "seri_number": row[9]
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

def WarehouseImport_DML_Insert_function(input, conn):
    try:
        cursor = conn.cursor()
        
        query = """ 
            INSERT INTO "WS_Import" 
            ("import_id", "time", "import_time", "project_code", "product_name", "part_no", "origin", "quantity", "seri_number") 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) 
            RETURNING id
        """
        cursor.execute(query, (
            input.form.import_id,
            input.form.time,
            input.form.import_time,
            input.form.project_code,
            input.form.product_name,
            input.form.part_no,
            input.form.origin,
            input.form.quantity,
            input.form.seri_number,
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

def WarehouseImport_DML_Update_function(input, conn):
    try:
        cursor = conn.cursor()
        query = """ 
            UPDATE "WS_Import" 
            SET "import_id" = %s, "time" = %s, "import_time" = %s, "project_code" = %s, "product_name" = %s, "part_no" = %s, "origin" = %s, "quantity" = %s, "seri_number" = %s
            WHERE id = %s
        """
        cursor.execute(query, (
            input.form.import_id,
            input.form.time,
            input.form.import_time,
            input.form.project_code,
            input.form.product_name,
            input.form.part_no,
            input.form.origin,
            input.form.quantity,
            input.form.seri_number,
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

def WarehouseImport_DML_Delete_function(input, conn):
    try:
        cursor = conn.cursor()
        query = """ 
            DELETE FROM "WS_Import" WHERE id = %s
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

def WarehouseImport_Upload_function(conn, file):
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
                df = pd.read_csv(file.file, encoding="utf-8", header=1)
            except UnicodeDecodeError:
                df = pd.read_csv(file.file, encoding="latin1", header=1)
        else:
            return {"status": "error", "message": "Định dạng file không được hỗ trợ"}

        # Chuẩn hóa dữ liệu
        df = df.replace({np.nan: None})

        # Map lại cột Excel -> DB (tuỳ thuộc file Excel của bạn)
        df = df.rename(columns={
            "Thời gian": "time",
            "Mã Dự án": "project_code",
            "Tên hàng": "product_name",
            "Mã hàng": "part_no",
            "Hãng": "origin",
            "Số lượng": "quantity",
            "Seri No.": "seri_number"
        })

        # Thêm cột auto
        if "import_time" in df.columns:
            df["import_time"] = pd.to_datetime(df["import_time"], dayfirst=True, errors="coerce")
            df["import_time"] = df["import_time"].where(df["import_time"].notnull(), None)
        else:
            df["import_time"] = datetime.now()

        # Insert vào DB
        cursor = conn.cursor()
        for _, row in df.iterrows():
            cursor.execute("""
                INSERT INTO "WS_Import"
                (import_id, time, import_time, project_code, product_name, part_no, origin, quantity, seri_number)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                row.get("import_id"),
                row.get("time"),
                row.get("import_time"),
                row.get("project_code"),
                row.get("product_name"),
                row.get("part_no"),
                row.get("origin"),
                row.get("quantity"),
                row.get("seri_number")
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

### Warehouse - Export ###

def WarehouseExport_View_function(input, conn):
    try:
        cursor = conn.cursor()
        query = """ 
            SELECT * FROM "WS_Export" 
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        items = []
        for row in rows:
            item = {
                "id": row[0],
                "export_id": row[1],
                "time": row[2],
                "export_time": row[3],
                "project_code": row[4],
                "product_name": row[5],
                "part_no": row[6],
                "origin": row[7],
                "quantity": row[8],
                "seri_number": row[9]
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

def WarehouseExport_View_Detail_function(input, conn):
    try:
        cursor = conn.cursor()
        query = """ 
            SELECT * FROM "WS_Export" WHERE id = %s
        """
        cursor.execute(query, (input.id,))
        row = cursor.fetchone()
        if row:
            item = {
                "id": row[0],
                "export_id": row[1],
                "time": row[2],
                "export_time": row[3],
                "project_code": row[4],
                "product_name": row[5],
                "part_no": row[6],
                "origin": row[7],
                "quantity": row[8],
                "seri_number": row[9]
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

def WarehouseExport_DML_Insert_function(input, conn):
    try:
        cursor = conn.cursor()
        
        query = """ 
            INSERT INTO "WS_Export" 
            ("export_id", "time", "export_time", "project_code", "product_name", "part_no", "origin", "quantity", "seri_number") 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) 
            RETURNING id
        """
        cursor.execute(query, (
            input.form.export_id,
            input.form.time,
            input.form.export_time,
            input.form.project_code,
            input.form.product_name,
            input.form.part_no,
            input.form.origin,
            input.form.quantity,
            input.form.seri_number,
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

def WarehouseExport_DML_Update_function(input, conn):
    try:
        cursor = conn.cursor()
        query = """ 
            UPDATE "WS_Export" 
            SET "export_id" = %s, "time" = %s, "export_time" = %s, "project_code" = %s, "product_name" = %s, "part_no" = %s, "origin" = %s, "quantity" = %s, "seri_number" = %s
            WHERE id = %s
        """
        cursor.execute(query, (
            input.form.export_id,
            input.form.time,
            input.form.export_time,
            input.form.project_code,
            input.form.product_name,
            input.form.part_no,
            input.form.origin,
            input.form.quantity,
            input.form.seri_number,
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

def WarehouseExport_DML_Delete_function(input, conn):
    try:
        cursor = conn.cursor()
        query = """ 
            DELETE FROM "WS_Export" WHERE id = %s
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

def WarehouseExport_Upload_function(conn, file):
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
                df = pd.read_csv(file.file, encoding="utf-8", header=1)
            except UnicodeDecodeError:
                df = pd.read_csv(file.file, encoding="latin1", header=1)
        else:
            return {"status": "error", "message": "Định dạng file không được hỗ trợ"}

        # Chuẩn hóa dữ liệu
        df = df.replace({np.nan: None})

        # Map lại cột Excel -> DB (tuỳ thuộc file Excel của bạn)
        df = df.rename(columns={
            "Thời gian": "time",
            "Mã Dự án": "project_code",
            "Tên hàng": "product_name",
            "Mã hàng": "part_no",
            "Hãng": "origin",
            "Số lượng": "quantity",
            "Seri No.": "seri_number"
        })

        # Thêm cột auto
        if "export_time" in df.columns:
            df["export_time"] = pd.to_datetime(df["export_time"], dayfirst=True, errors="coerce")
            df["export_time"] = df["export_time"].where(df["export_time"].notnull(), None)
        else:
            df["export_time"] = datetime.now()

        # Insert vào DB
        cursor = conn.cursor()
        for _, row in df.iterrows():
            cursor.execute("""
                INSERT INTO "WS_Export"
                (export_id, time, export_time, project_code, product_name, part_no, origin, quantity, seri_number)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                row.get("export_id"),
                row.get("time"),
                row.get("export_time"),
                row.get("project_code"),
                row.get("product_name"),
                row.get("part_no"),
                row.get("origin"),
                row.get("quantity"),
                row.get("seri_number")
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