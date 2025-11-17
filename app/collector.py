from __future__ import annotations

import asyncio
from contextlib import contextmanager

import structlog
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from .db import SessionLocal, init_db
from .models import Transaction, CursorState
from .xrpl_client import XRPLStream, normalize_transaction
from .alerts import AlertEngine

logger = structlog.get_logger(__name__)


@contextmanager
def session_scope():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


class CollectorService:
    def __init__(self):
        init_db()
        self.stream = XRPLStream()
        self.alert_engine = AlertEngine()

    async def run(self):
        logger.info("collector.start")
        async for event in self.stream.stream():
            tx_data = normalize_transaction(event)
            await self.persist_transaction(tx_data)
            await self.alert_engine.evaluate(tx_data)

    async def persist_transaction(self, tx_data):
        with session_scope() as session:
            existing = session.get(Transaction, tx_data["hash"])
            if existing:
                return
            tx = Transaction(**tx_data)
            session.add(tx)
            cursor = session.scalar(select(CursorState).limit(1))
            if not cursor:
                cursor = CursorState(last_ledger_index=tx.ledger_index)
                session.add(cursor)
            else:
                cursor.last_ledger_index = max(
                    cursor.last_ledger_index or 0, tx.ledger_index or 0
                )
        logger.info("collector.persisted", hash=tx_data["hash"])


async def main():
    service = CollectorService()
    while True:
        try:
            await service.run()
        except SQLAlchemyError as db_exc:
            logger.exception("collector.db_error", exc_info=db_exc)
            await asyncio.sleep(5)
        except Exception as exc:
            logger.exception("collector.error", exc_info=exc)
            await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())
