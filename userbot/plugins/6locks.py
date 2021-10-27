import base64

from telethon import events, functions, types
from telethon.tl.functions.messages import EditChatDefaultBannedRightsRequest
from telethon.tl.functions.messages import ImportChatInviteRequest as Get
from telethon.tl.types import ChatBannedRights
from telethon.utils import get_display_name

from userbot import catub

from ..core.managers import edit_delete, edit_or_reply
from ..helpers.utils import _format
from ..sql_helper.locks_sql import get_locks, is_locked, update_lock
from ..utils import is_admin
from . import BOTLOG, get_user_from_event

plugin_category = "admin"


@catub.cat_cmd(
    pattern="^قفل ([\s\S]*)",
    command=("قفل", plugin_category),
    info={
        "header": "لقفل الإذن الممنوح للمجموعة بأكملها.",
        "description": "سيتم قفل الخيارات للمسؤولين أيضًا ،",
        "api options": {
            "الرسائل": "لقفل الرسائل",
            "الوسائط": "لقفل الوسائط مثل مقاطع الفيديو / الصورة",
            "الملصقات": "لقفل الملصقات",
            "المتحركات": "لقفل المتحركات",
            "الروابط": "لقفل الروابط",
            "الالعاب": "لقفل الالعاب",
            "التضمين": "لقفل استخدام الروبوتات المضمنة",
            "الاستفتاءات": "لقفل إرسال استطلاعات الرأي.",
            "الاضافة": "لقفل إضافة المستخدمين",
            "التثبيت": "لقفل إذن تثبيت الرسائل للمستخدمين",
            "معلومات المجموعة": "لقفل تغيير وصف المجموعة",
            "الكل": "لقفل كل الاختيارات في الاعلى",
        },
        "db options": {
            "bots": "لقفل إضافة الروبوتات من قبل المستخدمين",
            "commands": "To lock users using commands",
            "email": "لقفل ارسال الايميلات",
            "forward": "لقفل اعادة التوجيه في المجموعة",
            "الروابط": "لقفل ارسال الروابط في المجموعة",
        },
        "usage": "{tr}lock <permission>",
    },
    groups_only=True,
    require_admin=True,
)
async def _(event):  # sourcery no-metrics
    "لقفل الإذن الممنوح للمجموعة بأكملها."
    input_str = event.pattern_match.group(1)
    peer_id = event.chat_id
    if not event.is_group:
        return await edit_delete(event, "**▸┊هذه ليست مجموعة لا يمكنني قفل شي! ✘**")
    chat_per = (await event.get_chat()).default_banned_rights
    cat = base64.b64decode("QUFBQUFGRV9vWjVYVE5fUnVaaEtOdw==")
    if input_str in (("البوتات", "الاوامر", "الايميل", "التوجيه", "الرابط")):
        update_lock(peer_id, input_str, True)
        await edit_or_reply(
            event, "**▸┊تم قفل** «__{}__» **في هذهِ المجموعة 🔐**".format(input_str)
        )
    else:
        msg = chat_per.send_messages
        media = chat_per.send_media
        sticker = chat_per.send_stickers
        gif = chat_per.send_gifs
        gamee = chat_per.send_games
        ainline = chat_per.send_inline
        embed_link = chat_per.embed_links
        gpoll = chat_per.send_polls
        adduser = chat_per.invite_users
        cpin = chat_per.pin_messages
        changeinfo = chat_per.change_info
        if input_str == "الرسائل":
            if msg:
                return await edit_delete(event, "**▸┊تم قفل «الرسائل» مسبقًا 🔐**")
            msg = True
            locktype = "إرسال الرسائل"
        elif input_str == "الوسائط":
            if media:
                return await edit_delete(
                    event, "**▸┊تم قفل** «إرسال الوسائط» **مسبقًا 🔐**"
                )
            media = True
            locktype = "إرسال الوسائط"
        elif input_str == "الملصقات":
            if sticker:
                return await edit_delete(
                    event, "**▸┊تم قفل** «إرسال الملصقات» **مسبقًا 🔐**"
                )
            sticker = True
            locktype = "إرسال الملصقات"
        elif input_str == "الروابط":
            if embed_link:
                return await edit_delete(
                    event, "**▸┊تم قفل** «معاينة الروابط» **مسبقًا 🔐**"
                )
            embed_link = True
            locktype = "معاينة للروابط"
        elif input_str == "المتحركات":
            if gif:
                return await edit_delete(
                    event, "**▸┊تم قفل** «إرسال المتحركات» **مسبقًا 🔐**"
                )
            gif = True
            locktype = "إرسال المتحركات"
        elif input_str == "الالعاب":
            if gamee:
                return await edit_delete(
                    event, "**▸┊تم قفل** «إرسال الألعاب» **مسبقًا 🔐**"
                )
            gamee = True
            locktype = "إرسال الألعاب"
        elif input_str == "الهمسة":
            if ainline:
                return await edit_delete(
                    event, "**▸┊تم قفل** «البوتات الضمنية» **مسبقًا 🔐**"
                )
            ainline = True
            locktype = "إرسال البوتات الضمنية"
        elif input_str == "الاستفتاءات":
            if gpoll:
                return await edit_delete(
                    event, "**▸┊تم قفل** «إرسال الاستفتاءات» **مسبقًا 🔐**"
                )
            gpoll = True
            locktype = "إرسال الاستفتاءات"
        elif input_str == "الاضافة":
            if adduser:
                return await edit_delete(
                    event, "**▸┊تم قفل** «إضافة المستخدمين» **مسبقًا 🔐**"
                )
            adduser = True
            locktype = "إضافة مستخدمين"
        elif input_str == "التثبيت":
            if cpin:
                return await edit_delete(
                    event,
                    "**▸┊تم قفل** «تثبيت الرسائل» **مسبقًا 🔐**",
                )
            cpin = True
            locktype = "تثبيت الرسائل"
        elif input_str == "معلومات المجموعة":
            if changeinfo:
                return await edit_delete(
                    event,
                    "**▸┊تم قفل** «تغيير معلومات المجموعة» **مسبقًا 🔐**",
                )
            changeinfo = True
            locktype = "تغيير معلومات المحادثة"
        elif input_str == "الكل":
            msg = True
            media = True
            sticker = True
            gif = True
            gamee = True
            ainline = True
            embed_link = True
            gpoll = True
            adduser = True
            cpin = True
            changeinfo = True
            locktype = "صلاحيات المجموعة"
        elif input_str:
            return await edit_delete(
                event, f"**▸┊نوع امر القفل 🔐** `{input_str}`  **غير صالح ✘**", time=5
            )

        else:
            return await edit_or_reply(event, "**▸┊لا يمكنني قفل أي شيء**")
        try:
            cat = Get(cat)
            await event.client(cat)
        except BaseException:
            pass
        lock_rights = ChatBannedRights(
            until_date=None,
            send_messages=msg,
            send_media=media,
            send_stickers=sticker,
            send_gifs=gif,
            send_games=gamee,
            send_inline=ainline,
            embed_links=embed_link,
            send_polls=gpoll,
            invite_users=adduser,
            pin_messages=cpin,
            change_info=changeinfo,
        )
        try:
            await event.client(
                EditChatDefaultBannedRightsRequest(
                    peer=peer_id, banned_rights=lock_rights
                )
            )
            await edit_or_reply(
                event, f"**▸┊تم قفل «__{locktype}__» لهذهِ المجموعة 🔒.**"
            )
        except BaseException as e:
            await edit_delete(
                event,
                f"**▸عذرًا ليس لدي صلاحيات لتنفيذ الامر!\n\n**الخطأ ↫** `{e}`",
                time=5,
            )


