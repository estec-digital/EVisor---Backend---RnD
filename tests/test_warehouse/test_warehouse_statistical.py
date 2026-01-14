import pytest
import json
import os
import io
import sys
import pandas as pd
from fastapi import UploadFile
from unittest.mock import patch, Mock, MagicMock
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
    """Mock database connection với pagination support"""
    class MockCursor:
        def __init__(self, all_data=None):
            self.all_data = all_data or []
            self.filtered_data = all_data or []
            self.closed = False
            self.last_query = None
            self.last_params = None
            
        def execute(self, query, params=None):
            self.last_query = query
            self.last_params = params
            print(f"DEBUG MOCK: Execute called with {len(self.all_data)} items")
            return self
            
        def fetchall(self):
            print(f"DEBUG MOCK: fetchall returning {len(self.filtered_data)} items")
            return self.filtered_data
            
        def close(self):
            self.closed = True
            print("DEBUG MOCK: Cursor closed")
            
        def __enter__(self):
            return self
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.close()

    class MockConnection:
        def __init__(self, all_data=None):
            self.cursor_instance = MockCursor(all_data)
            self.closed = False
            print(f"DEBUG MOCK: Connection created with {len(all_data) if all_data else 0} items")
            
        def cursor(self, cursor_factory=None):
            print("DEBUG MOCK: cursor() called")
            return self.cursor_instance
            
        def close(self):
            self.closed = True
            print("DEBUG MOCK: Connection closed")
            
        def __enter__(self):
            return self
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.close()

    return MockConnection

