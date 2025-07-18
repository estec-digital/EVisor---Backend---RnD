from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel, Field
from minio import Minio
import pandas as pd
from io import BytesIO
from dotenv import load_dotenv
import os
from typing import List, Optional
from datetime import datetime
from src.POD_TimeTracker import *
from src.Authentication import *
from src.DB_Connection import *
from src.WorkManagement import *
import uuid
from fastapi.middleware.cors import CORSMiddleware

# Tải biến môi trường từ file .env
load_dotenv()
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_SERVER = os.getenv("MINIO_SERVER")
MINIO_PORT_API_EXTERNAL = os.getenv("MINIO_PORT_API_EXTERNAL")
MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER")
MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD")
MINIO_BUCKET = os.getenv("MINIO_BUCKET")

POSTGRESQL_SERVER = os.getenv("POSTGRESQL_SERVER")
POSTGRES_PORT_EXTERNAL = os.getenv("POSTGRES_PORT_EXTERNAL")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/", tags=["Greeting"])
def read_root():
    return {"message": "Xin chào đây là API của EVisor!"}

# Cấu hình MinIO client
minio_client = Minio(
    endpoint=f"{MINIO_SERVER}:{MINIO_PORT_API_EXTERNAL}",
    access_key=f"{MINIO_ROOT_USER}",
    secret_key=f"{MINIO_ROOT_PASSWORD}",
    secure=False
)
print(minio_client)

postgres_db = {
    "host": POSTGRESQL_SERVER,
    "port": POSTGRES_PORT_EXTERNAL,
    "database": POSTGRES_DB,
    "user": POSTGRES_USER,
    "password": POSTGRES_PASSWORD
}

### POD ###
## TimeTracker
class POD_TimeTracker_Merge(BaseModel):
    request_id: str = Field(default="evisor-1234567890", example="evisor-1234567890")
    user_id: str = Field(default="hoanvlh", example="hoanvlh")
    start_time: datetime = Field(example="2025-06-23T15:20:00")
    path_files: List[str] = Field(example=["data/POD/TimeTracker/Input/Form mau 1.xlsx", "data/POD/TimeTracker/Input/Form mau 2.xlsx"])
    summary_file: Optional[str] = Field(default=None, example="data/POD/TimeTracker/Output/ES_20250704_104529.xlsx")

@app.post("/POD_TimeTracker_Merge", tags=["POD"])
def POD_TimeTracker_Merge_api(input: POD_TimeTracker_Merge):
    try:
        conn = get_postgres_connection(POSTGRESQL_SERVER, POSTGRES_PORT_EXTERNAL, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD)
        session = check_session(conn, input.user_id)
        if not session:
            return {
                "status": "error", 
                "message": "Phiên làm việc đã hết hạn hoặc không hợp lệ. Vui lòng đăng nhập lại."
                }
        else:
            if input.summary_file is None:
                return POD_TimeTracker_Merge_function(minio_client, input)
            else:
                return POD_TimeTracker_Merge_Manual_function(minio_client, input)
    except Exception as e:
        return {
            "status": "error", 
            "message": str(e)
            }

