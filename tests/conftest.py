import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import sys
import os

# Thêm src vào path để import modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import app  # Import app từ main


@pytest.fixture(scope="session")
def event_loop():
    """Event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client():
    """Test client fixture"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_db_connection():
    """Mock database connection với đầy đủ methods"""
    class MockCursor:
        def __init__(self, fetch_data=None, execute_side_effect=None):
            self.fetch_data = fetch_data or []
            self.execute_side_effect = execute_side_effect
            self.closed = False
            self.last_query = None
            
        def execute(self, query):
            self.last_query = query
            if self.execute_side_effect:
                if isinstance(self.execute_side_effect, Exception):
                    raise self.execute_side_effect
            return None
            
        def fetchall(self):
            return self.fetch_data
            
        def close(self):
            self.closed = True

    class MockConnection:
        def __init__(self, fetch_data=None, execute_side_effect=None):
            self.cursor_instance = MockCursor(fetch_data, execute_side_effect)
            self.closed = False
            
        def cursor(self):
            return self.cursor_instance
            
        def close(self):
            self.closed = True

    return MockConnection


@pytest.fixture
def mock_main_module():
    """Mock main module để tránh lỗi import"""
    with patch.dict('sys.modules', {'src.main': Mock()}):
        yield