################################## TEST WAREHOUSE STATISTICAL VIEW API ##################################
class TestWarehouseStatisticalViewAPI:
    """Test cases cho /WS/WarehouseStatistical_View API endpoint"""
    
    def test_success_basic_request(self, client, test_payloads, sample_data, mock_db_connection):
        """Test API thành công với request cơ bản"""
        payload = get_nested_data(test_payloads, "warehouse_statistical_view.valid_payloads[0]")
        test_data = get_nested_data(sample_data, "warehouse_statistical_data")
        
        db_data = []
        for item in test_data:
            db_data.append({
                "id": item["id"],
                "product_name": item["product_name"],
                "description": item["description"],
                "time": item["time"],
                "project_code": item["project_code"],
                "part_no": item["part_no"],
                "origin": item["origin"],
                "unit": item["unit"],
                "quantity": item["quantity"],
                "quantity_export": item["quantity_export"],
                "seri_number": item["seri_number"],
                "location": item["location"],
                "entered_by": item["entered_by"],
                "status": item["status"],
                "manufacturing_date": item["manufacturing_date"]
            })
        
        with patch('src.main.get_postgres_connection') as mock_conn, \
             patch('src.main.check_session', return_value=True):
            
            mock_conn.return_value = mock_db_connection(db_data)
            
            response = client.post("/WS/WarehouseStatistical_View", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert len(data["data"]) == len(test_data)
            
            item = data["data"][0]
            expected_keys = [
                "id", "product_name", "description", "time", "project_code",
                "part_no", "origin", "unit", "quantity_import", "quantity_export",
                "quantity_stock", "seri_number", "location", "entered_by", "status",
                "manufacturing_date"
            ]
            for key in expected_keys:
                assert key in item

    def test_success_with_filters(self, client, test_payloads, sample_data, mock_db_connection):
        """Test API thành công với filters"""
        payload = get_nested_data(test_payloads, "warehouse_statistical_view.valid_payloads[1]")
        test_data = get_nested_data(sample_data, "warehouse_statistical_data")

        print(f"=== DEBUG FILTER TEST ===")
        print(f"Payload: {payload}")
        print(f"Test data count: {len(test_data)}")

        filtered_data = [
            item for item in test_data
            if item["part_no"] == "PN001" and item["origin"] == "Vietnam"
        ]

        print(f"Filtered data count: {len(filtered_data)}")
        for item in filtered_data:
            print(f"Filtered item: {item['part_no']} - {item['origin']}")

        db_data = []
        for item in filtered_data:
            db_data.append({
                "id": item["id"],
                "product_name": item["product_name"],
                "description": item["description"],
                "time": item["time"],
                "project_code": item["project_code"],
                "part_no": item["part_no"],
                "origin": item["origin"],
                "unit": item["unit"],
                "quantity": item["quantity"],
                "quantity_export": item["quantity_export"],
                "seri_number": item["seri_number"],
                "location": item["location"],
                "entered_by": item["entered_by"],
                "status": item["status"],
                "manufacturing_date": item["manufacturing_date"]
            })

        print(f"DB data count: {len(db_data)}")

        with patch('src.main.get_postgres_connection') as mock_conn, \
            patch('src.main.check_session', return_value=True):

            mock_conn.return_value = mock_db_connection(db_data)

            response = client.post("/WS/WarehouseStatistical_View", json=payload)

            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.json()}")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
        
            print(f"Actual data length: {len(data['data'])}")
            print(f"Expected data length: {len(filtered_data)}")
        
            if len(data["data"]) != len(filtered_data):
                print(f"❌ DATA MISMATCH!")
                print(f"Returned data: {data['data']}")
        
            assert len(data["data"]) == len(filtered_data)

    def test_pagination(self, client, test_payloads, sample_data, mock_db_connection):
        """Test phân trang"""
        payload = get_nested_data(test_payloads, "warehouse_statistical_view.valid_payloads[2]")
        test_data = get_nested_data(sample_data, "warehouse_statistical_data")
        
        db_data = []
        for item in test_data:
            db_data.append({
                "id": item["id"],
                "product_name": item["product_name"],
                "description": item["description"],
                "time": item["time"],
                "project_code": item["project_code"],
                "part_no": item["part_no"],
                "origin": item["origin"],
                "unit": item["unit"],
                "quantity": item["quantity"],
                "quantity_export": item["quantity_export"],
                "seri_number": item["seri_number"],
                "location": item["location"],
                "entered_by": item["entered_by"],
                "status": item["status"],
                "manufacturing_date": item["manufacturing_date"]
            })
        
        with patch('src.main.get_postgres_connection') as mock_conn, \
             patch('src.main.check_session', return_value=True):
            
            mock_conn.return_value = mock_db_connection(db_data)
            
            response = client.post("/WS/WarehouseStatistical_View", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert len(data["data"]) <= payload["page_size"]

    def test_invalid_session(self, client, test_payloads, sample_data, mock_db_connection):
        """Test với session không hợp lệ"""
        payload = get_nested_data(test_payloads, "warehouse_statistical_view.valid_payloads[0]")
        test_data = get_nested_data(sample_data, "warehouse_statistical_data")
        
        with patch('src.main.get_postgres_connection') as mock_conn, \
             patch('src.main.check_session', return_value=False):
            
            mock_conn.return_value = mock_db_connection(test_data)
            
            response = client.post("/WS/WarehouseStatistical_View", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"
            assert "Phiên làm việc" in data["message"]

    def test_database_error(self, client, test_payloads):
        """Test với lỗi database"""
        payload = get_nested_data(test_payloads, "warehouse_statistical_view.valid_payloads[0]")
        
        with patch('src.main.get_postgres_connection') as mock_conn, \
             patch('src.main.check_session', return_value=True):
            
            mock_conn.side_effect = Exception("Database connection failed")
            
            response = client.post("/WS/WarehouseStatistical_View", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"
            assert "Database connection failed" in data["message"]

    def test_empty_result(self, client, test_payloads, sample_data, mock_db_connection):
        """Test khi không có dữ liệu"""
        payload = get_nested_data(test_payloads, "warehouse_statistical_view.valid_payloads[0]")
        empty_data = get_nested_data(sample_data, "empty_data")
        
        with patch('src.main.get_postgres_connection') as mock_conn, \
             patch('src.main.check_session', return_value=True):
            
            mock_conn.return_value = mock_db_connection(empty_data)
            
            response = client.post("/WS/WarehouseStatistical_View", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert len(data["data"]) == 0


class TestWarehouseStatisticalViewDynamic:
    """Test cases động từ JSON test_cases"""
    
    def test_success_cases_dynamic(self, client, test_cases, test_payloads, sample_data, mock_db_connection):
        """Test success cases được định nghĩa trong JSON"""
        success_cases = test_cases.get("warehouse_statistical_view_success_cases", [])

        for test_case in success_cases:
            print(f"Running test case: {test_case['name']}")

            payload = get_nested_data(test_payloads, test_case['payload_key'])
            all_test_data = get_nested_data(sample_data, test_case['data_key'])

            filtered_data = self._apply_filters(all_test_data, payload)
        
            print(f"DEBUG: Test case '{test_case['name']}'")
            print(f"DEBUG: All data count: {len(all_test_data)}")
            print(f"DEBUG: Filtered data count: {len(filtered_data)}")
            print(f"DEBUG: Expected count: {test_case['expected_data_length']}")

            db_data = []
            for item in filtered_data:
                db_data.append({
                    "id": item["id"],
                    "product_name": item["product_name"],
                    "description": item["description"],
                    "time": item["time"],
                    "project_code": item["project_code"],
                    "part_no": item["part_no"],
                    "origin": item["origin"],
                    "unit": item["unit"],
                    "quantity": item["quantity"],
                    "quantity_export": item["quantity_export"],
                    "seri_number": item["seri_number"],
                    "location": item["location"],
                    "entered_by": item["entered_by"],
                    "status": item["status"],
                    "manufacturing_date": item["manufacturing_date"]
                })

            with patch('src.main.get_postgres_connection') as mock_conn, \
                patch('src.main.check_session', return_value=True):

                mock_conn.return_value = mock_db_connection(db_data)

                response = client.post("/WS/WarehouseStatistical_View", json=payload)

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == test_case["expected_status"]
            
                print(f"DEBUG: Actual data count: {len(data['data'])}")
                print(f"DEBUG: Expected data count: {test_case['expected_data_length']}")
            
                assert len(data["data"]) == test_case["expected_data_length"]

    def _apply_filters(self, data, payload):
        """Áp dụng filter từ payload lên test data"""
        filtered_data = data.copy()
        filter_obj = payload.get("filter", {})
        
        if filter_obj.get("part_no"):
            part_no_filter = filter_obj["part_no"].lower()
            filtered_data = [item for item in filtered_data 
                           if part_no_filter in item["part_no"].lower()]
        
        if filter_obj.get("origin"):
            origin_filter = filter_obj["origin"].lower()
            filtered_data = [item for item in filtered_data 
                           if origin_filter in item["origin"].lower()]
        
        if filter_obj.get("seri_number"):
            seri_filter = filter_obj["seri_number"].lower()
            filtered_data = [item for item in filtered_data 
                           if seri_filter in item["seri_number"].lower()]
        
        if filter_obj.get("project_code"):
            project_filter = filter_obj["project_code"].lower()
            filtered_data = [item for item in filtered_data 
                           if project_filter in item["project_code"].lower()]
        
        if filter_obj.get("datetime_import"):
            import_date = filter_obj["datetime_import"][:10]  
            filtered_data = [item for item in filtered_data 
                           if item["time"].startswith(import_date)]
        
        return filtered_data

    def test_error_cases_dynamic(self, client, test_cases, test_payloads, mock_db_connection):
        """Test error cases được định nghĩa trong JSON"""
        error_cases = test_cases.get("warehouse_statistical_view_error_cases", [])
        
        for test_case in error_cases:
            print(f"Running error test case: {test_case['name']}")
            
            payload = get_nested_data(test_payloads, test_case['payload_key'])
            
            if test_case.get("mock_session") is False:
                with patch('src.main.get_postgres_connection') as mock_conn, \
                     patch('src.main.check_session', return_value=False):
                    
                    mock_conn.return_value = mock_db_connection()
                    response = client.post("/WS/WarehouseStatistical_View", json=payload)
                    
            elif test_case.get("mock_connection_error"):
                with patch('src.main.get_postgres_connection') as mock_conn, \
                     patch('src.main.check_session', return_value=True):
                    
                    mock_conn.side_effect = Exception(test_case["mock_connection_error"])
                    response = client.post("/WS/WarehouseStatistical_View", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == test_case["expected_status"]
            assert test_case["expected_message_contains"] in data["message"]

class TestWarehouseStatisticalViewFunction:
    """Test function WarehouseStatistical_View_function trực tiếp"""
    
    def test_function_success(self, sample_data, mock_db_connection):
        """Test function thành công"""
        from src.main import WarehouseStatistical_View_function, WarehouseStatistical_View, FilterModel_WarehouseStatistical
        
        test_data = get_nested_data(sample_data, "warehouse_statistical_data")
        
        db_data = []
        for item in test_data:
            db_data.append({
                "id": item["id"],
                "product_name": item["product_name"],
                "description": item["description"],
                "time": item["time"],
                "project_code": item["project_code"],
                "part_no": item["part_no"],
                "origin": item["origin"],
                "unit": item["unit"],
                "quantity": item["quantity"],
                "quantity_export": item["quantity_export"],
                "seri_number": item["seri_number"],
                "location": item["location"],
                "entered_by": item["entered_by"],
                "status": item["status"],
                "manufacturing_date": item["manufacturing_date"]
            })
        
        filter_model = FilterModel_WarehouseStatistical(
            part_no=None,
            origin=None,
            seri_number=None,
            project_code=None,
            datetime_import=None
        )
        
        input_obj = WarehouseStatistical_View(
            request_id="evisor-test-123",
            owner="hoanvlh",
            filter=filter_model,
            pagination=1,
            page_size=20
        )
        
        mock_conn = mock_db_connection(db_data)
        
        result = WarehouseStatistical_View_function(input_obj, mock_conn)
        
        assert result["status"] == "success"
        assert len(result["data"]) == len(test_data)
        
        assert mock_conn.cursor_instance.closed is True


########################### TEST WAREHOUSE STATISTICAL DASHBOARD API ###########################
class TestWarehouseStatisticalDashboardAPI:
    """Test cases cho /WS/WarehouseStatistical_Dashboard API endpoint"""
    
    def _create_simple_dashboard_mock(self, point_data=None, list_data=None, chart_data=None):
        """Tạo mock connection đơn giản cho dashboard"""
        class SimpleDashboardCursor:
            def __init__(self):
                self.query_count = 0
                
            def execute(self, query, params=None):
                self.query_count += 1
                return self
                
            def fetchone(self):
                if self.query_count == 1:  
                    return (point_data["total_product"] if point_data else 150,)
                elif self.query_count == 2: 
                    return (point_data["import_by_date"] if point_data else 25,)
                elif self.query_count == 3: 
                    return (point_data["export_by_date"] if point_data else 18,)
                elif self.query_count == 4:  
                    return (point_data["not_installation_by_date"] if point_data else 7,)
                elif self.query_count == 5:  
                    return (
                        point_data["total_PO"] if point_data else 45,
                        point_data["total_project"] if point_data else 12
                    )
                else:
                    return (0,)
                    
            def fetchall(self):
                if self.query_count == 6: 
                    return list_data["import"] if list_data else [("PROJ-A", 100), ("PROJ-B", 75), ("PROJ-C", 50)]
                elif self.query_count == 7: 
                    return list_data["export"] if list_data else [("PROJ-A", 60), ("PROJ-B", 40), ("PROJ-C", 25)]
                elif self.query_count == 8:  
                    return list_data["installation"] if list_data else [("PROJ-A", 35), ("PROJ-B", 20), ("PROJ-C", 15)]
                elif self.query_count == 9:  
                    return chart_data["day"] if chart_data else [("2025-01-15", 50, 25), ("2025-01-16", 75, 40), ("2025-01-17", 100, 60)]
                elif self.query_count == 10: 
                    return chart_data["week"] if chart_data else [("2025-W03", 200, 100), ("2025-W04", 300, 150), ("2025-W05", 250, 120)]
                elif self.query_count == 11: 
                    return chart_data["month"] if chart_data else [("2025-01", 1000, 600), ("2025-02", 1200, 700), ("2025-03", 900, 550)]
                elif self.query_count == 12:  
                    return chart_data["quarter"] if chart_data else [("2025-Q1", 3000, 1800), ("2025-Q2", 3500, 2100), ("2025-Q3", 3200, 1900)]
                elif self.query_count == 13:  
                    return chart_data["year"] if chart_data else [("2024", 12000, 8000), ("2025", 15000, 10000)]
                else:
                    return []
                    
            def close(self):
                pass
                
            def __enter__(self):
                return self
                
            def __exit__(self, exc_type, exc_val, exc_tb):
                self.close()

        class SimpleDashboardConnection:
            def cursor(self):
                return SimpleDashboardCursor()
                
            def close(self):
                pass
                
            def __enter__(self):
                return self
                
            def __exit__(self, exc_type, exc_val, exc_tb):
                self.close()

        return SimpleDashboardConnection()

    def test_dashboard_success_basic(self, client, test_payloads):
        """Test Dashboard API thành công với date range cơ bản"""
        payload = get_nested_data(test_payloads, "warehouse_statistical_dashboard.valid_payloads[0]")
        
        with patch('src.main.get_postgres_connection') as mock_conn, \
             patch('src.main.check_session', return_value=True):
            
            mock_conn.return_value = self._create_simple_dashboard_mock()
            
            response = client.post("/WS/WarehouseStatistical_Dashboard", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            
            point_data = data["point"]
            expected_point_keys = ["total_product", "import_by_date", "export_by_date", 
                                 "not_installation_by_date", "total_PO", "total_project"]
            for key in expected_point_keys:
                assert key in point_data
                assert isinstance(point_data[key], (int, float))
            
            list_data = data["list"]
            expected_list_keys = ["import", "export", "installation"]
            for key in expected_list_keys:
                assert key in list_data
                assert isinstance(list_data[key], list)
                assert len(list_data[key]) > 0  
            
            chart_data = data["chart"]
            assert "pie_chart" in chart_data
            assert "bar_chart" in chart_data
            assert "import_quantity" in chart_data["pie_chart"]
            assert "export_quantity" in chart_data["pie_chart"]
            
            expected_ranges = ["day", "week", "month", "quarter", "year"]
            for range_type in expected_ranges:
                assert range_type in chart_data["bar_chart"]
                range_data = chart_data["bar_chart"][range_type]
                assert "datetime_data" in range_data
                assert "import_data" in range_data
                assert "export_data" in range_data
                assert len(range_data["datetime_data"]) > 0

    def test_dashboard_empty_data(self, client, test_payloads):
        """Test Dashboard API khi không có dữ liệu"""
        payload = get_nested_data(test_payloads, "warehouse_statistical_dashboard.valid_payloads[1]")
        
        empty_point_data = {
            "total_product": 0,
            "import_by_date": 0, 
            "export_by_date": 0,
            "not_installation_by_date": 0,
            "total_PO": 0,
            "total_project": 0
        }
        
        empty_list_data = {
            "import": [],
            "export": [],
            "installation": []
        }
        
        empty_chart_data = {
            "day": [],
            "week": [],
            "month": [],
            "quarter": [],
            "year": []
        }
        
        with patch('src.main.get_postgres_connection') as mock_conn, \
             patch('src.main.check_session', return_value=True):
            
            mock_conn.return_value = self._create_simple_dashboard_mock(
                point_data=empty_point_data,
                list_data=empty_list_data, 
                chart_data=empty_chart_data
            )
            
            response = client.post("/WS/WarehouseStatistical_Dashboard", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            
            point_data = data["point"]
            for key in point_data:
                assert point_data[key] == 0
            
            list_data = data["list"]
            for key in list_data:
                assert len(list_data[key]) == 0

    def test_dashboard_invalid_session(self, client, test_payloads):
        """Test Dashboard API với session không hợp lệ"""
        payload = get_nested_data(test_payloads, "warehouse_statistical_dashboard.valid_payloads[0]")
        
        with patch('src.main.get_postgres_connection') as mock_conn, \
             patch('src.main.check_session', return_value=False):
            
            mock_conn.return_value = None
            
            response = client.post("/WS/WarehouseStatistical_Dashboard", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"
            assert "Phiên làm việc" in data["message"]

    def test_dashboard_database_error(self, client, test_payloads):
        """Test Dashboard API với lỗi database"""
        payload = get_nested_data(test_payloads, "warehouse_statistical_dashboard.valid_payloads[0]")
        
        with patch('src.main.get_postgres_connection') as mock_conn, \
             patch('src.main.check_session', return_value=True):
            
            mock_conn.side_effect = Exception("Database connection failed")
            
            response = client.post("/WS/WarehouseStatistical_Dashboard", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"
            assert "Database connection failed" in data["message"]

    def test_dashboard_with_sample_data(self, client, test_payloads, sample_data):
        """Test Dashboard API với sample data từ JSON"""
        payload = get_nested_data(test_payloads, "warehouse_statistical_dashboard.valid_payloads[0]")
        dashboard_data = get_nested_data(sample_data, "dashboard_sample_data")
        
        point_data = dashboard_data["point_data"]
        
        list_data = {
            "import": [
                (item["project_code"], item["total_quantity"]) 
                for item in dashboard_data["list_data"]["import"]
            ],
            "export": [
                (item["project_code"], item["total_quantity"]) 
                for item in dashboard_data["list_data"]["export"]
            ],
            "installation": [
                (item["project_code"], item["total_quantity"]) 
                for item in dashboard_data["list_data"]["installation"]
            ]
        }
        
        chart_data = {
            "day": [
                (date, imp, exp) for date, imp, exp in zip(
                    dashboard_data["chart_data"]["bar_chart"]["day"]["datetime_data"],
                    dashboard_data["chart_data"]["bar_chart"]["day"]["import_data"],
                    dashboard_data["chart_data"]["bar_chart"]["day"]["export_data"]
                )
            ],
            "week": [
                (date, imp, exp) for date, imp, exp in zip(
                    dashboard_data["chart_data"]["bar_chart"]["week"]["datetime_data"],
                    dashboard_data["chart_data"]["bar_chart"]["week"]["import_data"],
                    dashboard_data["chart_data"]["bar_chart"]["week"]["export_data"]
                )
            ],
            "month": [
                (date, imp, exp) for date, imp, exp in zip(
                    dashboard_data["chart_data"]["bar_chart"]["month"]["datetime_data"],
                    dashboard_data["chart_data"]["bar_chart"]["month"]["import_data"],
                    dashboard_data["chart_data"]["bar_chart"]["month"]["export_data"]
                )
            ],
            "quarter": [
                (date, imp, exp) for date, imp, exp in zip(
                    dashboard_data["chart_data"]["bar_chart"]["quarter"]["datetime_data"],
                    dashboard_data["chart_data"]["bar_chart"]["quarter"]["import_data"],
                    dashboard_data["chart_data"]["bar_chart"]["quarter"]["export_data"]
                )
            ],
            "year": [
                (date, imp, exp) for date, imp, exp in zip(
                    dashboard_data["chart_data"]["bar_chart"]["year"]["datetime_data"],
                    dashboard_data["chart_data"]["bar_chart"]["year"]["import_data"],
                    dashboard_data["chart_data"]["bar_chart"]["year"]["export_data"]
                )
            ]
        }
        
        with patch('src.main.get_postgres_connection') as mock_conn, \
             patch('src.main.check_session', return_value=True):
            
            mock_conn.return_value = self._create_simple_dashboard_mock(
                point_data=point_data,
                list_data=list_data,
                chart_data=chart_data
            )
            
            response = client.post("/WS/WarehouseStatistical_Dashboard", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            
            point_result = data["point"]
            for key in point_data:
                assert point_result[key] == point_data[key]


class TestWarehouseStatisticalDashboardDynamic:
    """Test cases động cho Dashboard API với mock đơn giản"""
    
    def test_dashboard_success_cases_dynamic(self, client, test_cases, test_payloads):
        """Test dashboard success cases được định nghĩa trong JSON"""
        success_cases = test_cases.get("warehouse_statistical_dashboard_success_cases", [])
        
        for test_case in success_cases:
            print(f"Running dashboard test case: {test_case['name']}")
            
            payload = get_nested_data(test_payloads, test_case['payload_key'])
            
            test_instance = TestWarehouseStatisticalDashboardAPI()
            
            with patch('src.main.get_postgres_connection') as mock_conn, \
                 patch('src.main.check_session', return_value=True):
                
                mock_conn.return_value = test_instance._create_simple_dashboard_mock()
                
                response = client.post("/WS/WarehouseStatistical_Dashboard", json=payload)
                
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == test_case["expected_status"]
                
                for key in test_case["expected_point_data_keys"]:
                    assert key in data["point"]
                
                for key in test_case["expected_list_data_keys"]:
                    assert key in data["list"]
                
                for key in test_case["expected_chart_data_keys"]:
                    assert key in data["chart"]


############################ TEST WAREHOUSE STATISTICAL VIEW DETAIL API ############################
class TestWarehouseStatisticalViewDetailAPI:
    """Test cases cho /WS/WarehouseStatistical_View_Detail API endpoint"""
    
    def _create_simple_detail_mock(self, db_data=None):
        """Tạo mock connection đơn giản cho detail view với cursor tracking"""
        class SimpleDetailCursor:
            def __init__(self, db_data):
                self.query_count = 0
                self.last_query = None
                self.last_params = None
                self.db_data = db_data
            
            def execute(self, query, params=None):
                self.query_count += 1
                self.last_query = query
                self.last_params = params
                return self
            
            def fetchone(self):
                return self.db_data
            
            def close(self):
                pass
            
            def __enter__(self):
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                self.close()

        class SimpleDetailConnection:
            def __init__(self, db_data):
                self.db_data = db_data
                self.cursor_instance = None
            
            def cursor(self):
                self.cursor_instance = SimpleDetailCursor(self.db_data)
                return self.cursor_instance
            
            def close(self):
                pass
            
            def __enter__(self):
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                self.close()

        return SimpleDetailConnection(db_data)

    def test_detail_success_existing_item(self, client, test_payloads, sample_data):
        """Test Detail API thành công với ID tồn tại"""
        payload = get_nested_data(test_payloads, "warehouse_statistical_detail_view.valid_payloads[0]")
        db_data = get_nested_data(sample_data, "warehouse_statistical_detail_data.item_1")
        
        with patch('src.main.get_postgres_connection') as mock_conn, \
             patch('src.main.check_session', return_value=True):
            
            mock_conn.return_value = self._create_simple_detail_mock(db_data)
            
            response = client.post("/WS/WarehouseStatistical_View_Detail", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "data" in data
            
            item = data["data"]
            expected_keys = [
                "id", "product_name", "description", "time", "part_no", 
                "origin", "unit", "quantity", "seri_number", "location", 
                "entered_by", "status"
            ]
            for key in expected_keys:
                assert key in item
            
            assert item["id"] == db_data[0]
            assert item["product_name"] == db_data[1]
            assert item["description"] == db_data[2]
            assert item["quantity"] == db_data[7]

    def test_detail_item_not_found(self, client, test_payloads, sample_data):
        """Test Detail API khi item không tồn tại"""
        payload = get_nested_data(test_payloads, "warehouse_statistical_detail_view.edge_case_payloads[0]")
    
        print(f"=== DEBUG PAYLOAD STRUCTURE ===")
        print(f"Payload: {payload}")
        print(f"Payload type: {type(payload)}")
        print(f"Payload keys: {list(payload.keys()) if isinstance(payload, dict) else 'Not a dict'}")
    
        if isinstance(payload, dict) and "payload" in payload:
            actual_payload = payload["payload"]
            print(f"Actual payload: {actual_payload}")
            print(f"Actual payload keys: {list(actual_payload.keys())}")
        else:
            actual_payload = payload

        with patch('src.main.get_postgres_connection') as mock_conn, \
            patch('src.main.check_session', return_value=True):

            mock_conn.return_value = self._create_simple_detail_mock(None)  

            response = client.post("/WS/WarehouseStatistical_View_Detail", json=actual_payload)

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"
            assert "not found" in data["message"].lower()
        
            if "id" in actual_payload:
                assert str(actual_payload["id"]) in data["message"]
            else:
                print(f"WARNING: 'id' not found in payload: {actual_payload}")
                assert True

    def test_detail_invalid_session(self, client, test_payloads, sample_data):
        """Test Detail API với session không hợp lệ"""
        payload = get_nested_data(test_payloads, "warehouse_statistical_detail_view.valid_payloads[0]")
        db_data = get_nested_data(sample_data, "warehouse_statistical_detail_data.item_1")
        
        with patch('src.main.get_postgres_connection') as mock_conn, \
             patch('src.main.check_session', return_value=False):
            
            mock_conn.return_value = self._create_simple_detail_mock(db_data)
            
            response = client.post("/WS/WarehouseStatistical_View_Detail", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"
            assert "Phiên làm việc" in data["message"]

    def test_detail_database_error(self, client, test_payloads):
        """Test Detail API với lỗi database"""
        payload = get_nested_data(test_payloads, "warehouse_statistical_detail_view.valid_payloads[0]")
        
        with patch('src.main.get_postgres_connection') as mock_conn, \
             patch('src.main.check_session', return_value=True):
            
            mock_conn.side_effect = Exception("Database connection failed")
            
            response = client.post("/WS/WarehouseStatistical_View_Detail", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"
            assert "Database connection failed" in data["message"]

    def test_detail_different_ids(self, client, test_payloads, sample_data):
        """Test Detail API với các ID khác nhau"""
        test_cases = [
            ("warehouse_statistical_detail_view.valid_payloads[0]", "warehouse_statistical_detail_data.item_1"),
            ("warehouse_statistical_detail_view.valid_payloads[1]", "warehouse_statistical_detail_data.item_2"), 
            ("warehouse_statistical_detail_view.valid_payloads[2]", "warehouse_statistical_detail_data.item_3")
        ]
        
        for payload_key, data_key in test_cases:
            payload = get_nested_data(test_payloads, payload_key)
            db_data = get_nested_data(sample_data, data_key)
            
            with patch('src.main.get_postgres_connection') as mock_conn, \
                 patch('src.main.check_session', return_value=True):
                
                mock_conn.return_value = self._create_simple_detail_mock(db_data)
                
                response = client.post("/WS/WarehouseStatistical_View_Detail", json=payload)
                
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "success"
                assert data["data"]["id"] == payload["id"]

    def get_payload_safely(self, test_payloads, key_path):
        """Lấy payload một cách an toàn, xử lý cả nested structure"""
        test_case_data = get_nested_data(test_payloads, key_path)
        
        if isinstance(test_case_data, dict) and "payload" in test_case_data:
            return test_case_data["payload"]
        else:
            return test_case_data

    def test_detail_query_validation(self, client, test_payloads, sample_data):
        """Test Detail API validation - query được gọi với đúng parameters"""
        payload = self.get_payload_safely(test_payloads, "warehouse_statistical_detail_view.valid_payloads[0]")
        db_data = get_nested_data(sample_data, "warehouse_statistical_detail_data.item_1")

        with patch('src.main.get_postgres_connection') as mock_conn, \
            patch('src.main.check_session', return_value=True):

            mock_connection = self._create_simple_detail_mock(db_data)
            mock_conn.return_value = mock_connection

            response = client.post("/WS/WarehouseStatistical_View_Detail", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"

            cursor = mock_connection.cursor_instance
            assert cursor is not None, "Cursor should not be None"
            assert cursor.last_query is not None, "Last query should not be None"
            assert "SELECT * FROM \"WS_Statistical\" WHERE id = %s" in cursor.last_query
            assert cursor.last_params == (payload["id"],)


class TestWarehouseStatisticalViewDetailDynamic:
    """Test cases động cho Detail API"""
    
    def test_detail_success_cases_dynamic(self, client, test_cases, test_payloads, sample_data):
        """Test detail success cases được định nghĩa trong JSON"""
        success_cases = test_cases.get("warehouse_statistical_detail_success_cases", [])
        
        for test_case in success_cases:
            print(f"Running detail test case: {test_case['name']}")
            
            payload = get_nested_data(test_payloads, test_case['payload_key'])
            db_data = get_nested_data(sample_data, test_case['data_key'])
            
            test_instance = TestWarehouseStatisticalViewDetailAPI()
            
            with patch('src.main.get_postgres_connection') as mock_conn, \
                 patch('src.main.check_session', return_value=True):
                
                mock_conn.return_value = test_instance._create_simple_detail_mock(db_data)
                
                response = client.post("/WS/WarehouseStatistical_View_Detail", json=payload)
                
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == test_case["expected_status"]
                
                if test_case["expected_data_structure"] == "object":
                    assert isinstance(data["data"], dict)
                    assert "id" in data["data"]

    def test_detail_error_cases_dynamic(self, client, test_cases, test_payloads, sample_data):
        """Test detail error cases được định nghĩa trong JSON"""
        error_cases = test_cases.get("warehouse_statistical_detail_error_cases", [])
        
        for test_case in error_cases:
            print(f"Running detail error test case: {test_case['name']}")
            
            payload = get_nested_data(test_payloads, test_case['payload_key'])
            
            test_instance = TestWarehouseStatisticalViewDetailAPI()
            
            if test_case.get("mock_session") is False:
                with patch('src.main.get_postgres_connection') as mock_conn, \
                     patch('src.main.check_session', return_value=False):
                    
                    mock_conn.return_value = test_instance._create_simple_detail_mock()
                    response = client.post("/WS/WarehouseStatistical_View_Detail", json=payload)
                    
            elif test_case.get("mock_connection_error"):
                with patch('src.main.get_postgres_connection') as mock_conn, \
                     patch('src.main.check_session', return_value=True):
                    
                    mock_conn.side_effect = Exception(test_case["mock_connection_error"])
                    response = client.post("/WS/WarehouseStatistical_View_Detail", json=payload)
                    
            else:
                with patch('src.main.get_postgres_connection') as mock_conn, \
                     patch('src.main.check_session', return_value=True):
                    
                    mock_conn.return_value = test_instance._create_simple_detail_mock(None)
                    response = client.post("/WS/WarehouseStatistical_View_Detail", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == test_case["expected_status"]
            assert test_case["expected_message_contains"].lower() in data["message"].lower()


class TestWarehouseStatisticalViewDetailFunction:
    """Test function WarehouseStatistical_View_Detail_function trực tiếp"""
    
    def test_function_success(self, sample_data):
        """Test function thành công"""
        from src.main import WarehouseStatistical_View_Detail_function, WarehouseStatistical_View_Detail
        
        db_data = get_nested_data(sample_data, "warehouse_statistical_detail_data.item_1")
        
        input_obj = WarehouseStatistical_View_Detail(
            request_id="evisor-test-123",
            owner="hoanvlh", 
            id=1
        )
        
        test_instance = TestWarehouseStatisticalViewDetailAPI()
        mock_conn = test_instance._create_simple_detail_mock(db_data)
        
        result = WarehouseStatistical_View_Detail_function(input_obj, mock_conn)
        
        assert result["status"] == "success"
        assert "data" in result
        assert result["data"]["id"] == db_data[0]
        assert result["data"]["product_name"] == db_data[1]
        
    def test_function_item_not_found(self):
        """Test function khi item không tồn tại"""
        from src.main import WarehouseStatistical_View_Detail_function, WarehouseStatistical_View_Detail
        
        input_obj = WarehouseStatistical_View_Detail(
            request_id="evisor-test-123",
            owner="hoanvlh",
            id=999999
        )
        
        test_instance = TestWarehouseStatisticalViewDetailAPI()
        mock_conn = test_instance._create_simple_detail_mock(None)
        
        result = WarehouseStatistical_View_Detail_function(input_obj, mock_conn)
        
        assert result["status"] == "error"
        assert "not found" in result["message"].lower()
        assert "999999" in result["message"]


############################## TEST WAREHOUSE STATISTICAL UPLOAD API ##############################
class TestWarehouseStatisticalUploadAPI:
    """Test cases cho /WS/WarehouseStatistical_Upload API endpoint"""

    def _create_mock_conn(self):
        """Mock connection để test insert"""
        class MockCursor:
            def __init__(self):
                self.executed = []
                self.closed = False
            def execute(self, query, params=None):
                self.executed.append((query, params))
            def close(self):
                self.closed = True
            def __enter__(self): return self
            def __exit__(self, *args): self.close()
        class MockConnection:
            def __init__(self):
                self.cursor_instance = MockCursor()
            def cursor(self): return self.cursor_instance
            def commit(self): pass
            def close(self): pass
        return MockConnection()

    def test_upload_xlsx_success(self, client):
        """Test upload file Excel thành công"""
        df = pd.DataFrame({
            "Tên sản phẩm": ["Sản phẩm A", "Sản phẩm B"],
            "Thông tin sản phẩm": ["Mô tả A", "Mô tả B"],
            "Ngày tạo": ["15/01/2025", "16/01/2025"],
            "Mã sản phẩm": ["PN001", "PN002"],
            "Nhà sản xuất": ["Vietnam", "China"],
            "Đơn vị": ["Cái", "Cái"],
            "Seri sản phẩm": ["SN001", "SN002"],
            "Người tạo": ["user1", "user2"]
        })
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)
        upload_file = UploadFile(filename="test.xlsx", file=buffer)

        with patch("src.main.get_postgres_connection") as mock_conn, \
             patch("src.main.check_session", return_value=True):
            mock_conn.return_value = self._create_mock_conn()
            response = client.post(
                "/WS/WarehouseStatistical_Upload",
                files={"file": ("test.xlsx", buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                data={"request_id": "evisor-1234567890", "owner": "hoanvlh"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "Import dữ liệu thành công" in data["message"]

    def test_upload_invalid_file_format(self, client):
        """Test upload định dạng file không hợp lệ"""
        fake_file = io.BytesIO(b"invalid content")
        with patch("src.main.check_session", return_value=True):
            response = client.post(
                "/WS/WarehouseStatistical_Upload",
                files={"file": ("test.txt", fake_file, "text/plain")},
                data={"request_id": "evisor-1234567890", "owner": "hoanvlh"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"
            assert "không được hỗ trợ" in data["message"]

    def test_upload_invalid_session(self, client):
        """Test khi phiên làm việc hết hạn"""
        fake_file = io.BytesIO(b"fake")
        with patch("src.main.get_postgres_connection") as mock_conn, \
             patch("src.main.check_session", return_value=False):
            mock_conn.return_value = self._create_mock_conn()
            response = client.post(
                "/WS/WarehouseStatistical_Upload",
                files={"file": ("test.csv", fake_file, "text/csv")},
                data={"request_id": "evisor-1234567890", "owner": "hoanvlh"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"
            assert "Phiên làm việc" in data["message"]

    def test_upload_database_error(self, client):
        """Test lỗi khi kết nối database"""
        fake_file = io.BytesIO(b"some data")
        with patch("src.main.get_postgres_connection") as mock_conn, \
             patch("src.main.check_session", return_value=True):
            mock_conn.side_effect = Exception("Database connection failed")
            response = client.post(
                "/WS/WarehouseStatistical_Upload",
                files={"file": ("test.csv", fake_file, "text/csv")},
                data={"request_id": "evisor-1234567890", "owner": "hoanvlh"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"
            assert "Database connection failed" in data["message"]


############################## TEST WAREHOUSE STATISTICAL UPLOAD BY IM/EXPORT ##############################
class TestWarehouseStatisticalUploadByImportExportAPI:
    """Test cases cho /WS/WarehouseStatistical_Upload_By_ImportExport API endpoint"""

    def _create_mock_conn(self):
        """Mock connection để test insert"""
        class MockCursor:
            def __init__(self):
                self.executed = []
                self.closed = False
            def execute(self, query, params=None):
                self.executed.append((query, params))
            def close(self):
                self.closed = True
            def __enter__(self): return self
            def __exit__(self, *args): self.close()
        class MockConnection:
            def __init__(self):
                self.cursor_instance = MockCursor()
            def cursor(self): return self.cursor_instance
            def commit(self): pass
            def close(self): pass
        return MockConnection()

    def test_upload_importexport_xlsx_success(self, client):
        """Test upload file Excel (.xlsx) hợp lệ"""
        df = pd.DataFrame({
            "Tên hàng": ["Thiết bị A", "Thiết bị B"],
            "Mã hàng": ["MH001", "MH002"],
            "Số lượng": [5, 10],
            "Hãng": ["Vietnam", "China"],
            "Seri No.": ["SN001", "SN002"],
            "Thời gian": ["15/01/2025", "16/01/2025"]
        })
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False, header=True, engine="openpyxl")
        buffer.seek(0)

        with patch("src.main.get_postgres_connection") as mock_conn, \
             patch("src.main.check_session", return_value=True):
            mock_conn.return_value = self._create_mock_conn()

            response = client.post(
                "/WS/WarehouseStatistical_Upload_By_ImportExport",
                files={"file": ("import_export.xlsx", buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                data={"request_id": "evisor-1234567890", "owner": "hoanvlh"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "Import dữ liệu thành công" in data["message"]

    def test_upload_importexport_invalid_file_format(self, client):
        """Test upload file định dạng không hợp lệ (.txt)"""
        fake_file = io.BytesIO(b"invalid content")
        with patch("src.main.check_session", return_value=True):
            response = client.post(
                "/WS/WarehouseStatistical_Upload_By_ImportExport",
                files={"file": ("test.txt", fake_file, "text/plain")},
                data={"request_id": "evisor-1234567890", "owner": "hoanvlh"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"
            assert "không được hỗ trợ" in data["message"]

    def test_upload_importexport_invalid_session(self, client):
        """Test khi phiên làm việc hết hạn"""
        fake_file = io.BytesIO(b"fake")
        with patch("src.main.get_postgres_connection") as mock_conn, \
             patch("src.main.check_session", return_value=False):
            mock_conn.return_value = self._create_mock_conn()

            response = client.post(
                "/WS/WarehouseStatistical_Upload_By_ImportExport",
                files={"file": ("test.csv", fake_file, "text/csv")},
                data={"request_id": "evisor-1234567890", "owner": "hoanvlh"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"
            assert "Phiên làm việc" in data["message"]

    def test_upload_importexport_database_error(self, client):
        """Test lỗi kết nối database"""
        fake_file = io.BytesIO(b"some data")
        with patch("src.main.get_postgres_connection") as mock_conn, \
             patch("src.main.check_session", return_value=True):
            mock_conn.side_effect = Exception("Database connection failed")

            response = client.post(
                "/WS/WarehouseStatistical_Upload_By_ImportExport",
                files={"file": ("test.csv", fake_file, "text/csv")},
                data={"request_id": "evisor-1234567890", "owner": "hoanvlh"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"
            assert "Database connection failed" in data["message"]