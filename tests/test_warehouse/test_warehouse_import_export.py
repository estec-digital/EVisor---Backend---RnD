import pytest
import json
import os
import io
import sys
import tempfile
import pandas as pd
from fastapi import UploadFile
from unittest.mock import patch, Mock, MagicMock, mock_open
from fastapi.testclient import TestClient
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.main import app

def load_test_data(filename):
    """Load test data từ file JSON"""
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    filepath = os.path.join(data_dir, filename)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_nested_data(data_dict, key_path):
    """Lấy nested data từ dictionary sử dụng key path với hỗ trợ array index"""
    try:
        keys = []
        current_key = ""
        
        for char in key_path:
            if char == '[':
                if current_key:
                    keys.append(current_key)
                    current_key = ""
            elif char == ']':
                if current_key:
                    keys.append(current_key)
                    current_key = ""
            elif char == '.':
                if current_key:
                    keys.append(current_key)
                    current_key = ""
            else:
                current_key += char
        
        if current_key:
            keys.append(current_key)
        
        current_data = data_dict
        
        for key in keys:
            if not key:  
                continue
                
            if key.isdigit():
                current_data = current_data[int(key)]
            else:
                current_data = current_data[key]
        
        return current_data
        
    except (KeyError, IndexError, TypeError) as e:
        print(f"ERROR: Cannot get data for key_path '{key_path}'")
        print(f"Available keys: {list(data_dict.keys())}")
        print(f"Parsed keys: {keys}")
        raise

