from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_dependencies import (
    AdminUser,
)
from app.core.database import get_db
from app.schemas.auth import (
    UserCreateRequest,
    UserRead,
    UserRoleUpdate,
    UserStatusUpdate,
)
from app.services.auth_service import (
    UserAlreadyExistsError,
    create_user,
    list_users,
    update_user_role,
    update_user_status,
)

router = APIRouter(
    prefix="/users",
    tags=["User Management"],
)


# =================================================
# List users
#
# Admin only
# =================================================


@router.get(
    "",
    response_model=list[UserRead],
)
async def get_users(
    _current_user: AdminUser,
    session: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
) -> list[UserRead]:
    users = await list_users(
        session=session
    )

    return [
        UserRead.model_validate(
            user
        )
        for user in users
    ]


# =================================================
# Create user
#
# Admin only
# =================================================


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_chargeops_user(
    request: UserCreateRequest,
    _current_user: AdminUser,
    session: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
) -> UserRead:
    try:
        user = await create_user(
            session=session,
            email=request.email,
            password=request.password,
            role=request.role,
        )

    except UserAlreadyExistsError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=str(error),
        ) from error

    return UserRead.model_validate(
        user
    )


# =================================================
# Change user role
#
# Admin only
#
# Prevent an administrator from accidentally
# removing their own admin permission.
# =================================================


@router.patch(
    "/{user_id}/role",
    response_model=UserRead,
)
async def change_user_role(
    user_id: UUID,
    request: UserRoleUpdate,
    current_user: AdminUser,
    session: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
) -> UserRead:
    if (
        user_id == current_user.id
        and request.role != "admin"
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=(
                "You cannot remove your own "
                "administrator role."
            ),
        )

    user = await update_user_role(
        session=session,
        user_id=user_id,
        role=request.role,
    )

    if user is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="User not found.",
        )

    return UserRead.model_validate(
        user
    )


# =================================================
# Activate / deactivate user
#
# Admin only
#
# Prevent an administrator from accidentally
# disabling their own authenticated account.
# =================================================


@router.patch(
    "/{user_id}/status",
    response_model=UserRead,
)
async def change_user_status(
    user_id: UUID,
    request: UserStatusUpdate,
    current_user: AdminUser,
    session: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
) -> UserRead:
    if (
        user_id == current_user.id
        and not request.is_active
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=(
                "You cannot deactivate "
                "your own account."
            ),
        )

    user = await update_user_status(
        session=session,
        user_id=user_id,
        is_active=request.is_active,
    )

    if user is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="User not found.",
        )

    return UserRead.model_validate(
        user
    )