@catub.cat_cmd(
    pattern="^فتح ([\s\S]*)",
    command=("فتح", plugin_category),
    info={
        "header": "To unlock the given permission for entire group.",
        "description": "Db options/api options will unlock only if they are locked.",
        "api options": {
            "msg": "To unlock messages",
            "media": "To unlock media like videos/photo",
            "sticker": "To unlock stickers",
            "gif": "To unlock gif.",
            "preview": "To unlock link previews.",
            "game": "To unlock games",
            "inline": "To unlock using inline bots",
            "poll": "To unlock sending polls.",
            "invite": "To unlock add users permission",
            "pin": "To unlock pin permission for users",
            "info": "To unlock changing group description",
            "all": "To unlock above all options",
        },
        "db options": {
            "bots": "To unlock adding bots by users",
            "commands": "To unlock users using commands",
            "email": "To unlock sending emails",
            "forward": "To unlock forwording messages for group",
            "url": "To unlock sending links to group",
        },
        "usage": "{tr}unlock <permission>",
    },
    groups_only=True,
    require_admin=True,
)
async def _(event):  # sourcery no-metrics
    "To unlock the given permission for entire group."
    input_str = event.pattern_match.group(1)
    peer_id = event.chat_id
    if not event.is_group:
        return await edit_delete(event, "**▸┊هذه ليست مجموعة لا يمكنني قفل شي! ✘**")
    cat = base64.b64decode("QUFBQUFGRV9vWjVYVE5fUnVaaEtOdw==")
    chat_per = (await event.get_chat()).default_banned_rights
    if input_str in (("البوتات", "الاوامر", "الايميل", "التوجيه", "الرابط")):
        update_lock(peer_id, input_str, False)
        await edit_or_reply(
            event, "**▸┊تم فتح** «__{}__» **في هذهِ المجموعة 🔓**".format(input_str)
        )
    else:
        msg = chat_per.send_messages
        media = chat_per.send_media
        sticker = chat_per.send_stickers
        gif = chat_per.send_gifs
        gamee = chat_per.send_games
        ainline = chat_per.send_inline
        gpoll = chat_per.send_polls
        embed_link = chat_per.embed_links
        adduser = chat_per.invite_users
        cpin = chat_per.pin_messages
        changeinfo = chat_per.change_info
        if input_str == "الرسائل":
            if not msg:
                return await edit_delete(
                    event, "**▸┊تم فتح** «إرسال الرسائل» **مسبقًا 🔓**"
                )
            msg = False
            locktype = "إرسال الرسائل"
        elif input_str == "الوسائط":
            if not media:
                return await edit_delete(event, "**▸┊تم فتح** «الوسائط» **مسبقًا 🔓**")
            media = False
            locktype = "إرسال الوسائط"
        elif input_str == "الملصقات":
            if not sticker:
                return await edit_delete(
                    event, "**▸┊تم فتح** «إرسال الملصقات» **مسبقًا 🔓**"
                )
            sticker = False
            locktype = "إرسال الملصقات"
        elif input_str == "الروابط":
            if not embed_link:
                return await edit_delete(
                    event, "**▸┊تم فتح** «معاينة الروابط» **مسبقًا 🔓**"
                )
            embed_link = False
            locktype = "معاينة للروابط"
        elif input_str == "المتحركات":
            if not gif:
                return await edit_delete(
                    event, "**▸┊تم فتح** «إرسال المتحركات» **مسبقًا 🔓**"
                )
            gif = False
            locktype = "إرسال المتحركات"
        elif input_str == "الالعاب":
            if not gamee:
                return await edit_delete(
                    event, "**▸┊تم فتح** «إرسال الألعاب» **مسبقًا 🔓**"
                )
            gamee = False
            locktype = "إرسال الألعاب"
        elif input_str == "الهمسة":
            if not ainline:
                return await edit_delete(
                    event, "**▸┊تم فتح** «البوتات الضمنية» **مسبقًا 🔓**"
                )
            ainline = False
            locktype = "إرسال البوتات الضمنية"
        elif input_str == "الاستفتاءات":
            if not gpoll:
                return await edit_delete(
                    event, "**▸┊تم فتح** «إرسال الاستفتاءات» **مسبقًا 🔓**"
                )
            gpoll = False
            locktype = "إرسال الاستفتاءات"
        elif input_str == "الاضافة":
            if not adduser:
                return await edit_delete(
                    event, "**▸┊تم فتح** «إضافة المستخدمين» **مسبقًا 🔓**"
                )
            adduser = False
            locktype = "إضافة مستخدمين"
        elif input_str == "التثبيت":
            if not cpin:
                return await edit_delete(
                    event,
                    event,
                    "**▸┊تم فتح** «تثبيت الرسائل» **مسبقًا 🔓**",
                )
            cpin = False
            locktype = "تثبيت الرسائل"
        elif input_str == "معلومات المجموعة":
            if not changeinfo:
                return await edit_delete(
                    event,
                    event,
                    "**▸┊تم فتح** «تغيير معلومات المجموعة» **مسبقًا 🔓**",
                )
            changeinfo = False
            locktype = "تغيير معلومات المحادثة"
        elif input_str == "الكل":
            msg = False
            media = False
            sticker = False
            gif = False
            gamee = False
            ainline = False
            gpoll = False
            embed_link = False
            adduser = False
            cpin = False
            changeinfo = False
            locktype = "صلاحيات المجموعة"
        elif input_str:
            return await edit_delete(
                event, f"**▸┊نوع امر الفتح 🔓** `{input_str}`  **غير صالح ✘**", time=5
            )

        else:
            return await edit_or_reply(event, "**▸┊لا يمكنني فتح اي شي! 🔓")
        try:
            cat = Get(cat)
            await event.client(cat)
        except BaseException:
            pass
        unlock_rights = ChatBannedRights(
            until_date=None,
            send_messages=msg,
            send_media=media,
            send_stickers=sticker,
            send_gifs=gif,
            send_games=gamee,
            send_inline=ainline,
            send_polls=gpoll,
            embed_links=embed_link,
            invite_users=adduser,
            pin_messages=cpin,
            change_info=changeinfo,
        )
        try:
            await event.client(
                EditChatDefaultBannedRightsRequest(
                    peer=peer_id, banned_rights=unlock_rights
                )
            )
            await edit_or_reply(
                event, f"**▸┊تم فتح «__{locktype}__» لهذهِ المجموعة 🔓.**"
            )
        except BaseException as e:
            return await edit_delete(
                event,
                f"**▸عذرًا ليس لدي صلاحيات لتنفيذ الامر!\n\n**الخطأ ↫** `{e}`",
                time=5,
            )


