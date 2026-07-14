@echo off
call .\.venv\Scripts\activate
python -m uvicorn src.main:app --reload --reload-dir src