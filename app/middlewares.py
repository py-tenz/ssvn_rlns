from __future__ import annotations

from aiogram import BaseMiddleware
from typing import Any, Awaitable, Callable, Dict

from .db import Mongo

class DbMiddleware(BaseMiddleware):
    def __init__(self, mongo: Mongo):
        super().__init__()
        self.mongo = mongo

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any],
    ) -> Any:
        data["mongo"] = self.mongo
        return await handler(event, data)