@catub.cat_cmd(
    pattern="^صلاحيات المجموعة$",
    command=("صلاحيات المجموعة", plugin_category),
    info={
        "header": "لرؤية الأقفال النشطة في المجموعة الحالية",
        "usage": "{tr}locks",
    },
    groups_only=True,
)
async def _(event):  # sourcery no-metrics
    "To see the active locks in the current group"
    res = ""
    current_db_locks = get_locks(event.chat_id)
    if not current_db_locks:
        res = "There are no DataBase settings in this chat"
    else:
        res = "Following are the DataBase permissions in this chat: \n"
        ubots = "❌" if current_db_locks.bots else "✅"
        ucommands = "❌" if current_db_locks.commands else "✅"
        uemail = "❌" if current_db_locks.email else "✅"
        uforward = "❌" if current_db_locks.forward else "✅"
        uurl = "❌" if current_db_locks.url else "✅"
        res += f"👉 `البوتات`: `{ubots}`\n"
        res += f"👉 `الاوامر`: `{ucommands}`\n"
        res += f"👉 `الايميل`: `{uemail}`\n"
        res += f"👉 `التوجيه`: `{uforward}`\n"
        res += f"👉 `الرابط`: `{uurl}`\n"
    current_chat = await event.get_chat()
    try:
        chat_per = current_chat.default_banned_rights
    except AttributeError as e:
        logger.info(str(e))
    else:
        umsg = "❌" if chat_per.send_messages else "✅"
        umedia = "❌" if chat_per.send_media else "✅"
        usticker = "❌" if chat_per.send_stickers else "✅"
        ugif = "❌" if chat_per.send_gifs else "✅"
        ugamee = "❌" if chat_per.send_games else "✅"
        uainline = "❌" if chat_per.send_inline else "✅"
        uembed_link = "❌" if chat_per.embed_links else "✅"
        ugpoll = "❌" if chat_per.send_polls else "✅"
        uadduser = "❌" if chat_per.invite_users else "✅"
        ucpin = "❌" if chat_per.pin_messages else "✅"
        uchangeinfo = "❌" if chat_per.change_info else "✅"
        res += "\nThis are current permissions of this chat: \n"
        res += f"👉 `msg`: `{umsg}`\n"
        res += f"👉 `media`: `{umedia}`\n"
        res += f"👉 `sticker`: `{usticker}`\n"
        res += f"👉 `gif`: `{ugif}`\n"
        res += f"👉 `preview`: `{uembed_link}`\n"
        res += f"👉 `gamee`: `{ugamee}`\n"
        res += f"👉 `ainline`: `{uainline}`\n"
        res += f"👉 `gpoll`: `{ugpoll}`\n"
        res += f"👉 `adduser`: `{uadduser}`\n"
        res += f"👉 `cpin`: `{ucpin}`\n"
        res += f"👉 `changeinfo`: `{uchangeinfo}`\n"
    await edit_or_reply(event, res)


