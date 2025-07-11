import uuid
from datetime import datetime, timedelta

def Authentication_function(conn, input):
    """
    Authenticate a user based on the provided username and password.
    
    Args:
        conn: PostgreSQL connection object.
        input: Input data containing username and password.
    
    Returns:
        dict: Authentication result with status and message.
    """
    try:
        cursor = conn.cursor()
        query = """
            SELECT "username", "password", "avatar", "full_name" FROM "User" WHERE "username" = %s AND "password" = %s
            """
        cursor.execute(query, (input.username, input.password))
        user = cursor.fetchone()
        
        if user:
            session_id = str(uuid.uuid4())
            created_at = datetime.now()
            expires_at = created_at + timedelta(hours=8)

            delete_query = """
                DELETE FROM "Session" WHERE "user_id" = %s
                """
            cursor.execute(delete_query, (user[0],))
            conn.commit()

            insert_query = """
                INSERT INTO "Session" ("session_id", "user_id", "created_at", "expires_at")
                VALUES (%s, %s, %s, %s)
                """
            cursor.execute(insert_query, (session_id, user[0], created_at, expires_at))
            conn.commit()
            return {
                "status": "success", 
                "authentication": "success",
                "user_id": user[0],
                "avatar": user[2],
                "full_name": user[3],
                "message": "Đăng nhập thành công!",
                "session_id": session_id,
                "expires_at": expires_at
                }
        else:
            return {
                "status": "error", 
                "authentication": "failed",
                "message": "Tên đăng nhập hoặc mật khẩu không đúng!"
                }
    
    except Exception as e:
        return {
            "status": "error", 
            "message": str(e)
            }
    
    finally:
        cursor.close()
        conn.close()

def check_session(conn , user_id: str) -> bool:
    """
    Check if the session for the given user_id is valid.
    
    Args:
        user_id (str): The user ID to check the session for.
    
    Returns:
        bool: True if the session is valid, False otherwise.
    """
    try:
        cursor = conn.cursor()
        query = """
            SELECT "expires_at" FROM "Session" WHERE "user_id" = %s
            """
        cursor.execute(query, (user_id,))
        session = cursor.fetchone()
        
        if session and session[0] > datetime.now():
            return True
        else:
            return False
    
    except Exception as e:
        print(f"Error checking session: {str(e)}")
        return False
    
    finally:
        cursor.close()
        conn.close()

def Authentication_Logout_function(conn, input):
    try:
        user = input.username
        if user:
            cursor = conn.cursor()
            delete_query = """
                DELETE FROM "Session" WHERE "user_id" = %s
                """
            cursor.execute(delete_query, (user,))
            conn.commit()
            return {
                "status": "success", 
                "message": "Đăng xuất thành công!"
                }
    except Exception as e:
        return {
            "status": "error", 
            "message": str(e)
            }