@app.post("/POD_TimeTracker_Upload", tags=["POD"])
async def POD_TimeTracker_Upload_api(files: List[UploadFile] = File(...)):
    try:
        uploaded_paths = []
        summary_file = ''
        for file in files:
            object_name = f"data/POD/TimeTracker/Input/{file.filename}"
            content = await file.read()
            minio_client.put_object(
                MINIO_BUCKET,
                object_name,
                BytesIO(content),
                length=len(content),
                content_type=file.content_type
            )
            issummary = issummary_file(content)
            if issummary:
                summary_file = object_name
            else:
                uploaded_paths.append(object_name)
        return {
            "status": "success",
            "path_files": uploaded_paths,
            "summary_file": summary_file
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
    
class POD_TimeTracker_Getfile(BaseModel):
    request_id: str = Field(default="evisor-1234567890", example="evisor-1234567890")
    user_id: str = Field(default="hoanvlh", example="hoanvlh")
    path_file: str = Field(default=None, example="data/POD/TimeTracker/Output/ES_20250702_093042.xlsx")

@app.post("/POD_TimeTracker_Getfile", tags=["POD"])
async def POD_TimeTracker_Getfile_postapi(input: POD_TimeTracker_Getfile):
    try:
        conn = get_postgres_connection(POSTGRESQL_SERVER, POSTGRES_PORT_EXTERNAL, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD)
        session = check_session(conn, input.user_id)
        if not session:
            return {
                "status": "error", 
                "message": "Phiên làm việc đã hết hạn hoặc không hợp lệ. Vui lòng đăng nhập lại."
                }
        else:
            return POD_TimeTracker_Getfile_function(minio_client, input, MINIO_BUCKET)
    except Exception as e:
        return {
            "status": "error", 
            "message": str(e)
            }
    
class POD_TimeTracker_Download(BaseModel):
    request_id: str = Field(default="evisor-1234567890", example="evisor-1234567890")
    user_id: str = Field(default="hoanvlh", example="hoanvlh")
    path_file: str = Field(default=None, example="data/POD/TimeTracker/Output/ES_20250702_093042.xlsx")

@app.post("/POD_TimeTracker_Download", tags=["POD"])
def POD_TimeTracker_Download_postapi(input: POD_TimeTracker_Download):
    try:
        conn = get_postgres_connection(POSTGRESQL_SERVER, POSTGRES_PORT_EXTERNAL, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD)
        session = check_session(conn, input.user_id)

        if not session:
            return {
                "status": "error", 
                "message": "Phiên làm việc đã hết hạn hoặc không hợp lệ. Vui lòng đăng nhập lại."
                }
        else:
            return POD_TimeTracker_Download_function(minio_client, input, MINIO_BUCKET)
    except Exception as e:
        return {
            "status": "error", 
            "message": str(e)
            }

@app.post("/WorkManagement_Processing", tags=["General"])
async def WorkManagement_Processing_api(file: UploadFile = File(...), user_id: str = Form(...)):
    try:
        conn = get_postgres_connection(POSTGRESQL_SERVER, POSTGRES_PORT_EXTERNAL, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD)
        session = check_session(conn, user_id)
        if not session:
            return {
                "status": "error", 
                "message": "Phiên làm việc đã hết hạn hoặc không hợp lệ. Vui lòng đăng nhập lại."
                }
        else:
            object_name = f"data/General/WorkManagement/Input/{file.filename}"
            print("object_name:", object_name)
            content = await file.read()
            print("minio_client:", minio_client)
            minio_client.put_object(
                MINIO_BUCKET,
                object_name,
                BytesIO(content),
                length=len(content),
                content_type=file.content_type
            )
            issummary = issummary_file(content)
            if issummary:
                print("ismmary:", issummary)
                conn = get_postgres_connection(POSTGRESQL_SERVER, POSTGRES_PORT_EXTERNAL, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD)
                workmanagement = WorkManagement_Processing_function(content, conn, user_id)
                return {
                    "status": "success",
                    "message": "Đã tạo quản lý kế hoạch!"
                }
            else:
                return {
                    "status": "error",
                    "message": "Sai định dạng cấu trúc tài liệu quản lý kế hoạch!"
                }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

class FilterModel(BaseModel):
    full_name: Optional[List[str]] = []
    project_code: Optional[List[str]] = []
    start_date: Optional[datetime] = "2025-01-01T09:48:50.222Z"
    end_date: Optional[datetime] = "2025-03-17T09:48:50.222Z"

class WorkManagement_View(BaseModel):
    request_id: str = Field(default="evisor-1234567890", example="evisor-1234567890")
    owner: str = Field(default="hoanvlh", example="hoanvlh")
    filter: FilterModel
    pagination: int = Field(default=1, example=1)
    page_size: int = Field(default=20, example=20)

@app.post("/WorkManagement_View", tags=["General"])
async def WorkManagement_View_api(input: WorkManagement_View):
    try:
        conn = get_postgres_connection(POSTGRESQL_SERVER, POSTGRES_PORT_EXTERNAL, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD)
        session = check_session(conn, input.owner)
        if not session:
            return {
                "status": "error", 
                "message": "Phiên làm việc đã hết hạn hoặc không hợp lệ. Vui lòng đăng nhập lại."
                }
        else:
            return WorkManagement_View_function(input, conn)
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
### Authentication
class Authentication(BaseModel):
    username: str = Field(example="hoanvlh")
    password: str = Field(example="Ef27Xw34")

@app.post("/Login", tags=["Authentication"])
def Authentication_api(input: Authentication):
    try:
        conn = get_postgres_connection(POSTGRESQL_SERVER, POSTGRES_PORT_EXTERNAL, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD)
        print(f"Connected to PostgreSQL database: {conn}")
        return Authentication_function(conn, input)
    except Exception as e:
        return {
            "status": "error", 
            "message": str(e)
            }

class Authentication_Logout(BaseModel):
    username: str = Field(example="hoanvlh")

@app.post("/Logout", tags=["Authentication"])
def Authentication_Logout_api(input: Authentication_Logout):
    try:
        conn = get_postgres_connection(POSTGRESQL_SERVER, POSTGRES_PORT_EXTERNAL, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD)
        print(f"Connected to PostgreSQL database: {conn}")
        return Authentication_Logout_function(conn, input)
    except Exception as e:
        return {
            "status": "error", 
            "message": str(e)
            }

class Authentication_ChangePassword(BaseModel):
    username: str = Field(example="hoanvlh")
    password: str = Field(example="Ef27Xw34")
    newpassword: str = Field(example="123456")

@app.post("/ChangePassword", tags=["Authentication"])
def Authentication_ChangePassword_api(input: Authentication_ChangePassword):
    try:
        conn = get_postgres_connection(POSTGRESQL_SERVER, POSTGRES_PORT_EXTERNAL, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD)
        print(f"Connected to PostgreSQL database: {conn}")
        return Authentication_ChangePassword_function(conn, input)
    except Exception as e:
        return {
            "status": "error", 
            "message": str(e)
            }
