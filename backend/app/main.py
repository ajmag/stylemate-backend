#  will be the FASTAPI entry point
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
# from contextlib import asynccontextmanager

# from backend.app.core.embedding.clip_singleton import get_clip  
from backend.app.api.routes.api_test import router as test_router
from backend.app.api.routes.clothing import router as clothing_router
from backend.app.api.routes.recommendations import router as recommendations_router
from backend.app.config import settings

logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG to see all log messages
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Pre-load the CLIP model on startup
#     model, preprocess = get_clip()
#     print("✅ CLIP model pre-loaded and ready for use")
#     yield  # divides the project into two sections - Startup and Shutdown
#     print("🔄 Application shutting down...")

# Initialize FastAPI app
app = FastAPI(
    # lifespan=lifespan,
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json", # where the documentation will be available
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

# route to test the vision agent
app.include_router(test_router, prefix=f"{settings.API_V1_STR}/test", tags=["test"])

app.include_router(clothing_router, prefix=f"{settings.API_V1_STR}/clothing", tags=["clothing"])

app.include_router(recommendations_router, prefix=f"{settings.API_V1_STR}/recommendations", tags=["outfit_recommendation"])

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Root endpoint
@app.get("/")
def root():
    return {"message": "Welcome to the StyleMate System API"}