import hashlib
import json
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Payload, TransformCache
from app.schemas.payload import PayloadCreate
from app.services.transformer import transform

TRANSFORM_VERSION = "uppercase-v1"


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def create_payload(session: Session, request: PayloadCreate) -> tuple[Payload, bool]:
    canonical = json.dumps(
        [request.list_1, request.list_2], ensure_ascii=False, separators=(",", ":")
    )
    input_hash = _hash(canonical)
    existing = session.scalar(select(Payload).where(Payload.input_hash == input_hash))
    if existing:
        return existing, True

    transformed: list[str] = []
    request_cache: dict[str, str] = {}
    for source in (*request.list_1, *request.list_2):
        source_hash = _hash(source)
        if source_hash in request_cache:
            transformed.append(request_cache[source_hash])
            continue
        cached = session.scalar(
            select(TransformCache).where(
                TransformCache.source_hash == source_hash,
                TransformCache.transform_version == TRANSFORM_VERSION,
            )
        )
        if cached:
            cached.hit_count += 1
            cached.accessed_at = datetime.now(UTC)
            transformed.append(cached.transformed_value)
            request_cache[source_hash] = cached.transformed_value
        else:
            result = transform(source)
            session.add(
                TransformCache(
                    source_hash=source_hash,
                    transform_version=TRANSFORM_VERSION,
                    transformed_value=result,
                )
            )
            transformed.append(result)
            request_cache[source_hash] = result

    output = ", ".join(
        item
        for pair in zip(
            transformed[: len(request.list_1)],
            transformed[len(request.list_1) :],
            strict=True,
        )
        for item in pair
    )
    payload = Payload(id=uuid.uuid4().hex, input_hash=input_hash, output=output)
    session.add(payload)
    session.commit()
    session.refresh(payload)

    return payload, False


def get_payload(session: Session, payload_id: str) -> Payload | None:
    return session.get(Payload, payload_id)


def cleanup_expired_transforms(session: Session) -> int:
    ttl = get_settings().cache_ttl_seconds
    if not ttl:
        return 0
    cutoff = datetime.now(UTC) - timedelta(seconds=ttl)
    deleted = session.query(TransformCache).filter(TransformCache.accessed_at < cutoff).delete()
    session.commit()
    return deleted
