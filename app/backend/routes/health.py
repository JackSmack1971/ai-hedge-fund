import asyncio
import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.backend.database import get_db
from app.backend.repositories.api_key_repository import ApiKeyRepository

router = APIRouter()


@router.get("/")
async def root(db: Session = Depends(get_db)):
    repo = ApiKeyRepository(db)
    plaintext_remaining = repo.count_plaintext_keys(include_inactive=True)
    return {"message": "Welcome to AI Hedge Fund API", "plaintext_api_keys_remaining": plaintext_remaining}


@router.get("/ping")
async def ping():
    async def event_generator():
        for i in range(5):
            # Create a JSON object for each ping
            data = {"ping": f"ping {i+1}/5", "timestamp": i + 1}

            # Format as SSE
            yield f"data: {json.dumps(data)}\n\n"

            # Wait 1 second
            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

