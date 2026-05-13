import hashlib
import json
from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException

from app.services.cache import CacheClient


PROCESSING = "processing"
COMPLETED = "completed"


@dataclass(frozen=True)
class IdempotencyState:
    cache_key: str | None
    response: dict[str, Any] | None = None

    @property
    def should_replay(self) -> bool:
        return self.response is not None


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def content_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def normalize_idempotency_key(key: str | None, max_length: int) -> str | None:
    if key is None:
        return None

    normalized = key.strip()
    if not normalized:
        return None
    if len(normalized) > max_length:
        raise HTTPException(status_code=400, detail="Idempotency-Key is too long")
    return normalized


class IdempotencyController:
    def __init__(self, cache: CacheClient, ttl_seconds: int):
        self._cache = cache
        self._ttl_seconds = ttl_seconds

    def begin(self, namespace: str, key: str | None, request_hash: str) -> IdempotencyState:
        if not key:
            return IdempotencyState(cache_key=None)

        cache_key = self._cache_key(namespace, key)
        record = self._cache.get(cache_key)
        if record:
            return self._resolve_existing(record, cache_key, request_hash)

        created = self._cache.set_if_absent(
            cache_key,
            {"status": PROCESSING, "request_hash": request_hash},
            ttl_seconds=self._ttl_seconds,
        )
        if not created:
            record = self._cache.get(cache_key)
            if record:
                return self._resolve_existing(record, cache_key, request_hash)

        return IdempotencyState(cache_key=cache_key)

    def finish(self, state: IdempotencyState, request_hash: str, response: dict[str, Any]) -> None:
        if not state.cache_key:
            return

        self._cache.set(
            state.cache_key,
            {"status": COMPLETED, "request_hash": request_hash, "response": response},
            ttl_seconds=self._ttl_seconds,
        )

    def abort(self, state: IdempotencyState) -> None:
        if state.cache_key and not state.should_replay:
            self._cache.delete(state.cache_key)

    def _resolve_existing(
        self,
        record: dict[str, Any],
        cache_key: str,
        request_hash: str,
    ) -> IdempotencyState:
        if record.get("request_hash") != request_hash:
            raise HTTPException(
                status_code=409,
                detail="Idempotency-Key was already used for a different request",
            )

        if record.get("status") == COMPLETED:
            return IdempotencyState(cache_key=cache_key, response=record.get("response"))

        raise HTTPException(status_code=409, detail="Request with this Idempotency-Key is still processing")

    @staticmethod
    def _cache_key(namespace: str, key: str) -> str:
        key_hash = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return f"idempotency:{namespace}:{key_hash}"
