import glob
import os
import sys
from asyncio.exceptions import CancelledError
from datetime import timedelta
from pathlib import Path

import requests
from telethon import Button, functions, types, utils

from userbot import BOTLOG, BOTLOG_CHATID, PM_LOGGER_GROUP_ID

from ..Config import Config
from ..core.logger import logging
from ..core.session import catub
from ..helpers.utils import install_pip
from ..sql_helper.global_collection import (
    del_keyword_collectionlist,
    get_item_collectionlist,
)
from ..sql_helper.globals import addgvar, delgvar, gvarstatus
from .pluginmanager import load_module
from .tools import create_supergroup

LOGS = logging.getLogger("CatArabic")
cmdhr = Config.COMMAND_HAND_LER


async def setup_bot():
    """
    بدأ اول رسالة في المجموعة الذي سينشأها التليثون في التلكرام
    """
    try:
        await catub.connect()
        config = await catub(functions.help.GetConfigRequest())
        for option in config.dc_options:
            if option.ip_address == catub.session.server_address:
                if catub.session.dc_id != option.id:
                    LOGS.warning(
                        f"Fixed DC ID in session from {catub.session.dc_id}"
                        f" to {option.id}"
                    )
                catub.session.set_dc(option.id, option.ip_address, option.port)
                catub.session.save()
                break
        bot_details = await catub.tgbot.get_me()
        Config.TG_BOT_USERNAME = f"@{bot_details.username}"
        # await catub.start(bot_token=Config.TG_BOT_USERNAME)
        catub.me = await catub.get_me()
        catub.uid = catub.tgbot.uid = utils.get_peer_id(catub.me)
        if Config.OWNER_ID == 0:
            Config.OWNER_ID = utils.get_peer_id(catub.me)
    except Exception as e:
        LOGS.error(f"STRING_SESSION - {e}")
        sys.exit()


async def startupmessage():
    """
    Start up message in telegram logger group
    """
    try:
        if BOTLOG:
            Config.CATUBLOGO = await catub.tgbot.send_file(
                BOTLOG_CHATID,
                "https://telegra.ph/file/ac1a7db2e66ab5b16da5c.jpg",
                caption="**▾∮ مرحبا عزيزي ↸\n▾↫ قمت بتنصيب نـوفـمبـر الان!\n▾∮ ⪼ [ՏøuƦcε πøνεʍβεƦ 🌦](t.me/NNEEE)**",
                buttons=[(Button.url("المطور", "https://t.me/bbsss"),)],
            )
    except Exception as e:
        LOGS.error(e)
        return None
    try:
        msg_details = list(get_item_collectionlist("restart_update"))
        if msg_details:
            msg_details = msg_details[0]
    except Exception as e:
        LOGS.error(e)
        return None
    try:
        if msg_details:
            await catub.check_testcases()
            message = await catub.get_messages(msg_details[0], ids=msg_details[1])
            text = message.text + "\n\n**▾∮ حسنًا تمت اعادة البوت الى الحياة ☻**"
            await catub.edit_message(msg_details[0], msg_details[1], text)
            if gvarstatus("restartupdate") is not None:
                await catub.send_message(
                    msg_details[0],
                    f"{cmdhr}ping",
                    reply_to=msg_details[1],
                    schedule=timedelta(seconds=10),
                )
            del_keyword_collectionlist("restart_update")
    except Exception as e:
        LOGS.error(e)
        return None


# don't know work or not just a try in future will use sleep
async def ipchange():
    """
    فقط للتحقق مما إذا تغيرت الملكية أم لا
    """
    newip = (requests.get("https://httpbin.org/ip").json())["origin"]
    if gvarstatus("ipaddress") is None:
        addgvar("ipaddress", newip)
        return None
    oldip = gvarstatus("ipaddress")
    if oldip != newip:
        delgvar("ipaddress")
        LOGS.info("Ip Change detected")
        try:
            await catub.disconnect()
        except (ConnectionError, CancelledError):
            pass
        return "ip change"