@pytest.fixture
def client():
    """Test client"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def test_payloads():
    """Load test payloads từ JSON"""
    return load_test_data('warehouse_payloads.json')


@pytest.fixture
def sample_data():
    """Load sample data từ JSON"""
    return load_test_data('sample_data.json')


@pytest.fixture
def test_cases():
    """Load test cases từ JSON"""
    return load_test_data('test_cases.json')


@pytest.fixture
def mock_db_connection():
    """Mock database connection cho test download"""
    class MockCursor:
        def __init__(self):
            self.description = [
                ("id",),
                ("time",),
                ("project_code",),
                ("product_name",),
                ("part_no",),
                ("origin",),
                ("quantity",),
                ("seri_number",)
            ]
            self.data = [
                (1, "2025-01-15", "PROJ-A", "Thiết bị A", "PN001", "Vietnam", 5, "SN001")
            ]
            self.executed = []
            self.closed = False

        def execute(self, query, params=None):
            self.executed.append((query, params))

        def fetchall(self):
            return self.data

        def close(self): self.closed = True
        def __enter__(self): return self
        def __exit__(self, *args): self.close()

    class MockConnection:
        def __init__(self):
            self.cursor_instance = MockCursor()
            self.closed = False
        def cursor(self): return self.cursor_instance
        def rollback(self): pass
        def close(self): self.closed = True

    return MockConnection

#################################### TEST WAREHOUSE IMPORT EXPORT VIEW API ####################################
class TestWarehouseImportExportViewAPI:
    """Test cases cho /WS/WarehouseImportExport_View API endpoint"""

    def _create_mock_conn(self, data=None):
        """Tạo mock connection đơn giản"""
        class MockCursor:
            def __init__(self, data):
                self.data = data or []
                self.executed_query = None
                self.closed = False

            def execute(self, query, params=None):
                self.executed_query = query

            def fetchall(self):
                return self.data

            def close(self):
                self.closed = True

            def __enter__(self): return self
            def __exit__(self, *args): self.close()

        class MockConnection:
            def __init__(self, data):
                self.cursor_instance = MockCursor(data)

            def cursor(self):
                return self.cursor_instance

            def close(self): pass

        return MockConnection(data)

    def test_import_view_success(self, client):
        """Test option='import' trả dữ liệu thành công"""
        payload = {
            "request_id": "evisor-1234567890",
            "owner": "hoanvlh",
            "option": "import"
        }

        mock_data = [
            (1, "IMP001", "2025-01-15T08:00:00", "2025-01-15T08:30:00", "PROJ-A", "Thiết bị A", "PN001", "Vietnam", 10, "SN001"),
            (2, "IMP002", "2025-01-16T09:00:00", "2025-01-16T09:30:00", "PROJ-B", "Thiết bị B", "PN002", "China", 20, "SN002")
        ]

        with patch("src.main.get_postgres_connection") as mock_conn, \
             patch("src.main.check_session", return_value=True):

            mock_conn.return_value = self._create_mock_conn(mock_data)

            response = client.post("/WS/WarehouseImportExport_View", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert isinstance(data["data"], list)
            assert len(data["data"]) == len(mock_data)
            assert "import_id" in data["data"][0]

    def test_export_view_success(self, client):
        """Test option='export' trả dữ liệu thành công"""
        payload = {
            "request_id": "evisor-9876543210",
            "owner": "hoanvlh",
            "option": "export"
        }

        mock_data = [
            (1, "EXP001", "2025-02-01T10:00:00", "2025-02-01T10:30:00", "PROJ-A", "Thiết bị C", "PN003", "Japan", 5, "SN003")
        ]

        with patch("src.main.get_postgres_connection") as mock_conn, \
             patch("src.main.check_session", return_value=True):

            mock_conn.return_value = self._create_mock_conn(mock_data)

            response = client.post("/WS/WarehouseImportExport_View", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "export_id" in data["data"][0]

    def test_invalid_option(self, client):
        """Test khi option không hợp lệ"""
        payload = {
            "request_id": "evisor-1234567890",
            "owner": "hoanvlh",
            "option": "invalid_option"
        }

        with patch("src.main.get_postgres_connection") as mock_conn, \
             patch("src.main.check_session", return_value=True):

            mock_conn.return_value = self._create_mock_conn()

            response = client.post("/WS/WarehouseImportExport_View", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"
            assert "không hợp lệ" in data["message"]

    def test_invalid_session(self, client):
        """Test khi phiên làm việc hết hạn"""
        payload = {
            "request_id": "evisor-1234567890",
            "owner": "hoanvlh",
            "option": "import"
        }

        with patch("src.main.get_postgres_connection") as mock_conn, \
             patch("src.main.check_session", return_value=False):

            mock_conn.return_value = self._create_mock_conn()

            response = client.post("/WS/WarehouseImportExport_View", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"
            assert "Phiên làm việc" in data["message"]

    def test_database_error(self, client):
        """Test khi kết nối database lỗi"""
        payload = {
            "request_id": "evisor-1234567890",
            "owner": "hoanvlh",
            "option": "import"
        }

        with patch("src.main.get_postgres_connection") as mock_conn, \
             patch("src.main.check_session", return_value=True):

            mock_conn.side_effect = Exception("Database connection failed")

            response = client.post("/WS/WarehouseImportExport_View", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"
            assert "Database connection failed" in data["message"]


#################################### TEST WAREHOUSE IMPORT EXPORT VIEW DETAIL API ####################################
class TestWarehouseImportExportViewDetailAPI:
    """Test cases cho /WS/WarehouseImportExport_View_Detail API"""

    def _create_mock_conn(self, row=None):
        """Tạo mock connection để mô phỏng cursor"""
        class MockCursor:
            def __init__(self, row):
                self.row = row
                self.executed_query = None
                self.params = None
                self.closed = False

            def execute(self, query, params=None):
                self.executed_query = query
                self.params = params

            def fetchone(self):
                return self.row

            def close(self):
                self.closed = True

            def __enter__(self): return self
            def __exit__(self, *args): self.close()

        class MockConnection:
            def __init__(self, row):
                self.cursor_instance = MockCursor(row)
            def cursor(self): return self.cursor_instance
            def close(self): pass

        return MockConnection(row)

    def test_import_detail_success(self, client):
        """Test lấy chi tiết import thành công"""
        payload = {
            "request_id": "evisor-1234567890",
            "owner": "hoanvlh",
            "id": 1,
            "option": "import"
        }

        mock_row = (1, "IMP001", "2025-01-15T08:00:00", "2025-01-15T08:30:00", "PROJ-A", "Thiết bị A", "PN001", "Vietnam", 10, "SN001")

        with patch("src.main.get_postgres_connection") as mock_conn, \
             patch("src.main.check_session", return_value=True):

            mock_conn.return_value = self._create_mock_conn(mock_row)

            response = client.post("/WS/WarehouseImportExport_View_Detail", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "import_id" in data["data"]
            assert data["data"]["project_code"] == "PROJ-A"

    def test_export_detail_success(self, client):
        """Test lấy chi tiết export thành công"""
        payload = {
            "request_id": "evisor-9876543210",
            "owner": "hoanvlh",
            "id": 2,
            "option": "export"
        }

        mock_row = (2, "EXP002", "2025-01-20T09:00:00", "2025-01-20T09:30:00", "PROJ-B", "Thiết bị B", "PN002", "China", 5, "SN002")

        with patch("src.main.get_postgres_connection") as mock_conn, \
             patch("src.main.check_session", return_value=True):

            mock_conn.return_value = self._create_mock_conn(mock_row)

            response = client.post("/WS/WarehouseImportExport_View_Detail", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "export_id" in data["data"]
            assert data["data"]["origin"] == "China"

    def test_invalid_option(self, client):
        """Test option không hợp lệ"""
        payload = {
            "request_id": "evisor-1234567890",
            "owner": "hoanvlh",
            "id": 1,
            "option": "invalid_option"
        }

        with patch("src.main.get_postgres_connection") as mock_conn, \
             patch("src.main.check_session", return_value=True):
            mock_conn.return_value = self._create_mock_conn()

            response = client.post("/WS/WarehouseImportExport_View_Detail", json=payload)
            data = response.json()

            assert data["status"] == "error"
            assert "không hợp lệ" in data["message"]

    def test_invalid_session(self, client):
        """Test phiên làm việc hết hạn"""
        payload = {
            "request_id": "evisor-1234567890",
            "owner": "hoanvlh",
            "id": 1,
            "option": "import"
        }

        with patch("src.main.get_postgres_connection") as mock_conn, \
             patch("src.main.check_session", return_value=False):
            mock_conn.return_value = self._create_mock_conn()

            response = client.post("/WS/WarehouseImportExport_View_Detail", json=payload)
            data = response.json()

            assert data["status"] == "error"
            assert "Phiên làm việc" in data["message"]

    def test_item_not_found(self, client):
        """Test khi không tìm thấy item"""
        payload = {
            "request_id": "evisor-1234567890",
            "owner": "hoanvlh",
            "id": 999,
            "option": "import"
        }

        with patch("src.main.get_postgres_connection") as mock_conn, \
             patch("src.main.check_session", return_value=True):
            mock_conn.return_value = self._create_mock_conn(None)

            response = client.post("/WS/WarehouseImportExport_View_Detail", json=payload)
            data = response.json()

            assert data["status"] == "error"
            assert "not found" in data["message"]

    def test_database_error(self, client):
        """Test lỗi database"""
        payload = {
            "request_id": "evisor-1234567890",
            "owner": "hoanvlh",
            "id": 1,
            "option": "import"
        }

        with patch("src.main.get_postgres_connection") as mock_conn, \
             patch("src.main.check_session", return_value=True):
            mock_conn.side_effect = Exception("Database connection failed")

            response = client.post("/WS/WarehouseImportExport_View_Detail", json=payload)
            data = response.json()

            assert data["status"] == "error"
            assert "Database connection failed" in data["message"]


#################################### TEST WAREHOUSE IMPORT EXPORT UPLOAD API ####################################
class TestWarehouseImportExportUploadAPI:
    """Test cases cho /WS/WarehouseImportExport_Upload API"""

    def _create_mock_conn(self):
        """Tạo mock database connection"""
        class MockCursor:
            def __init__(self):
                self.executed = []
                self.closed = False
            def execute(self, query, params=None):
                self.executed.append((query, params))
            def close(self): self.closed = True
            def __enter__(self): return self
            def __exit__(self, *args): self.close()

        class MockConnection:
            def __init__(self):
                self.cursor_instance = MockCursor()
            def cursor(self): return self.cursor_instance
            def commit(self): pass
            def rollback(self): pass
            def close(self): pass

        return MockConnection()

    def _make_excel_buffer(self, option="import"):
        """Tạo file Excel giả lập"""
        df = pd.DataFrame({
            "Thời gian": ["2025-01-15", "2025-01-16"],
            "Mã Dự án": ["PROJ-A", "PROJ-B"],
            "Tên hàng": ["Thiết bị A", "Thiết bị B"],
            "Mã hàng": ["PN001", "PN002"],
            "Hãng": ["Vietnam", "China"],
            "Số lượng": [5, 10],
            "Seri No.": ["SN001", "SN002"]
        })
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False, header=True, engine="openpyxl")
        buffer.seek(0)
        return buffer

    def test_upload_import_success(self, client):
        """Test upload import file thành công"""
        buffer = self._make_excel_buffer(option="import")

        with patch("src.main.get_postgres_connection") as mock_conn, \
             patch("src.main.check_session", return_value=True):
            mock_conn.return_value = self._create_mock_conn()

            response = client.post(
                "/WS/WarehouseImportExport_Upload",
                data={"request_id": "evisor-1234567890", "owner": "hoanvlh", "option": "import"},
                files={"file": ("import_file.xlsx", buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "import" in data["message"]

    def _make_excel_buffer(self, option="import"):
        """Tạo file Excel giả lập (tương thích với API header=1)"""
        df = pd.DataFrame({
            "STT": [1, 2],
            "Thời gian": ["2025-01-15", "2025-01-16"],
            "Mã Dự án": ["PROJ-A", "PROJ-B"],
            "Tên hàng": ["Thiết bị A", "Thiết bị B"],
            "Mã hàng": ["PN001", "PN002"],
            "Hãng": ["Vietnam", "China"],
            "Số lượng": [5, 10],
            "Seri No.": ["SN001", "SN002"]
        })

        if option == "export":
            df["export_id"] = ["EXP001", "EXP002"]
        elif option == "import":
            df["import_id"] = ["IMP001", "IMP002"]

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            pd.DataFrame([["DUMMY_ROW"] * len(df.columns)]).to_excel(
                writer, index=False, header=False
            )
            df.to_excel(writer, index=False, header=True, startrow=1)
        buffer.seek(0)
        return buffer

    def test_upload_export_success(self, client):
        """Test upload export file thành công"""
        buffer = self._make_excel_buffer(option="export")

        with patch("src.main.get_postgres_connection") as mock_conn, \
             patch("src.main.check_session", return_value=True):
            mock_conn.return_value = self._create_mock_conn()

            response = client.post(
                "/WS/WarehouseImportExport_Upload",
                data={"request_id": "evisor-1234567890", "owner": "hoanvlh", "option": "export"},
                files={"file": ("export_file.xlsx", buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "export" in data["message"]

    def test_invalid_file_format(self, client):
        """Test upload file sai định dạng (.txt)"""
        fake_file = io.BytesIO(b"invalid data")
        with patch("src.main.check_session", return_value=True):
            response = client.post(
                "/WS/WarehouseImportExport_Upload",
                data={"request_id": "evisor-1234567890", "owner": "hoanvlh", "option": "import"},
                files={"file": ("test.txt", fake_file, "text/plain")},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"
            assert "không được hỗ trợ" in data["message"]

    def test_invalid_option(self, client):
        """Test tùy chọn option không hợp lệ"""
        buffer = self._make_excel_buffer()

        with patch("src.main.get_postgres_connection") as mock_conn, \
             patch("src.main.check_session", return_value=True):
            mock_conn.return_value = self._create_mock_conn()

            response = client.post(
                "/WS/WarehouseImportExport_Upload",
                data={"request_id": "evisor-1234567890", "owner": "hoanvlh", "option": "invalid_option"},
                files={"file": ("import_file.xlsx", buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            )
            data = response.json()
            assert data["status"] == "error"
            assert "không hợp lệ" in data["message"]

    def test_invalid_session(self, client):
        """Test khi phiên làm việc hết hạn"""
        fake_file = io.BytesIO(b"fake")
        with patch("src.main.get_postgres_connection") as mock_conn, \
             patch("src.main.check_session", return_value=False):
            mock_conn.return_value = self._create_mock_conn()

            response = client.post(
                "/WS/WarehouseImportExport_Upload",
                data={"request_id": "evisor-1234567890", "owner": "hoanvlh", "option": "import"},
                files={"file": ("import_file.xlsx", fake_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            )
            data = response.json()
            assert data["status"] == "error"
            assert "Phiên làm việc" in data["message"]

    def test_database_error(self, client):
        """Test khi database lỗi"""
        fake_file = io.BytesIO(b"fake")
        with patch("src.main.get_postgres_connection") as mock_conn, \
             patch("src.main.check_session", return_value=True):
            mock_conn.side_effect = Exception("Database connection failed")

            response = client.post(
                "/WS/WarehouseImportExport_Upload",
                data={"request_id": "evisor-1234567890", "owner": "hoanvlh", "option": "import"},
                files={"file": ("import_file.xlsx", fake_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            )
            data = response.json()
            assert data["status"] == "error"
            assert "Database connection failed" in data["message"]


#################################### TEST WAREHOUSE IMPORT EXPORT DOWNLOAD API ####################################
class TestWarehouseImportExportDownloadAPI:

    def test_download_import_success(self, client):
        payload = {
            "request_id": "evisor-1234567890",
            "owner": "hoanvlh",
            "option": "import",
            "ticket_id": "1"
        }

        with patch("src.main.get_postgres_connection") as mock_conn, \
             patch("src.main.check_session", return_value=True), \
             patch("src.main.WarehouseImportExport_Download_function",
                   return_value={"status": "success", "url": "http://example.com/file.xlsx"}):

            mock_conn.return_value = object()
            response = client.post("/WS/WarehouseImportExport_Download", json=payload)

        assert response.status_code == 200
        res = response.json()
        assert res["status"] == "success"
        assert "url" in res

    def test_download_export_success(self, client):
        """Download Export thành công"""
        payload = {
            "request_id": "evisor-1234567890",
            "owner": "hoanvlh",
            "option": "export",
            "ticket_id": "5"
        }

        with patch("src.main.get_postgres_connection") as mock_conn, \
             patch("src.main.check_session", return_value=True), \
             patch("src.main.WarehouseImportExport_Download_function",
                   return_value={"status": "success", "url": "http://example.com/file.xlsx"}):

            mock_conn.return_value = object()
            response = client.post("/WS/WarehouseImportExport_Download", json=payload)

        assert response.status_code == 200
        res = response.json()
        assert res["status"] == "success"
        assert "url" in res

    def test_invalid_session(self, client):
        """Phiên làm việc hết hạn"""
        payload = {
            "request_id": "evisor-1234567890",
            "owner": "hoanvlh",
            "option": "import",
            "ticket_id": "1"
        }

        with patch("src.main.get_postgres_connection") as mock_conn, \
             patch("src.main.check_session", return_value=False):

            mock_conn.return_value = object()
            response = client.post("/WS/WarehouseImportExport_Download", json=payload)

        res = response.json()
        assert res["status"] == "error"
        assert "Phiên làm việc" in res["message"]

    def test_invalid_option(self, client, mock_db_connection):
        """Option không hợp lệ"""
        payload = {
            "request_id": "evisor-1234567890",
            "owner": "hoanvlh",
            "option": "abc",
            "ticket_id": "1"
        }

        with patch("src.main.get_postgres_connection") as mock_conn, \
             patch("src.main.check_session", return_value=True), \
             patch("src.WarehouseManagement.WarehouseImportExport_Download_function",
                   side_effect=ValueError("Invalid option. Must be 'import' or 'export'")):

            mock_conn.return_value = mock_db_connection()  
            response = client.post("/WS/WarehouseImportExport_Download", json=payload)

        res = response.json()
        assert res["status"] == "error"
        assert "Invalid option" in res["message"]

    def test_database_error(self, client):
        """Lỗi database khi gọi API"""
        payload = {
            "request_id": "evisor-1234567890",
            "owner": "hoanvlh",
            "option": "import",
            "ticket_id": "1"
        }

        with patch("src.main.get_postgres_connection",
                   side_effect=Exception("Database connection failed")), \
             patch("src.main.check_session", return_value=True):

            response = client.post("/WS/WarehouseImportExport_Download", json=payload)

        res = response.json()
        assert res["status"] == "error"
        assert "Database connection failed" in res["message"]