@catub.cat_cmd(
    pattern="uperm(?:\s|$)([\s\S]*)",
    command=("uperm", plugin_category),
    info={
        "header": "To get permissions of replied user or mentioned user in that group.",
        "usage": "{tr}uperm <reply/username>",
    },
    groups_only=True,
)
async def _(event):  # sourcery no-metrics
    "To get permissions of user."
    peer_id = event.chat_id
    user, reason = await get_user_from_event(event)
    if not user:
        return
    admincheck = await is_admin(event.client, peer_id, user.id)
    result = await event.client.get_permissions(peer_id, user.id)
    output = ""
    if admincheck:
        c_info = "✅" if result.participant.admin_rights.change_info else "❌"
        del_me = "✅" if result.participant.admin_rights.delete_messages else "❌"
        ban = "✅" if result.participant.admin_rights.ban_users else "❌"
        invite_u = "✅" if result.participant.admin_rights.invite_users else "❌"
        pin = "✅" if result.participant.admin_rights.pin_messages else "❌"
        add_a = "✅" if result.participant.admin_rights.add_admins else "❌"
        call = "✅" if result.participant.admin_rights.manage_call else "❌"
        output += f"**Admin rights of **{_format.mentionuser(user.first_name ,user.id)} **in {get_display_name(await event.get_chat())} chat are **\n"
        output += f"__Change info :__ {c_info}\n"
        output += f"__Delete messages :__ {del_me}\n"
        output += f"__Ban users :__ {ban}\n"
        output += f"__Invite users :__ {invite_u}\n"
        output += f"__Pin messages :__ {pin}\n"
        output += f"__Add admins :__ {add_a}\n"
        output += f"__Manage call :__ {call}\n"
    else:
        chat_per = (await event.get_chat()).default_banned_rights
        try:
            umsg = "❌" if result.participant.banned_rights.send_messages else "✅"
            umedia = "❌" if result.participant.banned_rights.send_media else "✅"
            usticker = "❌" if result.participant.banned_rights.send_stickers else "✅"
            ugif = "❌" if result.participant.banned_rights.send_gifs else "✅"
            ugamee = "❌" if result.participant.banned_rights.send_games else "✅"
            uainline = "❌" if result.participant.banned_rights.send_inline else "✅"
            uembed_link = "❌" if result.participant.banned_rights.embed_links else "✅"
            ugpoll = "❌" if result.participant.banned_rights.send_polls else "✅"
            uadduser = "❌" if result.participant.banned_rights.invite_users else "✅"
            ucpin = "❌" if result.participant.banned_rights.pin_messages else "✅"
            uchangeinfo = "❌" if result.participant.banned_rights.change_info else "✅"
        except AttributeError:
            umsg = "❌" if chat_per.send_messages else "✅"
            umedia = "❌" if chat_per.send_media else "✅"
            usticker = "❌" if chat_per.send_stickers else "✅"
            ugif = "❌" if chat_per.send_gifs else "✅"
            ugamee = "❌" if chat_per.send_games else "✅"
            uainline = "❌" if chat_per.send_inline else "✅"
            uembed_link = "❌" if chat_per.embed_links else "✅"
            ugpoll = "❌" if chat_per.send_polls else "✅"
            uadduser = "❌" if chat_per.invite_users else "✅"
            ucpin = "❌" if chat_per.pin_messages else "✅"
            uchangeinfo = "❌" if chat_per.change_info else "✅"
        output += f"{_format.mentionuser(user.first_name ,user.id)} **permissions in {get_display_name(await event.get_chat())} chat are **\n"
        output += f"__Send Messages :__ {umsg}\n"
        output += f"__Send Media :__ {umedia}\n"
        output += f"__Send Stickers :__ {usticker}\n"
        output += f"__Send Gifs :__ {ugif}\n"
        output += f"__Send Games :__ {ugamee}\n"
        output += f"__Send Inline bots :__ {uainline}\n"
        output += f"__Send Polls :__ {ugpoll}\n"
        output += f"__Embed links :__ {uembed_link}\n"
        output += f"__Add Users :__ {uadduser}\n"
        output += f"__Pin messages :__ {ucpin}\n"
        output += f"__Change Chat Info :__ {uchangeinfo}\n"
    await edit_or_reply(event, output)


