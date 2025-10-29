import pytest
from unittest.mock import patch
import sys
import os

# Thêm src vào path để import modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))


@pytest.fixture
def valid_warehouse_payload():
    """Payload hợp lệ cho Warehouse Statistical API"""
    return {
        "request_id": "evisor-1234567890",
        "owner": "hoanvlh"
    }


@pytest.fixture
def sample_warehouse_data():
    """Dữ liệu mẫu từ database WS_Statistical"""
    return [
        (201488, "Sản phẩm A", "Mô tả sản phẩm A", "2025-01-15 10:30:00", 
         "PN001", "Vietnam", "Cái", 100, "SN001", "Kho A", "user1", 1),
        (201489, "Sản phẩm B", "Mô tả sản phẩm B", "2025-01-16 14:20:00",
         "PN002", "China", "Cái", 50, "SN002", "Kho B", "user2", 1),
        (201490, "Sản phẩm C", "Mô tả sản phẩm C", "2025-01-17 09:15:00",
         "PN003", "Japan", "Cái", 75, "SN003", "Kho C", "user3", 0)
    ]


@pytest.fixture
def empty_warehouse_data():
    """Dữ liệu rỗng từ database"""
    return []


@pytest.fixture
def mock_success_session():
    """Mock session check thành công"""
    with patch('main.check_session') as mock_session:
        mock_session.return_value = True
        yield mock_session


@pytest.fixture
def mock_failed_session():
    """Mock session check thất bại"""
    with patch('main.check_session') as mock_session:
        mock_session.return_value = False
        yield mock_session


@pytest.fixture
def mock_database_connection():
    """Mock database connection"""
    with patch('main.get_postgres_connection') as mock_conn:
        yield mock_conn