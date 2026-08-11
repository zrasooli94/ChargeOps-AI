from typing import (
    Annotated,
    cast,
)

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from fastapi.security import (
    OAuth2PasswordRequestForm,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.core.auth_dependencies import (
    CurrentUser,
)
from app.core.database import get_db
from app.core.security import (
    create_access_token,
)
from app.schemas.auth import (
    AccessToken,
    UserRead,
    UserRole,
)
from app.services.auth_service import (
    authenticate_user,
)

router = APIRouter(
    prefix="/auth",
    tags=[
        "Authentication",
    ],
)


@router.post(
    "/login",
    response_model=AccessToken,
)
async def login(
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends(),
    ],
    session: Annotated[
        AsyncSession,
        Depends(
            get_db
        ),
    ],
) -> AccessToken:
    user = await authenticate_user(
        session=session,
        email=form_data.username,
        password=form_data.password,
    )

    if user is None:
        raise HTTPException(
            status_code=(
                status
                .HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Incorrect email "
                "or password."
            ),
            headers={
                "WWW-Authenticate": (
                    "Bearer"
                ),
            },
        )

    role = cast(
        UserRole,
        user.role,
    )

    access_token = (
        create_access_token(
            user_id=user.id,
            role=role,
        )
    )

    return AccessToken(
        access_token=(
            access_token
        )
    )


@router.get(
    "/me",
    response_model=UserRead,
)
async def get_me(
    current_user: CurrentUser,
) -> UserRead:
    return UserRead.model_validate(
        current_user
    )