@echo off
set DATABASE_URL=postgresql+psycopg://teamproject:teamproject@127.0.0.1:5432/teamproject
cd /d C:\Users\green\Desktop\teamproject\implemented_files\backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
