
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