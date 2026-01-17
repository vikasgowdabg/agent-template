import os
import json
import asyncio
from datetime import datetime, date
from typing import Any, Optional
from functools import wraps
from redis.asyncio import Redis, RedisError
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from bson import ObjectId
from fastapi import Request

from src.utils.logger import logger


class Cache:
    _instance = None
    _cache_client = None
    _cache_client_unavailable = False
    _init_lock = asyncio.Lock()  # Prevent concurrent initialization

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Cache, cls).__new__(cls)
            cls._cache_client_unavailable = False
        return cls._instance

    @classmethod
    async def _initialize_redis(cls):
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = os.getenv("REDIS_PORT", 6379)
        redis_password = os.getenv("REDIS_PASSWORD", "")
        redis_db = os.getenv("REDIS_DB", 0)
        if redis_password:
            redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}/{redis_db}"
        else:
            redis_url = f"redis://{redis_host}:{redis_port}/{redis_db}"
        try:
            # Setting socket timeouts and connection pool for concurrent access
            cache_client = Redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=False,
                socket_timeout=10,
                socket_connect_timeout=5,
                max_connections=50,
                socket_keepalive=True,
                socket_keepalive_options={},
            )
            pong = await cache_client.ping()
            if pong:
                logger.info(f"Connected to Redis Host {redis_host}.")
                cls._cache_client = cache_client
            else:
                logger.warning(f"Failed to connect to Redis Host {redis_host}.")
                cls._cache_client = None
                cls._cache_client_unavailable = True
        except (RedisError, TimeoutError, ConnectionError) as e:
            cls._cache_client_unavailable = True
            cls._cache_client = None
            logger.error(f"Error initializing Redis client for Redis Host {redis_host}: {e}")

    @classmethod
    async def get_redis(cls) -> Optional[Redis]:
        if cls._cache_client_unavailable:
            return None
        if not cls._cache_client:
            async with cls._init_lock:
                if not cls._cache_client and not cls._cache_client_unavailable:
                    await cls._initialize_redis()
        return cls._cache_client

    @classmethod
    def get_cache_backend(cls) -> Optional[RedisBackend]:
        cache_client = cls._cache_client
        if cache_client:
            return CustomRedisBackend(cache_client)
        else:
            logger.warning("Redis client is not available. Cannot return cache backend.")
            return None


def custom_key_builder(func, namespace: str, request: Request, *args, **kwargs):
    path = request.url.path
    params = ":".join([f"{k}:{v}" for k, v in request.query_params.items()])
    return f"{namespace}:{path}:{params}"


def generate_cache_key(func, args, kwargs, skip_args=None, skip_kwargs=None, prefix="cache"):
    """
    Generate cache key by skipping specified args and kwargs.

    Args:
        func: Function object
        args: Positional arguments
        kwargs: Keyword arguments
        skip_args: Positional argument indexes to skip
        skip_kwargs: Keyword argument keys to skip
        prefix: Cache key prefix (default: "cache")

    Returns:
        Cache key string
    """
    skip_args = skip_args or []
    skip_kwargs = skip_kwargs or []

    filtered_args = [str(arg) for i, arg in enumerate(args) if i not in skip_args]
    filtered_kwargs = {k: v for k, v in kwargs.items() if k not in skip_kwargs}

    cache_key = (
        f"{prefix}:{func.__name__}:"
        f"{':'.join(filtered_args)}:"
        f"{':'.join([f'{k}:{v}' for k, v in filtered_kwargs.items()])}"
    )
    return cache_key


def serialize_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, date):
        return obj.isoformat()
    raise TypeError(f"Type {obj.__class__.__name__} not serializable")


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


def deserialize_datetime(obj):
    if isinstance(obj, str):
        try:
            return datetime.fromisoformat(obj)
        except ValueError:
            return obj
    return obj


async def set_cache(key: str, value: Any, ttl: int | None = None):
    if not ttl:
        logger.error(f"TTL not provided for key {key}.")
    cache_client = await Cache.get_redis()
    if not cache_client:
        logger.warning(f"Redis client is not available, cannot set cache for key {key}.")
        return
    try:
        serialized_value = json.dumps(value, default=serialize_datetime)
        await cache_client.set(key, serialized_value, ex=ttl)
    except (TypeError, TimeoutError, ConnectionError) as e:
        logger.warning(f"Error in setting cache for key {key}: {e}")
    except RedisError as e:
        logger.warning(f"Redis error in setting cache for key {key}: {e}")


