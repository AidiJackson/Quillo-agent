"""
Pytest configuration for test suite
"""
import pytest


@pytest.fixture(scope="session")
def anyio_backend():
    """
    Configure pytest-anyio to use only asyncio backend.

    This prevents tests from being run with trio backend,
    which is not installed in this project.
    """
    return "asyncio"
