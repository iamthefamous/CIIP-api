from fastapi import APIRouter, Depends, Request, status

from app.ciip_api.schemas.saved import SavedCreate, SavedList, SavedOpportunity
from app.controllers import saved as saved_controller
from app.utils.auth import get_current_user
from app.utils.config import get_settings


router = APIRouter(prefix="/saved", tags=["saved"])


@router.get(
    "",
    response_model=SavedList,
    description="""
    Auth: Use Authorization: Bearer <access_token> from Supabase Auth
    Business requirement: List saved opportunities for the current user.
    Frontend note: Use for the user's saved tab.
    """,
)
async def list_saved(
    request: Request,
    limit: int = 20,
    offset: int = 0,
    user=Depends(get_current_user),
):
    settings = get_settings()
    async with request.app.state.pool.acquire() as conn:
        total, rows = await saved_controller.list_saved(
            conn,
            schema=settings.app_schema,
            user_id=user.id,
            limit=limit,
            offset=offset,
        )
    return {"total": total, "items": [dict(row) for row in rows]}


@router.post(
    "",
    response_model=SavedOpportunity,
    status_code=status.HTTP_201_CREATED,
    description="""
    Auth: Use Authorization: Bearer <access_token> from Supabase Auth
    Business requirement: Save an opportunity to the user's profile.
    Frontend note: Duplicate saves are ignored.
    """,
)
async def save_opportunity(
    request: Request,
    payload: SavedCreate,
    user=Depends(get_current_user),
):
    settings = get_settings()
    async with request.app.state.pool.acquire() as conn:
        row = await saved_controller.save_opportunity(
            conn,
            schema=settings.app_schema,
            user_id=user.id,
            opportunity_id=str(payload.opportunity_id),
        )
    return dict(row)


@router.delete(
    "/{opportunity_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    description="""
    Auth: Use Authorization: Bearer <access_token> from Supabase Auth
    Business requirement: Remove a saved opportunity.
    Frontend note: Call on unsave toggles.
    """,
)
async def unsave_opportunity(
    request: Request,
    opportunity_id: str,
    user=Depends(get_current_user),
):
    settings = get_settings()
    async with request.app.state.pool.acquire() as conn:
        await saved_controller.unsave_opportunity(
            conn,
            schema=settings.app_schema,
            user_id=user.id,
            opportunity_id=opportunity_id,
        )
    return None
