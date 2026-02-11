"""
State management with Redis for workflow coordination.
"""

import json
import os
import sys
from functools import lru_cache
from typing import Any, Dict, List, Optional

import redis.asyncio as redis
try:
    from loguru import logger
except Exception:  # pragma: no cover - fallback to stdlib logging
    import logging as _logging

    class _FallbackLogger:
        def info(self, *a, **k):
            _logging.getLogger("state_manager").info(*a, **k)

        def warning(self, *a, **k):
            _logging.getLogger("state_manager").warning(*a, **k)

        def error(self, *a, **k):
            _logging.getLogger("state_manager").error(*a, **k)

        def debug(self, *a, **k):
            _logging.getLogger("state_manager").debug(*a, **k)

    logger = _FallbackLogger()

from src.core.config import get_settings
from src.models.workflow_state import WorkflowState, Task, TaskResult


class StateManager:
    """Manages workflow state using Redis."""

    def __init__(self, redis_url: Optional[str] = None):
        """Initialize state manager."""
        self.settings = get_settings()
        self.redis_url = redis_url or self.settings.redis_url
        self._client: Optional[redis.Redis] = None
        self._pubsub: Optional[redis.client.PubSub] = None

    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self._client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            logger.info("Connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._client:
            await self._client.close()
            logger.info("Disconnected from Redis")

    async def ping(self) -> bool:
        """Check Redis connection."""
        try:
            if self._client:
                return await self._client.ping()
            return False
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False

    # Workflow State Management

    async def save_workflow_state(self, state: WorkflowState) -> bool:
        """Save workflow state to Redis."""
        try:
            if not self._client:
                logger.warning("Redis client not connected, skipping state save")
                return False
            key = f"workflow:{state.request_id}"
            value = state.model_dump_json()
            await self._client.set(key, value)
            await self._client.expire(key, 86400)  # 24 hours TTL
            logger.debug(f"Saved workflow state: {state.request_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save workflow state: {e}")
            return False

    async def save_workflow(self, workflow_id: str, state_dict: dict) -> bool:
        """Backward compatibility wrapper for save_workflow."""
        try:
            if not self._client:
                logger.warning("Redis client not connected, skipping workflow save")
                return False
            key = f"workflow:{workflow_id}"
            value = json.dumps(state_dict)
            await self._client.set(key, value)
            await self._client.expire(key, 86400)
            logger.debug(f"Saved workflow: {workflow_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save workflow: {e}")
            return False

    async def get_workflow_state(self, request_id: str) -> Optional[WorkflowState]:
        """Get workflow state from Redis."""
        try:
            key = f"workflow:{request_id}"
            value = await self._client.get(key)
            if value:
                return WorkflowState.model_validate_json(value)
            return None
        except Exception as e:
            logger.error(f"Failed to get workflow state: {e}")
            return None

    # Backwards-compatible wrapper expected by some tests
    async def get_workflow(self, workflow_id: str) -> Optional[dict]:
        """Backward-compatible getter returning raw workflow dict if present."""
        try:
            key = f"workflow:{workflow_id}"
            value = await self._client.get(key)
            if value:
                try:
                    return json.loads(value)
                except Exception:
                    return value
            return None
        except Exception as e:
            logger.error(f"Failed to get workflow: {e}")
            return None

    async def delete_workflow_state(self, request_id: str) -> bool:
        """Delete workflow state from Redis."""
        try:
            key = f"workflow:{request_id}"
            await self._client.delete(key)
            logger.debug(f"Deleted workflow state: {request_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete workflow state: {e}")
            return False

    # Backwards-compatible wrapper
    async def delete_workflow(self, workflow_id: str) -> bool:
        try:
            key = f"workflow:{workflow_id}"
            await self._client.delete(key)
            logger.debug(f"Deleted workflow: {workflow_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete workflow: {e}")
            return False

    async def list_workflows(self) -> List[str]:
        """List all workflow IDs."""
        try:
            keys = []
            async for key in self._client.scan_iter("workflow:*"):
                workflow_id = key.replace("workflow:", "")
                keys.append(workflow_id)
            return keys
        except Exception as e:
            logger.error(f"Failed to list workflows: {e}")
            return []

    # Task Management

    async def save_task(self, task: Task) -> bool:
        """Save task to Redis."""
        try:
            key = f"task:{task.task_id}"
            value = task.model_dump_json()
            await self._client.set(key, value)
            await self._client.expire(key, 86400)
            return True
        except Exception as e:
            logger.error(f"Failed to save task: {e}")
            return False

    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get task from Redis."""
        try:
            key = f"task:{task_id}"
            value = await self._client.get(key)
            if value:
                return Task.model_validate_json(value)
            return None
        except Exception as e:
            logger.error(f"Failed to get task: {e}")
            return None

    async def save_task_result(self, result: TaskResult) -> bool:
        """Save task result to Redis."""
        try:
            key = f"task_result:{result.task_id}"
            value = result.model_dump_json()
            await self._client.set(key, value)
            await self._client.expire(key, 86400)
            return True
        except Exception as e:
            logger.error(f"Failed to save task result: {e}")
            return False

    async def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """Get task result from Redis."""
        try:
            key = f"task_result:{task_id}"
            value = await self._client.get(key)
            if value:
                return TaskResult.model_validate_json(value)
            return None
        except Exception as e:
            logger.error(f"Failed to get task result: {e}")
            return None

    # Shared Context and Data

    async def set_shared_data(
        self, request_id: str, key: str, value: Any, ttl: int = 86400
    ) -> bool:
        """Set shared data for a workflow."""
        try:
            if not self._client:
                logger.warning("Redis client not connected, skipping shared data save")
                return False
            redis_key = f"shared:{request_id}:{key}"
            if isinstance(value, (dict, list)):
                # Use a JSON serializer that safely converts datetimes to strings
                value = json.dumps(value, default=str)
            await self._client.set(redis_key, value)
            await self._client.expire(redis_key, ttl)
            return True
        except Exception as e:
            logger.error(f"Failed to set shared data: {e}")
            return False

    async def get_shared_data(self, request_id: str, key: str) -> Optional[Any]:
        """Get shared data for a workflow."""
        try:
            redis_key = f"shared:{request_id}:{key}"
            value = await self._client.get(redis_key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            logger.error(f"Failed to get shared data: {e}")
            return None

    async def delete_shared_data(self, request_id: str, key: str) -> bool:
        """Delete shared data for a workflow."""
        try:
            redis_key = f"shared:{request_id}:{key}"
            await self._client.delete(redis_key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete shared data: {e}")
            return False

    # Pub/Sub for Agent Communication

    async def publish_message(self, channel: str, message: Dict[str, Any]) -> bool:
        """Publish message to a channel."""
        try:
            await self._client.publish(channel, json.dumps(message))
            logger.debug(f"Published message to channel: {channel}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            return False

    async def subscribe(self, *channels: str) -> redis.client.PubSub:
        """Subscribe to channels."""
        try:
            pubsub = self._client.pubsub()
            await pubsub.subscribe(*channels)
            logger.debug(f"Subscribed to channels: {channels}")
            return pubsub
        except Exception as e:
            logger.error(f"Failed to subscribe to channels: {e}")
            raise

    async def unsubscribe(self, pubsub: redis.client.PubSub, *channels: str) -> None:
        """Unsubscribe from channels."""
        try:
            await pubsub.unsubscribe(*channels)
            await pubsub.close()
            logger.debug(f"Unsubscribed from channels: {channels}")
        except Exception as e:
            logger.error(f"Failed to unsubscribe: {e}")

    # Caching

    async def cache_set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set cache value."""
        try:
            cache_key = f"cache:{key}"
            if isinstance(value, (dict, list)):
                # Serialize with default=str to handle datetimes and other non-serializable types
                value = json.dumps(value, default=str)
            await self._client.set(cache_key, value)
            await self._client.expire(cache_key, ttl)
            return True
        except Exception as e:
            logger.error(f"Failed to set cache: {e}")
            return False

    async def cache_get(self, key: str) -> Optional[Any]:
        """Get cache value."""
        try:
            cache_key = f"cache:{key}"
            value = await self._client.get(cache_key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            logger.error(f"Failed to get cache: {e}")
            return None

    async def cache_delete(self, key: str) -> bool:
        """Delete cache value."""
        try:
            cache_key = f"cache:{key}"
            await self._client.delete(cache_key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete cache: {e}")
            return False

    async def cache_clear_pattern(self, pattern: str) -> int:
        """Clear all cache keys matching pattern."""
        try:
            count = 0
            async for key in self._client.scan_iter(f"cache:{pattern}"):
                await self._client.delete(key)
                count += 1
            logger.debug(f"Cleared {count} cache keys matching pattern: {pattern}")
            return count
        except Exception as e:
            logger.error(f"Failed to clear cache pattern: {e}")
            return 0

    # Rate Limiting

    async def check_rate_limit(
        self, key: str, limit: int, window: int = 60
    ) -> tuple[bool, int]:
        """
        Check rate limit for a key.

        Args:
            key: Rate limit key
            limit: Maximum requests allowed
            window: Time window in seconds

        Returns:
            Tuple of (allowed, remaining)
        """
        # Implementation below uses Redis. For tests we provide an in-memory manager
        # via `get_state_manager()` which will return `InMemoryStateManager` when
        # `USE_INMEMORY_STATE=1` is set in the environment.
        try:
            rate_key = f"ratelimit:{key}"
            current = await self._client.get(rate_key)

            if current is None:
                await self._client.set(rate_key, 1)
                await self._client.expire(rate_key, window)
                return True, limit - 1

            current_count = int(current)
            if current_count >= limit:
                return False, 0

            await self._client.incr(rate_key)
            return True, limit - current_count - 1

        except Exception as e:
            logger.error(f"Failed to check rate limit: {e}")
            return True, limit  # Fail open

    # Lock Management for Distributed Operations

    async def acquire_lock(self, lock_name: str, timeout: int = 10) -> bool:
        """Acquire a distributed lock."""
        try:
            lock_key = f"lock:{lock_name}"
            result = await self._client.set(lock_key, "1", nx=True, ex=timeout)
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to acquire lock: {e}")
            return False

    async def release_lock(self, lock_name: str) -> bool:
        """Release a distributed lock."""
        try:
            lock_key = f"lock:{lock_name}"
            await self._client.delete(lock_key)
            return True
        except Exception as e:
            logger.error(f"Failed to release lock: {e}")
            return False

    # Health Check

    async def health_check(self) -> Dict[str, Any]:
        """Get Redis health status."""
        try:
            info = await self._client.info()
            return {
                "connected": True,
                "version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "uptime_days": info.get("uptime_in_days"),
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"connected": False, "error": str(e)}


@lru_cache()
def get_state_manager() -> StateManager:
    """Get cached state manager instance."""
    use_inmemory = os.environ.get("USE_INMEMORY_STATE", "0") == "1"
    if use_inmemory:
        return InMemoryStateManager()
    # When running tests under pytest without the env var, prefer in-memory as well
    if "PYTEST_CURRENT_TEST" in os.environ or any("pytest" in p for p in sys.argv):
        return InMemoryStateManager()
    return StateManager()


class InMemoryStateManager(StateManager):
    """A lightweight in-memory StateManager used for tests and mock runs.

    Implements the same public methods as `StateManager` but stores data in-memory.
    This avoids requiring a local Redis instance during unit/E2E mock tests.
    """

    def __init__(self) -> None:
        self._store: dict = {}
        self._pubsubs: dict = {}
        self.settings = get_settings()

    async def connect(self) -> None:
        # No-op for in-memory
        return None

    async def disconnect(self) -> None:
        # No-op for in-memory
        self._store.clear()
        return None

    async def ping(self) -> bool:
        return True

    async def save_workflow_state(self, state: WorkflowState) -> bool:
        try:
            self._store[f"workflow:{state.request_id}"] = state.model_dump()
            return True
        except Exception:
            return False

    async def save_workflow(self, workflow_id: str, state_dict: dict) -> bool:
        try:
            self._store[f"workflow:{workflow_id}"] = state_dict
            return True
        except Exception:
            return False

    async def get_workflow_state(self, request_id: str) -> Optional[WorkflowState]:
        try:
            v = self._store.get(f"workflow:{request_id}")
            if v is None:
                return None
            # If already a WorkflowState-compatible dict, attempt validation
            if isinstance(v, dict):
                return WorkflowState.model_validate(v)
            return WorkflowState.model_validate_json(v)
        except Exception:
            return None

    async def get_workflow(self, workflow_id: str) -> Optional[dict]:
        v = self._store.get(f"workflow:{workflow_id}")
        if v is None:
            return None
        if isinstance(v, dict):
            return v
        try:
            return json.loads(v)
        except Exception:
            return v

    async def delete_workflow_state(self, request_id: str) -> bool:
        self._store.pop(f"workflow:{request_id}", None)
        return True

    async def delete_workflow(self, workflow_id: str) -> bool:
        self._store.pop(f"workflow:{workflow_id}", None)
        return True

    async def list_workflows(self) -> List[str]:
        return [k.replace("workflow:", "") for k in self._store.keys() if k.startswith("workflow:")]

    async def save_task(self, task: Task) -> bool:
        try:
            self._store[f"task:{task.task_id}"] = task.model_dump()
            return True
        except Exception:
            return False

    async def get_task(self, task_id: str) -> Optional[Task]:
        v = self._store.get(f"task:{task_id}")
        if v is None:
            return None
        try:
            return Task.model_validate(v)
        except Exception:
            return None

    async def save_task_result(self, result: TaskResult) -> bool:
        try:
            self._store[f"task_result:{result.task_id}"] = result.model_dump()
            return True
        except Exception:
            return False

    async def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        v = self._store.get(f"task_result:{task_id}")
        if v is None:
            return None
        try:
            return TaskResult.model_validate(v)
        except Exception:
            return None

    async def set_shared_data(self, request_id: str, key: str, value: Any, ttl: int = 86400) -> bool:
        try:
            self._store[f"shared:{request_id}:{key}"] = value
            return True
        except Exception:
            return False

    async def get_shared_data(self, request_id: str, key: str) -> Optional[Any]:
        return self._store.get(f"shared:{request_id}:{key}")

    async def delete_shared_data(self, request_id: str, key: str) -> bool:
        self._store.pop(f"shared:{request_id}:{key}", None)
        return True

    async def publish_message(self, channel: str, message: Dict[str, Any]) -> bool:
        # No real pubsub; store last message per channel
        self._store[f"pubsub:{channel}"] = message
        return True

    async def cache_set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        self._store[f"cache:{key}"] = value
        return True

    async def cache_get(self, key: str) -> Optional[Any]:
        return self._store.get(f"cache:{key}")

    async def cache_delete(self, key: str) -> bool:
        self._store.pop(f"cache:{key}", None)
        return True

    async def cache_clear_pattern(self, pattern: str) -> int:
        keys = [k for k in self._store.keys() if k.startswith(f"cache:{pattern}")]
        for k in keys:
            self._store.pop(k, None)
        return len(keys)

    async def check_rate_limit(self, key: str, limit: int, window: int = 60) -> tuple[bool, int]:
        return True, limit

    async def acquire_lock(self, lock_name: str, timeout: int = 10) -> bool:
        lock_key = f"lock:{lock_name}"
        if self._store.get(lock_key):
            return False
        self._store[lock_key] = True
        return True

    async def release_lock(self, lock_name: str) -> bool:
        self._store.pop(f"lock:{lock_name}", None)
        return True

    async def health_check(self) -> Dict[str, Any]:
        return {"connected": True, "backend": "inmemory"}
