"""
Quillo Agent - FastAPI entrypoint
Expose FastAPI app for uvicorn (`uvicorn app:app --reload`)
"""
from quillo_agent.main import create_app

app = create_app()
