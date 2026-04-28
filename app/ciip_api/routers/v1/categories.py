from fastapi import APIRouter, Depends, Request, status

from app.ciip_api.schemas.categories import CategoryCreate, CategoryOut
from app.controllers import categories as categories_controller
from app.utils.auth import get_current_user
from app.utils.config import get_settings


router = APIRouter(prefix="/categories", tags=["categories"])


@router.get(
    "",
    response_model=list[CategoryOut],
    description="""
    Auth: Use Authorization: Bearer <access_token> from Supabase Auth
    Business requirement: List opportunity categories for filtering.
    Frontend note: Cache results in the client for dropdowns.
    """,
)
async def list_categories(request: Request, _user=Depends(get_current_user)):
    settings = get_settings()
    async with request.app.state.pool.acquire() as conn:
        rows = await categories_controller.list_categories(conn, schema=settings.app_schema)
    return [dict(row) for row in rows]


@router.post(
    "",
    response_model=CategoryOut,
    status_code=status.HTTP_201_CREATED,
    description="""
    Auth: Use Authorization: Bearer <access_token> from Supabase Auth
    Business requirement: Allow admins to add new opportunity categories.
    Frontend note: Keep slugs unique and URL-safe.
    """,
)
async def create_category(
    request: Request,
    payload: CategoryCreate,
    _user=Depends(get_current_user),
):
    settings = get_settings()
    async with request.app.state.pool.acquire() as conn:
        row = await categories_controller.create_category(
            conn, name=payload.name, slug=payload.slug, schema=settings.app_schema
        )
    return dict(row)
