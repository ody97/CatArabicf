import asyncio
import os
import re
import sys

from telethon import TelegramClient

from ..core.logger import logging
from ..sql_helper.global_collection import (
    add_to_collectionlist,
    del_keyword_collectionlist,
    get_collectionlist_items,
)

package_patern = re.compile(r"([\w-]+)(?:=|<|>|!)")
github_patern = re.compile(r"(?:https?)?(?:www.)?(?:github.com/)?([\w\-.]+/[\w\-.]+)/?")
github_raw_pattern = re.compile(
    r"(?:https?)?(?:raw.)?(?:githubusercontent.com/)?([\w\-.]+/[\w\-.]+)/?"
)
trees_pattern = "https://api.github.com/repos/{}/git/trees/master"
raw_pattern = "https://raw.githubusercontent.com/{}/master/{}"

LOGS = logging.getLogger(__name__)


async def get_pip_packages(requirements):
    """احصل على قائمة بجميع أسماء pacakage ."""
    if requirements:
        packages = requirements
    else:
        cmd = await asyncio.create_subprocess_exec(
            sys.executable.replace(" ", "\\ "),
            "-m",
            "pip",
            "freeze",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await cmd.communicate()
        packages = stdout.decode("utf-8")
    tmp = package_patern.findall(packages)
    return [package.lower() for package in tmp]


async def install_pip_packages(packages):
    """قم بتثبيت حزم النقاط ."""
    args = ["-m", "pip", "install", "--upgrade", "--user"]
    cmd = await asyncio.create_subprocess_exec(
        sys.executable.replace(" ", "\\ "),
        *args,
        *packages,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await cmd.communicate()
    return cmd.returncode == 0


def run_async(func: callable):
    """قم بتشغيل وظائف غير متزامنة باستخدام حلقة الحدث الصحيحة ."""
    asyncio.get_event_loop()
    return loop.run_until_complete(func)


async def restart_script(client: TelegramClient, sandy):
    """أعد تشغيل البرنامج النصي الحالي ."""
    try:
        ulist = get_collectionlist_items()
        for i in ulist:
            if i == "restart_update":
                del_keyword_collectionlist("restart_update")
    except Exception as e:
        LOGS.error(e)
    try:
        add_to_collectionlist("restart_update", [sandy.chat_id, sandy.id])
    except Exception as e:
        LOGS.error(e)
    executable = sys.executable.replace(" ", "\\ ")
    args = [executable, "-m", "userbot"]
    os.execle(executable, *args, os.environ)
    os._exit(143)


async def get_message_link(client, event):
    chat = await event.get_chat()
    if event.is_private:
        return f"tg://openmessage?user_id={chat.id}&message_id={event.id}"
    return f"https://t.me/c/{chat.id}/{event.id}"
