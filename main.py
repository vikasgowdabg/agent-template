from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel
import asyncio

from src.agent.agent_factory import create_agent
from src import Settings, logger
from src.db.mongo_client import Database
from src.utils.cache import clear_all_cache


# Request/Response Models
class AgentRequest(BaseModel):
    user_prompt: str


class AgentResponse(BaseModel):
    result: dict
    metadata: dict


class ClearCacheResponse(BaseModel):
    """Response for cache clear operation."""
    success: bool
    message: str


# Lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for FastAPI application.
    
    Initializes MongoDB connection if MONGO_CONNECTION_STRING is provided.
    """
    settings = Settings()
    
    # Initialize MongoDB if connection string is provided
    if settings.MONGO_CONNECTION_STRING:
        try:
            Database.init_client(settings.MONGO_CONNECTION_STRING)
            ping_response = Database.client().admin.command("ping")
            if int(ping_response["ok"]) != 1:
                raise Exception("Problem connecting to database cluster.")
            logger.info("Connected to MongoDB cluster.")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            logger.warning("Continuing without MongoDB connection.")
    else:
        logger.info("No MONGO_CONNECTION_STRING provided, skipping MongoDB initialization.")
    
    yield
    
    # Shutdown
    if settings.MONGO_CONNECTION_STRING:
        await Database.close_client()
        logger.info("MongoDB connection closed.")


# App
app = FastAPI(
    title="Agent API",
    lifespan=lifespan
)


# Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/invoke", response_model=AgentResponse)
async def invoke_agent(req: AgentRequest):
    """
    Invokes the deep agent and returns structured response.
    
    Args:
        req: AgentRequest with user_prompt
        
    Returns:
        AgentResponse with result and metadata
    """
    response = await asyncio.to_thread(create_agent, req.user_prompt)
    return response


@app.delete("/cache", response_model=ClearCacheResponse)
async def clear_cache():
    """
    Clear all Redis cache.
    
    Examples:
    - DELETE /cache -> clears all cache
    """
    try:
        await clear_all_cache()
        return ClearCacheResponse(
            success=True,
            message="All cache cleared successfully"
        )
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return ClearCacheResponse(
            success=False,
            message=f"Failed to clear cache: {str(e)}"
        )
