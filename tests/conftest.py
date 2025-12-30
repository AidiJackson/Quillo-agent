"""
Pytest configuration for test suite
"""
import os
import pytest

# This runs before test modules import app code.
os.environ["PYTEST_RUNNING"] = "1"


@pytest.fixture(scope="session")
def anyio_backend():
    """Use asyncio backend for anyio tests."""
    return "asyncio"
