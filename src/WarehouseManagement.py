def WarehouseManagement_View_function(input, conn):
    try:
        cursor = conn.cursor()
        query = """ 
            SELECT * FROM "WS_WarehouseManagement" 
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        items = []
        for row in rows:
            item = {
                "ID": row[0],
                "device_code": row[1],
                "series_number": row[2],
                "product_name": row[3],
                "date_time": row[4],
                "location": row[5],
                "description": row[6],
                "branch": row[7],
                "origin": row[8],
                "entered_by": row[9],
                "type": row[10],
                "quantity": row[11],
                "unit": row[12],
                "status": row[13]
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

def WarehouseManagement_View_Detail_function(input, conn):
    try:
        cursor = conn.cursor()
        query = """ 
            SELECT * FROM "WS_WarehouseManagement" WHERE "ID" = %s
        """
        cursor.execute(query, (input.id,))
        row = cursor.fetchone()
        if row:
            item = {
                "ID": row[0],
                "device_code": row[1],
                "series_number": row[2],
                "product_name": row[3],
                "date_time": row[4],
                "location": row[5],
                "description": row[6],
                "branch": row[7],
                "origin": row[8],
                "entered_by": row[9],
                "type": row[10],
                "quantity": row[11],
                "unit": row[12],
                "status": row[13]
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

def WarehouseManagement_DML_Insert_function(input, conn):
    try:
        cursor = conn.cursor()
        query = """ 
            INSERT INTO "WS_WarehouseManagement" 
            ("device_code", "series_number", "product_name", "date_time", "location", "description", "brand", "origin", "entered_by", "type", "quantity", "unit", "status") 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
            RETURNING "ID"
        """
        cursor.execute(query, (
            input.form.device_code,
            input.form.series_number,
            input.form.product_name,
            input.form.date_time,
            input.form.location,
            input.form.description,
            input.form.brand,
            input.form.origin,
            input.form.entered_by,
            input.form.type,
            input.form.quantity,
            input.form.unit,
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

def WarehouseManagement_DML_Update_function(input, conn):
    try:
        cursor = conn.cursor()
        query = """ 
            UPDATE "WS_WarehouseManagement" 
            SET "device_code" = %s, "series_number" = %s, "product_name" = %s, "date_time" = %s, "location" = %s, "description" = %s, "brand" = %s, "origin" = %s, "entered_by" = %s, "type" = %s, "quantity" = %s, "unit" = %s, "status" = %s 
            WHERE "ID" = %s
        """
        cursor.execute(query, (
            input.form.device_code,
            input.form.series_number,
            input.form.product_name,
            input.form.date_time,
            input.form.location,
            input.form.description,
            input.form.brand,
            input.form.origin,
            input.form.entered_by,
            input.form.type,
            input.form.quantity,
            input.form.unit,
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

def WarehouseManagement_DML_Delete_function(input, conn):
    try:
        cursor = conn.cursor()
        query = """ 
            DELETE FROM "WS_WarehouseManagement" WHERE "ID" = %s
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