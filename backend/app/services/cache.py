import json
from typing import Any

import redis


class CacheClient:
    def __init__(self, redis_url: str | None):
        self._memory: dict[str, str] = {}
        self._redis = None
        if redis_url:
            self._redis = redis.from_url(redis_url, decode_responses=True)

    def get(self, key: str) -> Any | None:
        if self._redis:
            value = self._redis.get(key)
            return json.loads(value) if value else None
        value = self._memory.get(key)
        return json.loads(value) if value else None

    def set(self, key: str, value: Any) -> None:
        payload = json.dumps(value, ensure_ascii=False)
        if self._redis:
            self._redis.set(key, payload)
        else:
            self._memory[key] = payload
