from aiogram.types import Update
from fastapi import APIRouter, HTTPException, Request

# from bot import bot, dp

router = APIRouter()


# @router.post("/webhook")
# async def webhook(request: Request):
#     update = Update.model_validate(await request.json(), context={"bot": bot})
#     await dp.feed_update(bot, update)

#     return {"status": "ok"}
