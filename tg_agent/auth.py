from __future__ import annotations
from datetime import datetime
from sqlalchemy import Column, String, BigInteger, DateTime
from db.postgres import Base


class TelegramBinding(Base):
    __tablename__ = "telegram_bindings"

    chat_id = Column(BigInteger, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


async def get_user_id_by_chat(db, chat_id: int) -> str | None:
    from sqlalchemy import select
    result = await db.scalar(
        select(TelegramBinding.user_id).where(TelegramBinding.chat_id == chat_id)
    )
    return result


async def bind_chat_to_user(db, chat_id: int, user_id: str) -> TelegramBinding:
    from sqlalchemy import select
    existing = await db.scalar(
        select(TelegramBinding).where(TelegramBinding.chat_id == chat_id)
    )
    if existing:
        existing.user_id = user_id
        await db.commit()
        return existing

    binding = TelegramBinding(chat_id=chat_id, user_id=user_id)
    db.add(binding)
    await db.commit()
    return binding
