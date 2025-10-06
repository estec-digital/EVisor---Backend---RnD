import os
import pandas as pd
import numpy as np
from datetime import datetime
from psycopg2 import sql

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

### Warehouse - Import, Export ###

def WarehouseImportExport_View_function(conn, table_name: str):
    try:
        cursor = conn.cursor()

        if table_name not in ["WS_Import", "WS_Export"]:
            return {
                "status": "error",
                "message": f"Bảng '{table_name}' không được phép truy cập."
            }

        query = f'SELECT * FROM "{table_name}"'
        cursor.execute(query)
        rows = cursor.fetchall()

        items = []
        for row in rows:
            item = {
                "id": row[0],
                "import_export_id": row[1],
                "time": row[2],
                "import_export_time": row[3],
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

def WarehouseImportExport_View_Detail_function(input, conn, table_name: str):
    try:
        cursor = conn.cursor()

        query = sql.SQL("""
            SELECT * FROM {table} WHERE id = %s
        """).format(table=sql.Identifier(table_name))
        cursor.execute(query, (input.id,))
        row = cursor.fetchone()

        if row:
            item = {
                "id": row[0],
                f"{'import' if table_name == 'WS_Import' else 'export'}_id": row[1],
                "time": row[2],
                f"{'import' if table_name == 'WS_Import' else 'export'}_time": row[3],
                "project_code": row[4],
                "product_name": row[5],
                "part_no": row[6],
                "origin": row[7],
                "quantity": row[8],
                "seri_number": row[9]
            }
            return {"status": "success", "data": item}
        else:
            return {
                "status": "error",
                "message": f"Item with ID {input.id} not found."
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        cursor.close()

def WarehouseImportExport_DML_Insert_function(input, conn, option):
    try:
        cursor = conn.cursor()
        
        if option == "import":
            table_name = "WS_Import"
            id_field = "import_id"
            id_value = input.form.import_id
            time_field = "import_time"
            time_value = input.form.import_time
        elif option == "export":
            table_name = "WS_Export"
            id_field = "export_id"
            id_value = input.form.export_id
            time_field = "export_time"
            time_value = input.form.export_time
        else:
            return {
                "status": "error", 
                "message": "Option không hợp lệ. Chỉ hỗ trợ 'import' hoặc 'export'."
                }
        
        query = sql.SQL("""
            INSERT INTO {table} 
            ({id_field}, "time", {time_field}, "project_code", "product_name", "part_no", "origin", "quantity", "seri_number")
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """).format(
            table=sql.Identifier(table_name),
            id_field=sql.Identifier(id_field),
            time_field=sql.Identifier(time_field)
        )
        
        cursor.execute(query, (
            id_value,
            input.form.time,
            time_value,
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

def WarehouseImportExport_DML_Update_function(input, conn, option):
    try:
        cursor = conn.cursor()

        if option == "import":
            table_name = "WS_Import"
            id_field = "import_id"
            id_value = input.form.import_id
            time_field = "import_time"
            time_value = input.form.import_time
        elif option == "export":
            table_name = "WS_Export"
            id_field = "export_id"
            id_value = input.form.export_id
            time_field = "export_time"
            time_value = input.form.export_time
        else:
            return {
                "status": "error", 
                "message": "Option không hợp lệ. Chỉ hỗ trợ 'import' hoặc 'export'."
                }

        query = sql.SQL("""
            UPDATE {table}
            SET 
                {id_field} = %s, 
                "time" = %s, 
                {time_field} = %s, 
                "project_code" = %s, 
                "product_name" = %s, 
                "part_no" = %s, 
                "origin" = %s, 
                "quantity" = %s, 
                "seri_number" = %s
            WHERE id = %s
        """).format(
            table=sql.Identifier(table_name),
            id_field=sql.Identifier(id_field),
            time_field=sql.Identifier(time_field)
        )

        cursor.execute(query, (
            id_value,
            input.form.time,
            time_value,
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

def WarehouseImportExport_DML_Delete_function(input, conn, option):
    try:
        cursor = conn.cursor()

        if option == "import":
            table_name = "WS_Import"
        elif option == "export":
            table_name = "WS_Export"
        else:
            return {
                "status": "error", 
                "message": "Option không hợp lệ. Chỉ hỗ trợ 'import' hoặc 'export'."
                }

        query = sql.SQL("""
            DELETE FROM {table} WHERE id = %s
        """).format(
            table=sql.Identifier(table_name)
        )

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

def WarehouseImportExport_Upload_function(conn, file, option: str):
    cursor = None
    try:
        filename = file.filename
        ext = os.path.splitext(filename)[1].lower()

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
            return {"status": "error", "message": "Định dạng file không được hỗ trợ."}

        df = df.replace({np.nan: None})
        df = df.where(pd.notnull(df), None)

        df = df.rename(columns={
            "Thời gian": "time",
            "Mã Dự án": "project_code",
            "Tên hàng": "product_name",
            "Mã hàng": "part_no",
            "Hãng": "origin",
            "Số lượng": "quantity",
            "Seri No.": "seri_number"
        })

        if "time" in df.columns:
            df["time"] = pd.to_datetime(df["time"], errors="coerce")
            df["time"] = df["time"].replace({pd.NaT: None})

        now = datetime.now()
        if option == "import":
            table_name = "WS_Import"
            if "import_time" in df.columns:
                df["import_time"] = pd.to_datetime(df["import_time"], errors="coerce")
                df["import_time"] = df["import_time"].replace({pd.NaT: None})
            else:
                df["import_time"] = now  
            id_col = "import_id"
            time_col = "import_time"
        elif option == "export":
            table_name = "WS_Export"
            if "export_time" in df.columns:
                df["export_time"] = pd.to_datetime(df["export_time"], errors="coerce")
                df["export_time"] = df["export_time"].replace({pd.NaT: None})
            else:
                df["export_time"] = now  
            id_col = "export_id"
            time_col = "export_time"
        else:
            return {"status": "error", "message": f"Tùy chọn '{option}' không hợp lệ."}

        datetime_columns = ["time", time_col]
        for col in datetime_columns:
            if col in df.columns:
                df[col] = df[col].replace({pd.NaT: None})

        cursor = conn.cursor()
        for _, row in df.iterrows():
            time_value = row.get("time")
            time_col_value = row.get(time_col)
            
            if time_col not in df.columns and time_col_value is None:
                time_col_value = now
            
            values = (
                row.get(id_col),  
                time_value,         
                time_col_value,   
                row.get("project_code"),
                row.get("product_name"), 
                row.get("part_no"),
                row.get("origin"),
                row.get("quantity"),
                row.get("seri_number")
            )
            
            cursor.execute(f"""
                INSERT INTO "{table_name}"
                ({id_col}, time, {time_col}, project_code, product_name, part_no, origin, quantity, seri_number)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, values)

        conn.commit()
        return {"status": "success", "message": f"Tải dữ liệu {option} thành công."}

    except Exception as e:
        conn.rollback()
        return {
            "status": "error", 
            "message": str(e)}
    finally:
        if cursor:
            cursor.close()