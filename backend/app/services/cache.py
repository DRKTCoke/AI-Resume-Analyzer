import json
import time
from threading import Lock
from typing import Any

import redis


class CacheClient:
    def __init__(self, redis_url: str | None):
        self._memory: dict[str, str] = {}
        self._memory_expires_at: dict[str, float] = {}
        self._lock = Lock()
        self._redis = None
        if redis_url:
            self._redis = redis.from_url(redis_url, decode_responses=True)

    def get(self, key: str) -> Any | None:
        if self._redis:
            value = self._redis.get(key)
            return json.loads(value) if value else None
        with self._lock:
            value = self._get_memory_value(key)
        return json.loads(value) if value else None

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        payload = json.dumps(value, ensure_ascii=False)
        if self._redis:
            self._redis.set(key, payload, ex=ttl_seconds)
        else:
            with self._lock:
                self._memory[key] = payload
                if ttl_seconds:
                    self._memory_expires_at[key] = time.time() + ttl_seconds
                else:
                    self._memory_expires_at.pop(key, None)

    def set_if_absent(self, key: str, value: Any, ttl_seconds: int | None = None) -> bool:
        payload = json.dumps(value, ensure_ascii=False)
        if self._redis:
            return bool(self._redis.set(key, payload, nx=True, ex=ttl_seconds))

        with self._lock:
            if self._get_memory_value(key) is not None:
                return False
            self._memory[key] = payload
            if ttl_seconds:
                self._memory_expires_at[key] = time.time() + ttl_seconds
            else:
                self._memory_expires_at.pop(key, None)
            return True

    def delete(self, key: str) -> None:
        if self._redis:
            self._redis.delete(key)
            return

        with self._lock:
            self._memory.pop(key, None)
            self._memory_expires_at.pop(key, None)

    def health(self) -> dict[str, str]:
        if not self._redis:
            return {"backend": "memory", "status": "ok"}

        try:
            self._redis.ping()
        except redis.RedisError:
            return {"backend": "redis", "status": "unavailable"}
        return {"backend": "redis", "status": "ok"}

    def _get_memory_value(self, key: str) -> str | None:
        expires_at = self._memory_expires_at.get(key)
        if expires_at and expires_at <= time.time():
            self._memory.pop(key, None)
            self._memory_expires_at.pop(key, None)
            return None
        return self._memory.get(key)
