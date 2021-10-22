import json
import os
import re

from telethon.events import CallbackQuery

from userbot import catub


@catub.tgbot.on(CallbackQuery(data=re.compile(b"hide_(.*)")))
async def on_plug_in_callback_query_handler(event):
    timestamp = int(event.pattern_match.group(1).decode("UTF-8"))
    if os.path.exists("./userbot/hide.txt"):
        jsondata = json.load(open("./userbot/hide.txt"))
        try:
            reply_pop_up_alert = jsondata[f"{timestamp}"]["text"]
        except KeyError:
            reply_pop_up_alert = "▾∮ لم تعد هذه الرسالة موجودة في خادم البوت ،ـ"
    else:
        reply_pop_up_alert = "▾∮ لم تعد هذه الرسالة موجودة ،ـ 🎈"
    await event.answer(reply_pop_up_alert, cache_time=0, alert=True)