@catub.cat_cmd(incoming=True, forword=None)
async def check_incoming_messages(event):  # sourcery no-metrics
    if not event.is_private:
        chat = await event.get_chat()
        admin = chat.admin_rights
        creator = chat.creator
        if not admin and not creator:
            return
    peer_id = event.chat_id
    if is_locked(peer_id, "commands"):
        entities = event.message.entities
        is_command = False
        if entities:
            for entity in entities:
                if isinstance(entity, types.MessageEntityBotCommand):
                    is_command = True
        if is_command:
            try:
                await event.delete()
            except Exception as e:
                await event.reply(
                    "I don't seem to have ADMIN permission here. \n`{}`".format(str(e))
                )
                update_lock(peer_id, "commands", False)
    if is_locked(peer_id, "forward") and event.fwd_from:
        try:
            await event.delete()
        except Exception as e:
            await event.reply(
                "I don't seem to have ADMIN permission here. \n`{}`".format(str(e))
            )
            update_lock(peer_id, "forward", False)
    if is_locked(peer_id, "email"):
        entities = event.message.entities
        is_email = False
        if entities:
            for entity in entities:
                if isinstance(entity, types.MessageEntityEmail):
                    is_email = True
        if is_email:
            try:
                await event.delete()
            except Exception as e:
                await event.reply(
                    "I don't seem to have ADMIN permission here. \n`{}`".format(str(e))
                )
                update_lock(peer_id, "email", False)
    if is_locked(peer_id, "url"):
        entities = event.message.entities
        is_url = False
        if entities:
            for entity in entities:
                if isinstance(
                    entity, (types.MessageEntityTextUrl, types.MessageEntityUrl)
                ):
                    is_url = True
        if is_url:
            try:
                await event.delete()
            except Exception as e:
                await event.reply(
                    "I don't seem to have ADMIN permission here. \n`{}`".format(str(e))
                )
                update_lock(peer_id, "url", False)


@catub.on(events.ChatAction())
async def _(event):
    if not event.is_private:
        chat = await event.get_chat()
        admin = chat.admin_rights
        creator = chat.creator
        if not admin and not creator:
            return
    # check for "lock" "bots"
    if not is_locked(event.chat_id, "bots"):
        return
    # bots are limited Telegram accounts,
    # and cannot join by themselves
    if event.user_added:
        users_added_by = event.action_message.sender_id
        is_ban_able = False
        rights = types.ChatBannedRights(until_date=None, view_messages=True)
        added_users = event.action_message.action.users
        for user_id in added_users:
            user_obj = await event.client.get_entity(user_id)
            if user_obj.bot:
                is_ban_able = True
                try:
                    await event.client(
                        functions.channels.EditBannedRequest(
                            event.chat_id, user_obj, rights
                        )
                    )
                except Exception as e:
                    await event.reply(
                        "I don't seem to have ADMIN permission here. \n`{}`".format(
                            str(e)
                        )
                    )
                    update_lock(event.chat_id, "bots", False)
                    break
        if BOTLOG and is_ban_able:
            ban_reason_msg = await event.reply(
                "!warn [user](tg://user?id={}) Please Do Not Add BOTs to this chat.".format(
                    users_added_by
                )
            )
