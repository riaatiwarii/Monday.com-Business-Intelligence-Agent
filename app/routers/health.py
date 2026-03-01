from fastapi import APIRouter

from app.config import settings
from app.models import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        app_env=settings.app_env,
        monday_configured=bool(settings.monday_api_token and settings.monday_deals_board_id and settings.monday_work_orders_board_id),
        openai_configured=bool(settings.openai_api_key),
    )
