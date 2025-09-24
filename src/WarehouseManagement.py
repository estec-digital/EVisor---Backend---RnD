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
                "product_id": row[1],
                "barcode": row[2],
                "product_name": row[3],
                "datetime": row[4],
                "location": row[5],
                "description": row[6],
                "branch": row[7],
                "seri": row[8],
                "origin": row[9],
                "entered_by": row[10],
                "type": row[11],
                "quantity": row[12],
                "unit": row[13],
                "status": row[14]
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
                "product_id": row[1],
                "barcode": row[2],
                "product_name": row[3],
                "datetime": row[4],
                "location": row[5],
                "description": row[6],
                "branch": row[7],
                "seri": row[8],
                "origin": row[9],
                "entered_by": row[10],
                "type": row[11],
                "quantity": row[12],
                "unit": row[13],
                "status": row[14]
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
            ("product_id", "barcode", "product_name", "datetime", "location", "description", "brand", "seri", "origin", "entered_by", "type", "quantity", "unit", "status") 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
            RETURNING "ID"
        """
        cursor.execute(query, (
            input.form.product_id,
            input.form.barcode,
            input.form.product_name,
            input.form.timestamp,
            input.form.location,
            input.form.description,
            input.form.brand,
            input.form.seri,
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
            SET "product_id" = %s, "barcode" = %s, "product_name" = %s, "datetime" = %s, "location" = %s, "description" = %s, "brand" = %s, "seri" = %s, "origin" = %s, "entered_by" = %s, "type" = %s, "quantity" = %s, "unit" = %s, "status" = %s 
            WHERE "ID" = %s
        """
        cursor.execute(query, (
            input.form.product_id,
            input.form.barcode,
            input.form.product_name,
            input.form.timestamp,
            input.form.location,
            input.form.description,
            input.form.brand,
            input.form.seri,
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