from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.ciip_api.schemas.opportunities import (
    OpportunityCreate,
    OpportunityList,
    OpportunityOut,
    OpportunityStatus,
    OpportunityType,
)
from app.ciip_api.schemas.users import AudienceType
from app.controllers import opportunities as opportunities_controller
from app.services.ai_service import AIService
from app.utils.auth import get_current_user, require_roles
from app.utils.config import get_settings


router = APIRouter(prefix="/opportunities", tags=["opportunities"])


@router.get(
    "",
    response_model=OpportunityList,
    description="""
    Auth: Use Authorization: Bearer <access_token> from Supabase Auth
    Business requirement: List approved opportunities with filtering and pagination.
    Frontend note: Combine audience, category, and type filters in one request.
    """,
)
async def list_opportunities(
    request: Request,
    status_param: Optional[OpportunityStatus] = Query(None, alias="status"),
    opportunity_type: Optional[OpportunityType] = Query(None),
    category_id: Optional[str] = Query(None),
    audience: Optional[list[AudienceType]] = Query(None),
    limit: int = 20,
    offset: int = 0,
    user=Depends(get_current_user),
):
    settings = get_settings()
    allowed_status = status_param
    if allowed_status is None:
        allowed_status = OpportunityStatus.approved
    elif user.role not in {"admin", "moderator"}:
        allowed_status = OpportunityStatus.approved

    async with request.app.state.pool.acquire() as conn:
        total, rows = await opportunities_controller.list_opportunities(
            conn,
            schema=settings.app_schema,
            status=allowed_status,
            limit=limit,
            offset=offset,
            opportunity_type=opportunity_type,
            category_id=category_id,
            audiences=audience,
        )
    return {"total": total, "items": [dict(row) for row in rows]}


@router.get(
    "/{opportunity_id}",
    response_model=OpportunityOut,
    description="""
    Auth: Use Authorization: Bearer <access_token> from Supabase Auth
    Business requirement: Fetch a single opportunity by id.
    Frontend note: Use this for detail pages.
    """,
)
async def get_opportunity(
    request: Request, opportunity_id: str, _user=Depends(get_current_user)
):
    settings = get_settings()
    async with request.app.state.pool.acquire() as conn:
        row = await opportunities_controller.get_opportunity(
            conn, schema=settings.app_schema, opportunity_id=opportunity_id
        )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")
    return dict(row)


@router.post(
    "",
    response_model=OpportunityOut,
    status_code=status.HTTP_201_CREATED,
    description="""
    Auth: Use Authorization: Bearer <access_token> from Supabase Auth
    Business requirement: Institutions submit opportunities for moderation.
    Frontend note: Newly created items enter the moderation queue.
    """,
)
async def create_opportunity(
    request: Request,
    payload: OpportunityCreate,
    user=Depends(require_roles({"institution", "admin"})),
):
    settings = get_settings()
    ai_tags = None
    ai_summary = None
    if payload.generate_ai:
        ai_service = AIService(settings)
        ai_summary, ai_tags = await ai_service.generate_summary_and_tags(
            f"{payload.title}\n\n{payload.description}"
        )

    async with request.app.state.pool.acquire() as conn:
        row = await opportunities_controller.create_opportunity(
            conn,
            schema=settings.app_schema,
            title=payload.title,
            description=payload.description,
            opportunity_type=payload.opportunity_type,
            category_id=str(payload.category_id),
            institution_id=str(payload.institution_id),
            submitted_by=user.id,
            status=OpportunityStatus.pending,
            deadline=payload.deadline,
            location=payload.location,
            url=payload.url,
            audiences=payload.audiences,
            ai_tags=ai_tags,
            ai_summary=ai_summary,
        )
    return dict(row)
