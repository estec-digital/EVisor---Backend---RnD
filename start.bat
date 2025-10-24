@echo off
REM If a virtual environment exists at .venv, activate it first
if exist ".venv\Scripts\activate.bat" (
	call .venv\Scripts\activate.bat
) else (
	echo No .venv found, using system python
)

python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
