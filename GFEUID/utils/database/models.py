from typing import Dict, Any, Optional

from sqlmodel import Field, col, select
from sqlalchemy.ext.asyncio import AsyncSession

from gsuid_core.utils.database.base_models import (
    Bind,
    User,
    with_session,
)


class GfeBind(Bind, table=True):
    __table_args__: Dict[str, Any] = {"extend_existing": True}
    uid: Optional[str] = Field(default=None, title="GF2游戏UID")
    server: str = Field(default="cn", title="服务器(cn/intl)")

    @classmethod
    @with_session
    async def get_uid_by_game(
        cls,
        session: AsyncSession,
        user_id: str,
        bot_id: str,
    ) -> Optional[str]:
        result = await session.execute(
            select(cls).where(cls.user_id == user_id, cls.bot_id == bot_id)
        )
        record = result.scalars().first()
        return record.uid if record else None

    @classmethod
    async def insert_gfe_uid(
        cls,
        user_id: str,
        bot_id: str,
        uid: str,
        server: str = "cn",
    ) -> int:
        if not uid:
            return -1
        if not await cls.bind_exists(user_id, bot_id):
            return await cls.insert_data(
                user_id=user_id,
                bot_id=bot_id,
                uid=uid,
                server=server,
            )
        # 已存在：更新
        await cls.update_data(
            user_id=user_id,
            bot_id=bot_id,
            uid=uid,
            server=server,
        )
        return 0


class GfeUser(User, table=True):
    __table_args__: Dict[str, Any] = {"extend_existing": True}
    uid: str = Field(default="", title="GF2游戏UID")
    nickname: str = Field(default="", title="游戏昵称")
    web_token: str = Field(default="", title="BBS WebToken")
    server: str = Field(default="cn", title="服务器(cn/intl)")
    login_type: str = Field(default="", title="登录方式(sms/password)")
    last_bind_time: Optional[int] = Field(default=None, title="最后绑定时间")

    @classmethod
    @with_session
    async def select_by_user(
        cls,
        session: AsyncSession,
        user_id: str,
        bot_id: str,
    ):
        result = await session.execute(
            select(cls).where(cls.user_id == user_id, cls.bot_id == bot_id)
        )
        return result.scalars().first()

    @classmethod
    @with_session
    async def delete_user(
        cls,
        session: AsyncSession,
        user_id: str,
        bot_id: str,
    ):
        from sqlalchemy import delete
        sql = delete(cls).where(cls.user_id == user_id, cls.bot_id == bot_id)
        await session.execute(sql)
