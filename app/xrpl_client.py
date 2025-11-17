from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator, Dict, Any

import structlog
from xrpl.asyncio.clients import AsyncWebsocketClient
from xrpl.models.requests import AccountTx

from .config import get_settings

logger = structlog.get_logger(__name__)


class XRPLStream:
    def __init__(self):
        self.settings = get_settings()
        self.ws_url = self.settings.xrpl_ws_url
        self.addresses = self.settings.xrpl_account_addresses

    @asynccontextmanager
    async def websocket(self):
        client = AsyncWebsocketClient(self.ws_url)
        await client.open()
        try:
            yield client
        finally:
            await client.close()

    async def backfill(self, client: AsyncWebsocketClient, ledger_index_min=None):
        for address in self.addresses:
            req = AccountTx(
                account=address,
                ledger_index_min=ledger_index_min or -1,
                ledger_index_max=-1,
                limit=200,
            )
            response = await client.request(req)
            for tx in response.result.get("transactions", []):
                yield tx

    async def stream(self) -> AsyncGenerator[Dict[str, Any], None]:
        async with self.websocket() as client:
            sub_request = {
                "command": "subscribe",
                "accounts": self.addresses,
            }
            await client.send(sub_request)
            try:
                async for message in client:
                    if message.get("type") == "transaction":
                        yield message
            except asyncio.CancelledError:
                logger.info("XRPL stream cancelled")
                raise
            except Exception as exc:  # pragma: no cover
                logger.exception("XRPL stream error", exc_info=exc)
                await asyncio.sleep(5)
                async for event in self.stream():
                    yield event


def normalize_transaction(event: Dict[str, Any]) -> Dict[str, Any]:
    tx = event.get("transaction", {})
    meta = event.get("meta", {})
    delivered_amount = meta.get("delivered_amount") or tx.get("Amount")
    amount_xrp = 0.0
    if isinstance(delivered_amount, str):
        amount_xrp = float(delivered_amount) / 1_000_000
    timestamp = datetime.fromtimestamp(event.get("date", 0) + 946684800)
    direction = "inbound"
    account = tx.get("Account")
    destination = tx.get("Destination")
    settings = get_settings()
    if account in settings.xrpl_account_addresses:
        direction = "outbound"
    counterparty = destination if direction == "outbound" else account
    memo = None
    memos = tx.get("Memos")
    if memos:
        memo_data = memos[0].get("Memo", {}).get("MemoData")
        if memo_data:
            memo = bytes.fromhex(memo_data).decode("utf-8", errors="ignore")
    return {
        "hash": tx.get("hash") or event.get("hash"),
        "ledger_index": event.get("ledger_index") or tx.get("ledger_index"),
        "account": account,
        "destination": destination,
        "amount_xrp": amount_xrp,
        "direction": direction,
        "counterparty": counterparty,
        "memo": memo,
        "timestamp": timestamp,
        "raw": event,
    }