async def get_cache(key: str) -> Any:
    cache_client = await Cache.get_redis()
    if not cache_client:
        logger.warning(f"Redis client is not available, cannot get cache for key {key}.")
        return None

    try:
        serialized_value = await cache_client.get(key)
        if serialized_value:
            return json.loads(serialized_value, object_hook=deserialize_datetime)
        return None
    except (TimeoutError, ConnectionError) as e:
        logger.warning(f"Redis connection timeout or error getting cache for key {key}: {e}")
        return None
    except RedisError as e:
        logger.warning(f"Redis error getting cache for key {key}: {e}")
        return None


def unified_safe_cache(expire: int = 60, prefix: str = "cache"):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = generate_cache_key(func, args, kwargs, prefix=prefix)
            cached_result = None
            try:
                cached_result = await get_cache(cache_key)
            except Exception as e:
                logger.warning(f"Error retrieving cache for key {cache_key}: {e}")

            if cached_result is not None:
                return cached_result

            result = await func(*args, **kwargs)

            if not _is_empty_data(result):
                try:
                    await set_cache(cache_key, result, expire)
                except Exception as e:
                    logger.warning(f"Error setting cache for key {cache_key}: {e}")
            else:
                logger.debug(f"Skipping cache for key {cache_key} - result is empty")

            return result

        return wrapper

    return decorator


def _is_empty_data(data: Any) -> bool:
    """
    Check if data is considered empty.

    Args:
        data: The data to check

    Returns:
        True if data is empty (empty list, dict, None, empty string), False otherwise
    """
    if data is None:
        return True
    if isinstance(data, (list, dict, str)):
        return len(data) == 0
    return False


class CustomRedisBackend(RedisBackend):
    def __init__(self, client: Redis):
        super().__init__(client)
        self.client = client

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        serialized_value = json.dumps(value, default=serialize_datetime)
        await self.client.set(key, serialized_value, ex=ttl)

    async def get(self, key: str) -> Optional[Any]:
        serialized_value = await self.client.get(key)
        if serialized_value:
            return json.loads(serialized_value, object_hook=deserialize_datetime)
        return None


async def init_cache(prefix: str = "cache"):
    try:
        cache_client_instance = Cache()
        cache_client = await cache_client_instance.get_redis()
        if not cache_client:
            logger.warning("Redis client is not available, cannot initialize cache.")
            return
        backend = Cache.get_cache_backend()
        FastAPICache.init(backend, prefix=prefix, key_builder=custom_key_builder)
    except RedisError as e:
        logger.warning(f"Error initializing FastAPI cache: {e}")
        raise


async def clear_cache_by_pattern(pattern: str, prefix: str = "cache"):
    cache_client = await Cache.get_redis()
    if not cache_client:
        logger.warning("Redis client is not available, cannot clear cache.")
        return

    await clear_pattern(cache_client, pattern, prefix)


async def clear_pattern(cache_client: Redis, pattern: str, prefix: str = "cache"):
    cursor = 0
    pattern = f"{prefix}*{pattern}*"
    logger.debug(f"Clearing cache with pattern: {pattern}")
    try:
        async with cache_client.pipeline() as pipe:
            while True:
                cursor, keys = await cache_client.scan(cursor=cursor, match=pattern)
                if keys:
                    for key in keys:
                        pipe.delete(key)
                    await pipe.execute()
                if cursor == 0:
                    break
    except (TimeoutError, ConnectionError) as e:
        logger.warning(f"Redis timeout or connection error scanning and deleting keys: {e}")
    except RedisError as e:
        logger.warning(f"Redis error scanning and deleting keys: {e}")
        raise


async def clear_all_cache():
    cache_client = await Cache.get_redis()
    if not cache_client:
        logger.warning("Redis client is not available, cannot clear all cache.")
        return

    await clear_cache_by_pattern("*")
