from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.ciip_api.schemas.institutions import InstitutionCreate, InstitutionOut
from app.controllers import institutions as institutions_controller
from app.utils.auth import get_current_user, require_roles
from app.utils.config import get_settings


router = APIRouter(prefix="/institutions", tags=["institutions"])


@router.get(
    "",
    response_model=dict,
    description="""
    Auth: Use Authorization: Bearer <access_token> from Supabase Auth
    Business requirement: List verified institutions for partner visibility.
    Frontend note: Paginate results for directory views.
    """,
)
async def list_institutions(
    request: Request,
    limit: int = 20,
    offset: int = 0,
    _user=Depends(get_current_user),
):
    settings = get_settings()
    async with request.app.state.pool.acquire() as conn:
        total, rows = await institutions_controller.list_institutions(
            conn, schema=settings.app_schema, limit=limit, offset=offset
        )
    return {"total": total, "items": [dict(row) for row in rows]}


@router.post(
    "",
    response_model=InstitutionOut,
    status_code=status.HTTP_201_CREATED,
    description="""
    Auth: Use Authorization: Bearer <access_token> from Supabase Auth
    Business requirement: Register an institution for opportunity submissions.
    Frontend note: Verification is handled separately by admins.
    """,
)
async def create_institution(
    request: Request,
    payload: InstitutionCreate,
    user=Depends(require_roles({"institution", "admin"})),
):
    settings = get_settings()
    async with request.app.state.pool.acquire() as conn:
        row = await institutions_controller.create_institution(
            conn,
            name=payload.name,
            description=payload.description,
            website=str(payload.website) if payload.website else None,
            owner_user_id=user.id,
            schema=settings.app_schema,
        )
    return dict(row)


@router.patch(
    "/{institution_id}/verify",
    response_model=InstitutionOut,
    description="""
    Auth: Use Authorization: Bearer <access_token> from Supabase Auth
    Business requirement: Admins verify institutions before promoting them.
    Frontend note: This powers the admin review workflow.
    """,
)
async def verify_institution(
    request: Request,
    institution_id: str,
    is_verified: bool,
    _user=Depends(require_roles({"admin"})),
):
    settings = get_settings()
    async with request.app.state.pool.acquire() as conn:
        row = await institutions_controller.verify_institution(
            conn,
            schema=settings.app_schema,
            institution_id=institution_id,
            is_verified=is_verified,
        )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found"
        )
    return dict(row)
