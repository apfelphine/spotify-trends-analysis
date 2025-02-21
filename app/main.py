import datetime

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from apscheduler.schedulers.background import BackgroundScheduler
from asyncio import run

from app.api import root, data_import
from app.database import create_db_and_tables
from app.business.data_import import import_songs_from_kaggle

app = FastAPI(
    title="Global Spotify Charts API",
    description="Project for class \"Geoinformationssysteme\" "
                "at City University of Applied Science Bremen "
                "- Winter Semester 2024/25",
    root_path="/api",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(root.router)
app.include_router(data_import.router)

app.mount("", StaticFiles(directory="static", html=True), name="static")

create_db_and_tables()

scheduler = BackgroundScheduler()
scheduler.start()

scheduler.add_job(
    lambda: run(import_songs_from_kaggle()),
    'cron', hour=1,  # Run import script every night at 1am for daily delta load
    next_run_time=datetime.datetime.now()  # Run script immediately upon start
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)
