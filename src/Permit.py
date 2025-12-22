
def Permit_View_function(conn , input):
    cursor = None
    try:
        cursor = conn.cursor()
        query = """
            SELECT "user_id", "full_name", "username", "phone_number", "ext", "email", "avatar", "role_id", "created_at", "updated_at", "department_id", "factory_id", "language_id", "is_active", "last_active_at"
            FROM "User"
            ORDER BY "user_id" ASC
            """
        cursor.execute(query)
        rows = cursor.fetchall()
        data = []
        for row in rows:
            data.append({
                "user_id": row[0],
                "full_name": row[1],
                "username": row[2],
                "phone_number": row[3],
                "ext": row[4],
                "email": row[5],
                "avatar": row[6],
                "role_id": row[7],
                "created_at": row[8],
                "updated_at": row[9],
                "department_id": row[10],
                "factory_id": row[11],
                "language_id": row[12],
                "is_active": row[13],
                "last_active_at": row[14]
            })
        return data
    except Exception as e:
        print(f"Error checking permit: {str(e)}")
        return False
    finally:
        cursor.close()
def check_permit_WorkManagement_Processing(conn , user_id: str) -> bool:
    cursor = None
    try:
        require_role_id = 64
        require_department_id = [2008, 1000, 1005, 1015, 1021, 1020, 1019, 1017, 2003, 2005, 2007]
        cursor = conn.cursor()
        query = """
            SELECT "role_id", "department_id" FROM "User" WHERE "username" = %s
            """
        cursor.execute(query, (user_id,))
        permit = cursor.fetchone()
        if not permit:
            return False
        role_id, department_id = permit
        return role_id > require_role_id and department_id in require_department_id
    except Exception as e:
        print(f"Error checking permit: {str(e)}")
        return False
    finally:
        cursor.close()

def check_permit_WorkManagement_View(conn , user_id: str) -> bool:
    cursor = None
    try:
        require_role_id = 1
        # require_department_id = [2008, 1000, 1005, 1015, 1021, 1020, 1019, 1017, 2003, 2005, 2007]
        cursor = conn.cursor()
        query = """
            SELECT "role_id", "department_id" FROM "User" WHERE "username" = %s
            """
        cursor.execute(query, (user_id,))
        permit = cursor.fetchone()
        if not permit:
            return False
        role_id, department_id = permit
        return role_id >= require_role_id
    except Exception as e:
        print(f"Error checking permit: {str(e)}")
        return False
    finally:
        cursor.close()

def check_permit_WorkManagement_DML(conn , user_id: str) -> bool:
    cursor = None
    try:
        require_role_id = 64
        require_department_id = [2008, 1000, 1005, 1015, 1021, 1020, 1019, 1017, 2003, 2005, 2007]
        cursor = conn.cursor()
        query = """
            SELECT "role_id", "department_id" FROM "User" WHERE "username" = %s
            """
        cursor.execute(query, (user_id,))
        permit = cursor.fetchone()
        if not permit:
            return False
        role_id, department_id = permit
        print(f"Role ID: {role_id}, Department ID: {department_id}")
        return role_id >= require_role_id and department_id in require_department_id
    except Exception as e:
        print(f"Error checking permit: {str(e)}")
        return False
    finally:
        cursor.close()