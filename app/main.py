from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from app.api import root

from app.controllers import postgis_controller # noqa

app = FastAPI(
    title="Global Spotify Charts API",
    description="Project for class \"Geoinformationssysteme\" at City University of Applied Science Bremen "
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

app.mount("", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)
