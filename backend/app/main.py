from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logger import logger
from app.core.database import engine
from app.models.base import Base
from app.routers import jobs, settings as settings_router, dashboard, logs
from app.scheduler.tasks import setup_scheduler

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(jobs.router, prefix=f"{settings.API_V1_STR}/jobs", tags=["Jobs"])
app.include_router(settings_router.router, prefix=f"{settings.API_V1_STR}/settings", tags=["Settings"])
app.include_router(dashboard.router, prefix=f"{settings.API_V1_STR}/dashboard", tags=["Dashboard"])
app.include_router(logs.router, prefix=f"{settings.API_V1_STR}/logs", tags=["Logs"])

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing database tables...")
    async with engine.begin() as conn:
        # Create all tables dynamically if they don't exist
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Starting background scheduler...")
    setup_scheduler()
    logger.info("Backend Application ready.")

@app.get("/")
def read_root():
    return {"status": "healthy", "service": "AI Job Hunter Backend"}
