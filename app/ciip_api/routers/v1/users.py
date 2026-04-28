from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.ciip_api.schemas.users import UserOut, UserRole, UserUpsert
from app.controllers import users as users_controller
from app.utils.auth import get_current_user
from app.utils.config import get_settings


router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=UserOut,
    description="""
    Auth: Use Authorization: Bearer <access_token> from Supabase Auth
    Business requirement: Fetch the authenticated user's profile.
    Frontend note: Call after login to sync Supabase user data.
    """,
)
async def get_me(request: Request, user=Depends(get_current_user)):
    settings = get_settings()
    async with request.app.state.pool.acquire() as conn:
        row = await users_controller.get_user(
            conn, user_id=user.id, schema=settings.app_schema
        )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return dict(row)


@router.post(
    "/me",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    description="""
    Auth: Use Authorization: Bearer <access_token> from Supabase Auth
    Business requirement: Ensure the user exists in the CIIP database.
    Frontend note: Use this after login to upsert profile fields.
    """,
)
async def upsert_me(
    request: Request,
    payload: UserUpsert,
    user=Depends(get_current_user),
):
    settings = get_settings()
    async with request.app.state.pool.acquire() as conn:
        row = await users_controller.upsert_user(
            conn,
            user_id=user.id,
            email=user.email,
            full_name=payload.full_name,
            role=UserRole(user.role),
            audience_type=payload.audience_type,
            schema=settings.app_schema,
        )
    return dict(row)
