import certifi
from functools import wraps
from typing import Any, Callable, Optional, TypeVar, cast
from urllib.parse import quote_plus

from pymongo import MongoClient
from pymongo.server_api import ServerApi
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from src import logger

T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])


def handle_db_errors(default_return: T) -> Callable[[F], F]:
    """
    Decorator to handle database errors consistently.

    Returns default_return if any exception occurs.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Database error in {func.__name__}: {e}")
                return default_return

        return cast(F, wrapper)

    return decorator


def encode_mongo_password(password: str) -> str:
    """Encode MongoDB password for URI usage."""
    return quote_plus(password)


def should_enable_tls(mongo_uri: str) -> bool:
    """Determine if TLS should be enabled based on URI or environment."""
    import os

    if os.getenv("APP_ENV", "").lower() == "local":
        return False
    if ".svc.cluster.local" in mongo_uri:
        return False
    if mongo_uri.startswith("mongodb+srv://"):
        return True
    if "ssl=false" in mongo_uri or "tls=false" in mongo_uri:
        return False
    return True


def create_mongo_client(mongo_uri: str, timeout: int = 60000) -> MongoClient:
    """Creates a MongoDB client with TLS and sensible defaults."""
    enable_tls = should_enable_tls(mongo_uri)

    client_args: dict[str, Any] = {
        "server_api": ServerApi("1"),
        "serverSelectionTimeoutMS": timeout,
        "connectTimeoutMS": timeout,
        "socketTimeoutMS": timeout,
        "retryWrites": True,
        "maxPoolSize": 50,
        "minPoolSize": 5,
        "waitQueueTimeoutMS": 10000,
        "maxIdleTimeMS": 300000,
        "uuidRepresentation": "standard",
    }

    if enable_tls:
        client_args["tlsCAFile"] = certifi.where()

    return MongoClient(mongo_uri, **client_args)


class Database:
    """
    Singleton MongoDB connection handler with sync and async support.

    Usage:
        # Initialize once at startup
        Database.init_client(mongo_uri)

        # Sync access
        db = Database.get_database("my_db")

        # Async access (for session management, etc.)
        db = Database.get_async_database("my_db")

        # Close at shutdown
        Database.close_client()
    """

    _client: Optional[MongoClient] = None
    _async_client: Optional[AsyncIOMotorClient] = None
    _mongo_uri: Optional[str] = None

    @classmethod
    def init_client(cls, mongo_uri: str) -> None:
        """Initialize both sync and async MongoDB clients."""
        cls._mongo_uri = mongo_uri
        if cls._client is None:
            cls._client = create_mongo_client(mongo_uri)
        if cls._async_client is None:
            cls._async_client = AsyncIOMotorClient(mongo_uri)
        logger.info("MongoDB clients initialized")

    @classmethod
    def client(cls) -> MongoClient:
        """Get the sync MongoDB client."""
        if cls._client is None:
            raise RuntimeError("MongoDB client not initialized. Call init_client() first.")
        return cls._client

    @classmethod
    def async_client(cls) -> AsyncIOMotorClient:
        """Get the async MongoDB client."""
        if cls._async_client is None:
            raise RuntimeError("MongoDB client not initialized. Call init_client() first.")
        return cls._async_client

    @classmethod
    def get_database(cls, db_name: str):
        """Get a sync MongoDB database."""
        if cls._client is None:
            raise RuntimeError("MongoDB client not initialized. Call init_client() first.")
        return cls._client[db_name]

    @classmethod
    def get_async_database(cls, db_name: str) -> AsyncIOMotorDatabase:
        """Get an async MongoDB database."""
        if cls._async_client is None:
            raise RuntimeError("MongoDB client not initialized. Call init_client() first.")
        return cls._async_client[db_name]

    @classmethod
    def get_collection(cls, collection_name: str, db_name: str):
        """Get a sync MongoDB collection."""
        return cls.get_database(db_name)[collection_name]

    @classmethod
    async def close_client(cls):
        """Close both MongoDB clients."""
        if cls._client:
            cls._client.close()
            cls._client = None
        if cls._async_client:
            cls._async_client.close()
            cls._async_client = None
        logger.info("MongoDB clients closed")
