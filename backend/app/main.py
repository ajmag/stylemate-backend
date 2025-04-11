#  will be the FASTAPI entry point
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Configure CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Root endpoint
@app.get("/")
def root():
    return {"message": "Welcome to the StyleMate System API"}