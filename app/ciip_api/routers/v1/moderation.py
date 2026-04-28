from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.ciip_api.schemas.moderation import ModerationAction, ModerationQueueItem
from app.ciip_api.schemas.opportunities import OpportunityStatus
from app.controllers import moderation as moderation_controller
from app.controllers import opportunities as opportunities_controller
from app.utils.auth import require_roles
from app.utils.config import get_settings


router = APIRouter(prefix="/moderation", tags=["moderation"])


@router.get(
    "/queue",
    response_model=dict,
    description="""
    Auth: Use Authorization: Bearer <access_token> from Supabase Auth
    Business requirement: Moderators review pending opportunities.
    Frontend note: Use status filter to drive queue tabs.
    """,
)
async def list_queue(
    request: Request,
    status_param: OpportunityStatus = Query(OpportunityStatus.pending, alias="status"),
    limit: int = 20,
    offset: int = 0,
    _user=Depends(require_roles({"admin", "moderator"})),
):
    settings = get_settings()
    async with request.app.state.pool.acquire() as conn:
        total, rows = await moderation_controller.list_queue(
            conn,
            schema=settings.app_schema,
            status=status_param,
            limit=limit,
            offset=offset,
        )
    return {"total": total, "items": [dict(row) for row in rows]}


@router.post(
    "/approve",
    response_model=ModerationQueueItem,
    description="""
    Auth: Use Authorization: Bearer <access_token> from Supabase Auth
    Business requirement: Approve an opportunity submission.
    Frontend note: Use the moderation queue id from /moderation/queue.
    """,
)
async def approve(
    request: Request,
    payload: ModerationAction,
    user=Depends(require_roles({"admin", "moderator"})),
):
    settings = get_settings()
    async with request.app.state.pool.acquire() as conn:
        async with conn.transaction():
            queue_row = await moderation_controller.update_queue_status(
                conn,
                schema=settings.app_schema,
                opportunity_id=str(payload.opportunity_id),
                reviewed_by=user.id,
                status=OpportunityStatus.approved,
                note=payload.note,
            )
            if not queue_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Queue item not found"
                )
            await opportunities_controller.update_opportunity_status(
                conn,
                schema=settings.app_schema,
                opportunity_id=str(payload.opportunity_id),
                status=OpportunityStatus.approved,
            )
    return dict(queue_row)


@router.post(
    "/reject",
    response_model=ModerationQueueItem,
    description="""
    Auth: Use Authorization: Bearer <access_token> from Supabase Auth
    Business requirement: Reject an opportunity submission.
    Frontend note: Provide a note explaining the rejection reason.
    """,
)
async def reject(
    request: Request,
    payload: ModerationAction,
    user=Depends(require_roles({"admin", "moderator"})),
):
    settings = get_settings()
    async with request.app.state.pool.acquire() as conn:
        async with conn.transaction():
            queue_row = await moderation_controller.update_queue_status(
                conn,
                schema=settings.app_schema,
                opportunity_id=str(payload.opportunity_id),
                reviewed_by=user.id,
                status=OpportunityStatus.rejected,
                note=payload.note,
            )
            if not queue_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Queue item not found"
                )
            await opportunities_controller.update_opportunity_status(
                conn,
                schema=settings.app_schema,
                opportunity_id=str(payload.opportunity_id),
                status=OpportunityStatus.rejected,
            )
    return dict(queue_row)
