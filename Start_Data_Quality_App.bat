@echo off
set "PROJECT_DIR=C:\Users\mmrao\PycharmProjects\DATA_QUALITY_REVIEW"
set "PYTHON_EXE=%PROJECT_DIR%\.venv\Scripts\python.exe"

cd /d "%PROJECT_DIR%"

if exist "%PYTHON_EXE%" (
    "%PYTHON_EXE%" -m streamlit run ai_data_quality_platform.py
) else (
    py -3 -m streamlit run ai_data_quality_platform.py
)
