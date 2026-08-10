from langgraph.checkpoint.postgres.aio import (
    AsyncPostgresSaver,
)
from langgraph.checkpoint.serde.jsonplus import (
    JsonPlusSerializer,
)
from psycopg import AsyncConnection
from psycopg.rows import (
    DictRow,
    dict_row,
)
from psycopg_pool import AsyncConnectionPool

from app.core.config import settings

_checkpoint_pool: (
    AsyncConnectionPool[
        AsyncConnection[DictRow]
    ]
    | None
) = None

_checkpointer: (
    AsyncPostgresSaver | None
) = None


async def initialize_checkpointing(
) -> AsyncPostgresSaver:
    global _checkpoint_pool
    global _checkpointer

    if _checkpointer is not None:
        return _checkpointer

    pool: AsyncConnectionPool[
        AsyncConnection[DictRow]
    ] = AsyncConnectionPool(
        conninfo=(
            settings
            .checkpoint_database_url
        ),
        connection_class=(
            AsyncConnection[DictRow]
        ),
        min_size=1,
        max_size=5,
        open=False,
        kwargs={
            "autocommit": True,
            "prepare_threshold": 0,
            "row_factory": dict_row,
        },
    )

    await pool.open(
        wait=True
    )

    serializer = JsonPlusSerializer(
        pickle_fallback=False,
        allowed_msgpack_modules=None,
    )

    checkpointer = AsyncPostgresSaver(
        conn=pool,
        serde=serializer,
    )

    await checkpointer.setup()

    _checkpoint_pool = pool
    _checkpointer = checkpointer

    return checkpointer


def get_checkpointer(
) -> AsyncPostgresSaver:
    if _checkpointer is None:
        raise RuntimeError(
            "LangGraph checkpointing "
            "has not been initialized."
        )

    return _checkpointer


async def close_checkpointing(
) -> None:
    global _checkpoint_pool
    global _checkpointer

    if _checkpoint_pool is not None:
        await _checkpoint_pool.close()

    _checkpoint_pool = None
    _checkpointer = None