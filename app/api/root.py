from fastapi import APIRouter

router = APIRouter(
    tags=["status"],
)


@router.get("/health", status_code=200)
async def health():
    """Check if the service is healthy"""
    return "OK"

