from typing import Optional

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from api.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    api_key: Optional[str] = Security(api_key_header),
) -> str:
    if api_key is None or api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return api_key
