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
    auto_community: bool = Field(default=True, title="自动社区开关")
    exchange_enable: bool = Field(default=False, title="自动兑换开关")
    exchange_items: str = Field(default="[]", title="兑换物品ID列表(JSON)")
    last_sign_time: Optional[int] = Field(default=None, title="最后签到时间")

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

    @classmethod
    @with_session
    async def get_all_auto_community_users(
        cls,
        session: AsyncSession,
    ):
        """获取所有开启自动社区且有有效web_token的用户"""
        result = await session.execute(
            select(cls).where(
                cls.auto_community == True,
                cls.web_token != "",
            )
        )
        return result.scalars().all()

    @classmethod
    @with_session
    async def set_auto_community(
        cls,
        session: AsyncSession,
        user_id: str,
        bot_id: str,
        enabled: bool,
    ):
        result = await session.execute(
            select(cls).where(cls.user_id == user_id, cls.bot_id == bot_id)
        )
        user = result.scalars().first()
        if user:
            user.auto_community = enabled
            await session.commit()

    @classmethod
    @with_session
    async def set_exchange_enable(
        cls,
        session: AsyncSession,
        user_id: str,
        bot_id: str,
        enabled: bool,
    ):
        result = await session.execute(
            select(cls).where(cls.user_id == user_id, cls.bot_id == bot_id)
        )
        user = result.scalars().first()
        if user:
            user.exchange_enable = enabled
            await session.commit()

    @classmethod
    @with_session
    async def set_exchange_items(
        cls,
        session: AsyncSession,
        user_id: str,
        bot_id: str,
        items: str,
    ):
        result = await session.execute(
            select(cls).where(cls.user_id == user_id, cls.bot_id == bot_id)
        )
        user = result.scalars().first()
        if user:
            user.exchange_items = items
            await session.commit()

    @classmethod
    @with_session
    async def update_sign_time(
        cls,
        session: AsyncSession,
        user_id: str,
        bot_id: str,
        timestamp: int,
    ):
        result = await session.execute(
            select(cls).where(cls.user_id == user_id, cls.bot_id == bot_id)
        )
        user = result.scalars().first()
        if user:
            user.last_sign_time = timestamp
            await session.commit()


    @classmethod
    @with_session
    async def get_all_users_with_token(
        cls,
        session: AsyncSession,
    ):
        """获取所有已绑定web_token的用户"""
        result = await session.execute(
            select(cls).where(cls.web_token != "")
        )
        return result.scalars().all()


exec_list = [
    "ALTER TABLE gfe_user ADD COLUMN auto_community BOOLEAN DEFAULT 1",
    "ALTER TABLE gfe_user ADD COLUMN exchange_enable BOOLEAN DEFAULT 0",
    "ALTER TABLE gfe_user ADD COLUMN exchange_items TEXT DEFAULT '[]'",
    "ALTER TABLE gfe_user ADD COLUMN last_sign_time INTEGER",
]
