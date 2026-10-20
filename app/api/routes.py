from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.errors import PAYLOAD_NOT_FOUND
from app.db.session import get_session
from app.schemas.payload import PayloadCreate, PayloadCreated, PayloadRead
from app.services.payloads import create_payload, get_payload

router = APIRouter()


@router.get("/health/live", tags=["health"])
def liveness() -> dict[str, str]:
    return {"status": "alive"}


@router.get("/health/ready", tags=["health"])
def readiness(session: Session = Depends(get_session)) -> dict[str, str]:
    session.execute(text("SELECT 1"))
    return {"status": "ready"}


@router.post("/payload", response_model=PayloadCreated, status_code=201, tags=["payloads"])
def create(request: PayloadCreate, session: Session = Depends(get_session)) -> PayloadCreated:
    payload, reused = create_payload(session, request)
    return PayloadCreated(id=payload.id, reused=reused)


@router.get("/payload/{payload_id}", response_model=PayloadRead, tags=["payloads"])
def read(payload_id: str, session: Session = Depends(get_session)) -> PayloadRead:
    payload = get_payload(session, payload_id)
    if payload is None:
        raise HTTPException(status_code=PAYLOAD_NOT_FOUND.status_code,
                            detail={"error": PAYLOAD_NOT_FOUND.code, "message": PAYLOAD_NOT_FOUND.message})
    return PayloadRead(output=payload.output)
