from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel
import asyncio

from src.agent.agent_factory import agent_instance
from src import Settings, logger
from src.db.mongo_client import Database


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


app = FastAPI(
    title="Agent API",
    lifespan=lifespan
)


# Request model
class AgentRequest(BaseModel):
    query: str


# Response model
class AgentResponse(BaseModel):
    answer: str


@app.post("/invoke", response_model=AgentResponse)
async def invoke_agent(req: AgentRequest):
    """
    Invokes the deepagents agent asynchronously.
    
    Args:
        req: AgentRequest with query field
        
    Returns:
        AgentResponse with answer field
    """
    # Run the synchronous agent in a thread to avoid blocking
    result = await asyncio.to_thread(agent_instance.run, req.query)
    return AgentResponse(answer=result)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
