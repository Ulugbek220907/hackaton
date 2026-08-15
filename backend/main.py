import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.database import engine, Base
from backend.routers import companies, offers, codes, redeem, admin

# Create tables if not created yet
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="B2B2C Discount Platform API",
    description="API for B2B2C Discount and Loyalty Marketplace Platform",
    version="1.0.0",
)

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(companies.router)
app.include_router(offers.router)
app.include_router(codes.router)
app.include_router(redeem.router)
app.include_router(admin.router)

# Static file mounts
backend_static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(backend_static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=backend_static_dir), name="static")

frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/app", StaticFiles(directory=frontend_dir, html=True), name="frontend")


@app.get("/")
def read_root():
    index_file = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Welcome to B2B2C Discount Platform API"}