async def add_bot_to_logger_group(chat_id):
    """
    لإضافة بوت إلى مجموعات المسجل
    """
    bot_details = await catub.tgbot.get_me()
    try:
        await catub(
            functions.messages.AddChatUserRequest(
                chat_id=chat_id,
                user_id=bot_details.username,
                fwd_limit=1000000,
            )
        )
    except BaseException:
        try:
            await catub(
                functions.channels.InviteToChannelRequest(
                    channel=chat_id,
                    users=[bot_details.username],
                )
            )
        except Exception as e:
            LOGS.error(str(e))


async def load_plugins(folder):
    """
    لتحميل الإضافات من المجلد المذكور
    """
    path = f"userbot/{folder}/*.py"
    files = glob.glob(path)
    files.sort()
    for name in files:
        with open(name) as f:
            path1 = Path(f.name)
            shortname = path1.stem
            try:
                if shortname.replace(".py", "") not in Config.NO_LOAD:
                    flag = True
                    check = 0
                    while flag:
                        try:
                            load_module(
                                shortname.replace(".py", ""),
                                plugin_path=f"userbot/{folder}",
                            )
                            break
                        except ModuleNotFoundError as e:
                            install_pip(e.name)
                            check += 1
                            if check > 5:
                                break
                else:
                    os.remove(Path(f"userbot/{folder}/{shortname}.py"))
            except Exception as e:
                os.remove(Path(f"userbot/{folder}/{shortname}.py"))
                LOGS.info(f"unable to load {shortname} because of error {e}")


async def verifyLoggerGroup():
    """
    Will verify the both loggers group
    """
    flag = False
    if BOTLOG:
        try:
            entity = await catub.get_entity(BOTLOG_CHATID)
            if not isinstance(entity, types.User) and not entity.creator:
                if entity.default_banned_rights.send_messages:
                    LOGS.info(
                        "أذونات مفقودة لإرسال رسائل لملف PRIVATE_GROUP_BOT_API_ID."
                    )
                if entity.default_banned_rights.invite_users:
                    LOGS.info(
                        "أذونات مفقودة لإضافة المستخدمين إلى المحدد PRIVATE_GROUP_BOT_API_ID."
                    )
        except ValueError:
            LOGS.error("PRIVATE_GROUP_BOT_API_ID لايمكن إيجاده. تأكد من صحتها.")
        except TypeError:
            LOGS.error("PRIVATE_GROUP_BOT_API_ID is غير مدعوم. تأكد من صحتها.")
        except Exception as e:
            LOGS.error(
                "حدث استثناء عند محاولة التحقق من PRIVATE_GROUP_BOT_API_ID.\n" + str(e)
            )
    else:
        descript = "لا تحذف هذه المجموعة أو تغير إلى مجموعة اخرى(اذا قمت بتغيير المجموعة سيتوقف سجل البوت)"
        _, groupid = await create_supergroup(
            "▾∮ مجموعة سجل بوت CatArabic", catub, Config.TG_BOT_USERNAME, descript
        )
        addgvar("PRIVATE_GROUP_BOT_API_ID", groupid)
        print(
            "مجموعة خاصة لـ PRIVATE_GROUP_BOT_API_ID تم إنشاؤه بنجاح وإضافته إلى vars."
        )
        flag = True
    if PM_LOGGER_GROUP_ID != -100:
        try:
            entity = await catub.get_entity(PM_LOGGER_GROUP_ID)
            if not isinstance(entity, types.User) and not entity.creator:
                if entity.default_banned_rights.send_messages:
                    LOGS.info("أذونات مفقودة لإرسال رسائل لملف PM_LOGGER_GROUP_ID.")
                if entity.default_banned_rights.invite_users:
                    LOGS.info(
                        "أذونات مفقودة لإضافة المستخدمين إلى المحدد PM_LOGGER_GROUP_ID."
                    )
        except ValueError:
            LOGS.error("PM_LOGGER_GROUP_ID لايمكن إيجاده. تأكد من صحتها.")
        except TypeError:
            LOGS.error("PM_LOGGER_GROUP_ID غير مدعوم. تأكد من صحتها.")
        except Exception as e:
            LOGS.error(
                "حدث استثناء عند محاولة التحقق من PM_LOGGER_GROUP_ID.\n" + str(e)
            )
    if flag:
        executable = sys.executable.replace(" ", "\\ ")
        args = [executable, "-m", "userbot"]
        os.execle(executable, *args, os.environ)
        sys.exit(0)
