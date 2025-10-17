from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel, Field
from minio import Minio
import pandas as pd
from io import BytesIO
from dotenv import load_dotenv
import os
from psycopg2.extras import RealDictCursor
from typing import List, Optional, Union
from datetime import datetime
from src.POD_TimeTracker import *
from src.Authentication import *
from src.DB_Connection import *
from src.WorkManagement import *
from src.WarehouseManagement import *
import uuid
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from fastapi import Form
from pydantic import validator

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

JVM_PATH = os.getenv("JVM_PATH")

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
    summary_file: Optional[str] = Field(default=None, example="data/POD/TimeTracker/Output/ES_20250904_110039.xlsx")
    duplicate: Optional[List[str]] = Field(default=["ES192-5-A2302"], example=["ES192-5-A2302"])

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
                return POD_TimeTracker_Merge_function(minio_client, input, JVM_PATH)
            else:
                return POD_TimeTracker_Merge_Manual_function(minio_client, input, JVM_PATH)
    except Exception as e:
        return {
            "status": "error", 
            "message": str(e)
            }

@app.post("/POD_TimeTracker_Upload", tags=["POD"])
async def POD_TimeTracker_Upload_api(files: List[UploadFile] = File(...)):
    try:
        uploaded_paths = []
        list_codes = []
        summary_file = ""

        for file in files:
            object_name = f"data/POD/TimeTracker/Input/{file.filename}"
            content = await file.read()

            # Upload MinIO
            minio_client.put_object(
                MINIO_BUCKET,
                object_name,
                BytesIO(content),
                length=len(content),
                content_type=file.content_type
            )

            issummary, codes = issummary_file(content, object_name, JVM_PATH)
            print("issummary:", issummary)

            # Collect codes
            list_codes.extend(codes)

            if issummary:
                summary_file = object_name
            else:
                uploaded_paths.append(object_name)

        duplicate = duplicate_project_code(list_codes)

        return {
            "status": "success",
            "path_files": uploaded_paths,
            "summary_file": summary_file,
            "duplicate": duplicate
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
            issummary = issummary_file(content, object_name, JVM_PATH)
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
    version: Optional[int] = 1

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

class Form(BaseModel):
    id: Optional[List[int]] = None
    owner: Optional[str] = ""
    full_name: Optional[str] = ""
    project_code: Optional[str] = ""
    description: Optional[str] = ""
    start_date: Optional[datetime] = Field(default=None, example="2025-01-01T09:48:50.222Z")
    end_date: Optional[datetime] = Field(default=None, example="2025-03-17T09:48:50.222Z")
    QTY: Optional[float] = None
    site: Optional[str] = ""
    status: Optional[int] = None

class WorkManagement_DML(BaseModel):
    request_id: str = Field(default="evisor-1234567890", example="evisor-1234567890")
    owner: str = Field(default="hoanvlh", example="hoanvlh")
    dml_action: str = Field(default="delete", example="delete") # "insert", "update", "delete"
    form: Form

@app.post("/WorkManagement_DML", tags=["General"])
async def WorkManagement_DML_api(input: WorkManagement_DML):
    print("input:", input)
    try:
        conn = get_postgres_connection(POSTGRESQL_SERVER, POSTGRES_PORT_EXTERNAL, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD)
        session = check_session(conn, input.owner)
        if not session:
            return {
                "status": "error", 
                "message": "Phiên làm việc đã hết hạn hoặc không hợp lệ. Vui lòng đăng nhập lại."
                }
        else:
            if input.dml_action == "delete":
                return WorkManagement_DML_Delete_function(input, conn)
            elif input.dml_action == "insert":
                return WorkManagement_DML_Insert_function(input, conn)
            elif input.dml_action == "update":
                return WorkManagement_DML_Update_function(input, conn)
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

### Warehouse - Statistical ###
class WarehouseStatistical_View(BaseModel):
    request_id: str = Field(default="evisor-1234567890", example="evisor-1234567890")
    owner: str = Field(default="hoanvlh", example="hoanvlh")

@app.post("/WS/WarehouseStatistical_View", tags=["Warehouse"])
async def WarehouseStatistical_View_api(input: WarehouseStatistical_View):
    try:
        conn = get_postgres_connection(POSTGRESQL_SERVER, POSTGRES_PORT_EXTERNAL, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD)
        session = check_session(conn, input.owner)
        if not session:
            return {
                "status": "error", 
                "message": "Phiên làm việc đã hết hạn hoặc không hợp lệ. Vui lòng đăng nhập lại."
                }
        else:
            return WarehouseStatistical_View_function(input, conn)
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

class WarehouseStatistical_View_Detail(BaseModel):
    request_id: str = Field(default="evisor-1234567890", example="evisor-1234567890")
    owner: str = Field(default="hoanvlh", example="hoanvlh")
    id: int = Field(default=1, example=1)

@app.post("/WS/WarehouseStatistical_View_Detail", tags=["Warehouse"])
async def WarehouseStatistical_View_Detail_api(input: WarehouseStatistical_View_Detail):
    try:
        conn = get_postgres_connection(POSTGRESQL_SERVER, POSTGRES_PORT_EXTERNAL, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD)
        session = check_session(conn, input.owner)
        if not session:
            return {
                "status": "error", 
                "message": "Phiên làm việc đã hết hạn hoặc không hợp lệ. Vui lòng đăng nhập lại."
                }
        else:
            return WarehouseStatistical_View_Detail_function(input, conn)
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

class FormWarehouseStatistical(BaseModel):
    id: int = Field(default=1, example=1)
    product_name: str = Field(default="Product Name", example="Product Name")
    description: str = Field(default="Description", example="Description")
    time: Optional[datetime] = Field(default=None, example="2025-03-17T09:48:50.222Z")
    part_no: str = Field(default="ES192-5-A2302", example="ES192-5-A2302") 
    origin: str = Field(default="Origin", example="Origin")  
    unit: str = Field(default="Cái", example="Cái")  
    quantity: int = Field(default=1, example=1) 
    seri_number: str = Field(default="seri_number", example="seri_number")
    location: str = Field(default="location", example="location")
    entered_by: str = Field(default="entered_by", example="entered_by")
    status: int = Field(default=1, example=1) # 1: Available, 0: Not available 

class WarehouseStatistical_DML(BaseModel):
    request_id: str = Field(default="evisor-1234567890", example="evisor-1234567890")
    owner: str = Field(default="hoanvlh", example="hoanvlh")
    dml_action: str = Field(default="delete", example="delete") # "insert", "update", "delete"
    form: FormWarehouseStatistical

@app.post("/WS/WarehouseStatistical_DML", tags=["Warehouse"])
async def WarehouseStatistical_DML_api(input: WarehouseStatistical_DML):
    try:
        conn = get_postgres_connection(POSTGRESQL_SERVER, POSTGRES_PORT_EXTERNAL, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD)
        session = check_session(conn, input.owner)
        if not session:
            return {
                "status": "error", 
                "message": "Phiên làm việc đã hết hạn hoặc không hợp lệ. Vui lòng đăng nhập lại."
                }
        else:
            if input.dml_action == "insert":
                return WarehouseStatistical_DML_Insert_function(input, conn)
            elif input.dml_action == "update":
                return WarehouseStatistical_DML_Update_function(input, conn)
            elif input.dml_action == "delete":
                return WarehouseStatistical_DML_Delete_function(input, conn)
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
    
from fastapi import Form
@app.post("/WS/WarehouseStatistical_Upload", tags=["Warehouse"])
async def WarehouseStatistical_Upload_api(
    request_id: str = Form("evisor-1234567890", example="evisor-1234567890"),
    owner: str = Form("hoanvlh", example="hoanvlh"),
    file: UploadFile = File(...)):
    try:
        conn = get_postgres_connection(POSTGRESQL_SERVER, POSTGRES_PORT_EXTERNAL, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD)
        session = check_session(conn, owner)

        if not session:
            return {
                "status": "error",
                "message": "Phiên làm việc đã hết hạn hoặc không hợp lệ. Vui lòng đăng nhập lại."
            }
        return WarehouseStatistical_Upload_function(conn, file)
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

### Warehouse - Import, Export ###

class WarehouseImportExport_View(BaseModel):
    request_id: str = Field(default="evisor-1234567890", example="evisor-1234567890")
    owner: str = Field(default="hoanvlh", example="hoanvlh")
    option: str = Field(default="import", example="import")  # "import" hoặc "export"

@app.post("/WS/WarehouseImportExport_View", tags=["Warehouse"])
async def WarehouseImportExport_View_api(input: WarehouseImportExport_View):
    try:
        conn = get_postgres_connection(POSTGRESQL_SERVER, POSTGRES_PORT_EXTERNAL, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD)
        session = check_session(conn, input.owner)
        if not session:
            return {
                "status": "error",
                "message": "Phiên làm việc đã hết hạn hoặc không hợp lệ. Vui lòng đăng nhập lại."
            }
        option_map = {
            "import": "WS_Import",
            "export": "WS_Export"
        }
        table_name = option_map.get(input.option.lower())

        if not table_name:
            return {
                "status": "error",
                "message": f"Tùy chọn '{input.option}' không hợp lệ. Chỉ chấp nhận 'import' hoặc 'export'."
            }
        return WarehouseImportExport_View_function(conn, table_name)
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

class WarehouseImportExport_View_Detail(BaseModel):
    request_id: str = Field(default="evisor-1234567890", example="evisor-1234567890")
    owner: str = Field(default="hoanvlh", example="hoanvlh")
    id: int = Field(default=1, example=1)
    option: str = Field(default="import", example="import")  # "import" hoặc "export"

@app.post("/WS/WarehouseImportExport_View_Detail", tags=["Warehouse"])
async def WarehouseImportExport_View_Detail_api(input: WarehouseImportExport_View_Detail):
    try:
        conn = get_postgres_connection(POSTGRESQL_SERVER, POSTGRES_PORT_EXTERNAL, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD)
        session = check_session(conn, input.owner)
        if not session:
            return {
                "status": "error",
                "message": "Phiên làm việc đã hết hạn hoặc không hợp lệ. Vui lòng đăng nhập lại."
            }
        option_map = {
            "import": "WS_Import",
            "export": "WS_Export"
        }
        table_name = option_map.get(input.option.lower())
        if not table_name:
            return {
                "status": "error",
                "message": f"Tùy chọn '{input.option}' không hợp lệ. Chỉ chấp nhận 'import' hoặc 'export'."
            }
        return WarehouseImportExport_View_Detail_function(input, conn, table_name)
    except Exception as e:
        return {
            "status": "error", 
            "message": str(e)
    }
    
# class FormWarehouseImport(BaseModel):
#     id: int = Field(default=1, example=1)
#     import_id: int = Field(default=1, example=1)
#     time: Optional[datetime] = Field(default=None, example="2025-03-17T09:48:50.222Z")
#     import_time: Optional[datetime] = Field(default=None, example="2025-03-17T09:48:50.222Z")
#     project_code: str = Field(default="project_code", example="project_code")
#     product_name: str = Field(default="Product Name", example="Product Name")
#     part_no: str = Field(default="ES192-5-A2302", example="ES192-5-A2302") 
#     origin: str = Field(default="Origin", example="Origin")
#     quantity: int = Field(default=1, example=1) 
#     seri_number: str = Field(default="seri_number", example="seri_number")

class FormWarehouseImportExport(BaseModel):
    id: int = Field(default=1, example=1)
    ticket_id: str = Field(default=1, example=1)
    time: Optional[datetime] = None
    ticket_time: Optional[datetime] = None
    project_code: str = Field(default="project_code", example="project_code")
    product_name: str = Field(default="Product Name", example="Product Name")
    part_no: str = Field(default="ES192-5-A2302", example="ES192-5-A2302") 
    origin: str = Field(default="Origin", example="Origin")
    quantity: int = Field(default=1, example=1) 
    seri_number: str = Field(default="seri_number", example="seri_number")

    @validator('time', pre=True)
    def parse_empty_string_as_none(cls, value):
        if value == "":
            return None
        return value

class WarehouseImportExport_DML(BaseModel):
    request_id: str = Field(default="evisor-1234567890", example="evisor-1234567890")
    owner: str = Field(default="hoanvlh", example="hoanvlh")
    option: str = Field(default="import", example="import") # "import", "export"
    dml_action: str = Field(default="delete", example="delete") # "insert", "update", "delete"
    # form: Union[FormWarehouseImport, FormWarehouseExport]
    form: FormWarehouseImportExport

@app.post("/WS/WarehouseImportExport_DML", tags=["Warehouse"])
async def WarehouseImportExport_DML_api(input: WarehouseImportExport_DML):
    try:
        conn = get_postgres_connection(POSTGRESQL_SERVER, POSTGRES_PORT_EXTERNAL, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD)
        session = check_session(conn, input.owner)
        if not session:
            return {
                "status": "error", 
                "message": "Phiên làm việc đã hết hạn hoặc không hợp lệ. Vui lòng đăng nhập lại."
                }
        if input.dml_action == "insert":
            return WarehouseImportExport_DML_Insert_function(input, conn, input.option)
        elif input.dml_action == "update":
            return WarehouseImportExport_DML_Update_function(input, conn, input.option)
        elif input.dml_action == "delete":
            return WarehouseImportExport_DML_Delete_function(input, conn, input.option)
        else:
            return {"status": "error", "message": "DML action không hợp lệ. Chỉ hỗ trợ 'insert', 'update', 'delete'."}

    except Exception as e:
        return {
            "status": "error", 
            "message": str(e)
    }
    
from fastapi import Form
@app.post("/WS/WarehouseImportExport_Upload", tags=["Warehouse"])
async def WarehouseImportExport_Upload_api(
    request_id: str = Form("evisor-1234567890"),
    owner: str = Form("hoanvlh"),
    option: str = Form("import"),  # "import" hoặc "export"
    file: UploadFile = File(...)
):
    try:
        conn = get_postgres_connection(POSTGRESQL_SERVER, POSTGRES_PORT_EXTERNAL, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD)
        session = check_session(conn, owner)
        if not session:
            return {
                "status": "error",
                "message": "Phiên làm việc đã hết hạn hoặc không hợp lệ. Vui lòng đăng nhập lại."
            }
        return WarehouseImportExport_Upload_function(conn, file, option)
    except Exception as e:
        return {
            "status": "error", 
            "message": str(e)
    }

class WarehouseImportExport_Download(BaseModel):
    request_id: str = Field(default="evisor-1234567890", example="evisor-1234567890")
    owner: str = Field(default="hoanvlh", example="hoanvlh")
    option: str = Field(default="import", example="import") # "import", "export"
    ticket_id: Optional[str] = Field(default=1, example=1)
    project_code: Optional[str] = Field(default="example", example="example")

@app.post("/WS/WarehouseImportExport_Download", tags=["Warehouse"])
async def WarehouseImportExport_Download_api(input: WarehouseImportExport_Download):
    try:
        conn = get_postgres_connection(POSTGRESQL_SERVER, POSTGRES_PORT_EXTERNAL, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD)
        session = check_session(conn, input.owner)
        if not session:
            return {
                "status": "error",
                "message": "Phiên làm việc đã hết hạn hoặc không hợp lệ. Vui lòng đăng nhập lại."
            }
        return WarehouseImportExport_Download_function(conn, input, minio_client,  MINIO_BUCKET)
    except Exception as e:
        return {
            "status": "error", 
            "message": str(e)
    }
# ### Warehouse - Export ###

# class WarehouseExport_View(BaseModel):
#     request_id: str = Field(default="evisor-1234567890", example="evisor-1234567890")
#     owner: str = Field(default="hoanvlh", example="hoanvlh")

# @app.post("/WS/WarehouseExport_View", tags=["Warehouse"])
# async def WarehouseExport_View_api(input: WarehouseExport_View):
#     try:
#         conn = get_postgres_connection(POSTGRESQL_SERVER, POSTGRES_PORT_EXTERNAL, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD)
#         session = check_session(conn, input.owner)
#         if not session:
#             return {
#                 "status": "error", 
#                 "message": "Phiên làm việc đã hết hạn hoặc không hợp lệ. Vui lòng đăng nhập lại."
#                 }
#         else:
#             return WarehouseExport_View_function(input, conn)
#     except Exception as e:
#         return {
#             "status": "error",
#             "message": str(e)
#         }

# class WarehouseExport_View_Detail(BaseModel):
#     request_id: str = Field(default="evisor-1234567890", example="evisor-1234567890")
#     owner: str = Field(default="hoanvlh", example="hoanvlh")
#     id: int = Field(default=1, example=1)

# @app.post("/WS/WarehouseExport_View_Detail", tags=["Warehouse"])
# async def WarehouseExport_View_Detail_api(input: WarehouseExport_View_Detail):
#     try:
#         conn = get_postgres_connection(POSTGRESQL_SERVER, POSTGRES_PORT_EXTERNAL, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD)
#         session = check_session(conn, input.owner)
#         if not session:
#             return {
#                 "status": "error", 
#                 "message": "Phiên làm việc đã hết hạn hoặc không hợp lệ. Vui lòng đăng nhập lại."
#                 }
#         else:
#             return WarehouseExport_View_Detail_function(input, conn)
#     except Exception as e:
#         return {
#             "status": "error",
#             "message": str(e)
#         }
    
# class FormWarehouseExport(BaseModel):
#     id: int = Field(default=1, example=1)
#     Export_id: int = Field(default=1, example=1)
#     time: Optional[datetime] = Field(default=None, example="2025-03-17T09:48:50.222Z")
#     Export_time: Optional[datetime] = Field(default=None, example="2025-03-17T09:48:50.222Z")
#     project_code: str = Field(default="project_code", example="project_code")
#     product_name: str = Field(default="Product Name", example="Product Name")
#     part_no: str = Field(default="ES192-5-A2302", example="ES192-5-A2302") 
#     origin: str = Field(default="Origin", example="Origin")
#     quantity: int = Field(default=1, example=1) 
#     seri_number: str = Field(default="seri_number", example="seri_number")

# class WarehouseExport_DML(BaseModel):
#     request_id: str = Field(default="evisor-1234567890", example="evisor-1234567890")
#     owner: str = Field(default="hoanvlh", example="hoanvlh")
#     dml_action: str = Field(default="delete", example="delete") # "insert", "update", "delete"
#     form: FormWarehouseExport

# @app.post("/WS/WarehouseExport_DML", tags=["Warehouse"])
# async def WarehouseExport_DML_api(input: WarehouseExport_DML):
#     try:
#         conn = get_postgres_connection(POSTGRESQL_SERVER, POSTGRES_PORT_EXTERNAL, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD)
#         session = check_session(conn, input.owner)
#         if not session:
#             return {
#                 "status": "error", 
#                 "message": "Phiên làm việc đã hết hạn hoặc không hợp lệ. Vui lòng đăng nhập lại."
#                 }
#         else:
#             if input.dml_action == "insert":
#                 return WarehouseExport_DML_Insert_function(input, conn)
#             elif input.dml_action == "update":
#                 return WarehouseExport_DML_Update_function(input, conn)
#             elif input.dml_action == "delete":
#                 return WarehouseExport_DML_Delete_function(input, conn)
#     except Exception as e:
#         return {
#             "status": "error",
#             "message": str(e)
#         }

# from fastapi import Form
# @app.post("/WS/WarehouseExport_Upload", tags=["Warehouse"])
# async def WarehouseExport_Upload_api(
#     request_id: str = Form("evisor-1234567890", example="evisor-1234567890"),
#     owner: str = Form("hoanvlh", example="hoanvlh"),
#     file: UploadFile = File(...)):
#     try:
#         conn = get_postgres_connection(POSTGRESQL_SERVER, POSTGRES_PORT_EXTERNAL, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD)
#         session = check_session(conn, owner)

#         if not session:
#             return {
#                 "status": "error",
#                 "message": "Phiên làm việc đã hết hạn hoặc không hợp lệ. Vui lòng đăng nhập lại."
#             }

#         return WarehouseExport_Upload_function(conn, file)

#     except Exception as e:
#         return {
#             "status": "error",
#             "message": str(e)
#         }
# --------------------------------------------------------
# Authentication
# --------------------------------------------------------
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


# --------------------------------------------------------
# WebSocket
# --------------------------------------------------------

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                # payload example: {"request_id": "...", "owner": "...", "option": "..."}
                print("Received payload:", payload)
                
                # TODO: xử lý logic import/export hoặc gọi DB
                response_msg = f"Payload processed: {payload['request_id']}"
                await websocket.send_text(response_msg)
            except json.JSONDecodeError:
                await websocket.send_text("Invalid JSON")
    except WebSocketDisconnect:
        print("Client disconnected")