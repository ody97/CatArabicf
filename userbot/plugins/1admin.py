from asyncio import sleep

from telethon import functions
from telethon.errors import (
    BadRequestError,
    ImageProcessFailedError,
    PhotoCropSizeSmallError,
)
from telethon.errors.rpcerrorlist import UserAdminInvalidError, UserIdInvalidError
from telethon.tl.functions.channels import (
    EditAdminRequest,
    EditBannedRequest,
    EditPhotoRequest,
)
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import (
    ChatAdminRights,
    ChatBannedRights,
    InputChatPhotoEmpty,
    MessageMediaPhoto,
)

from userbot import catub

from ..core.logger import logging
from ..core.managers import edit_delete, edit_or_reply
from ..helpers import media_type
from ..helpers.utils import _format, get_user_from_event
from ..sql_helper.mute_sql import is_muted, mute, unmute
from . import BOTLOG, BOTLOG_CHATID

# =================== STRINGS ============
PP_TOO_SMOL = "**▾∮ الصورة صغيرة جدًا لا يمكنني وضعها ✘**"
PP_ERROR = "**▾∮ فشل أثناء معالجة الصورة ✘**"
NO_ADMIN = "**▾↫ عذرًا انا لست مشرفًا هنا! ✘**"
NO_PERM = "**▾↫ عذرًا احتاج الى صلاحيات! ✘**"
CHAT_PP_CHANGED = "**▾↫ تم تغيير صورة المجموعة ✓**"
INVALID_MEDIA = "**▾↫ ملحق غير صالح ✘**"

BANNED_RIGHTS = ChatBannedRights(
    until_date=None,
    view_messages=True,
    send_messages=True,
    send_media=True,
    send_stickers=True,
    send_gifs=True,
    send_games=True,
    send_inline=True,
    embed_links=True,
)

UNBAN_RIGHTS = ChatBannedRights(
    until_date=None,
    send_messages=None,
    send_media=None,
    send_stickers=None,
    send_gifs=None,
    send_games=None,
    send_inline=None,
    embed_links=None,
)

LOGS = logging.getLogger(__name__)
MUTE_RIGHTS = ChatBannedRights(until_date=None, send_messages=True)
UNMUTE_RIGHTS = ChatBannedRights(until_date=None, send_messages=False)

plugin_category = "admin"
# ================================================


@catub.cat_cmd(
    pattern="^صورة( ضع| حذف)$",
    command=("صورة( ضع| حذف)", plugin_category),
    info={
        "عمل الملف": "لتغيير صورة  المجموعة أو حذفها",
        "الوصف": "الرد على صورة لوضعها صورة للمجموعة",
        "الاوامر": {
            "صورة ضع": "لوضع صورة للمجموعة ",
            "صورة حذف": "لحذف صورة المجموعة",
        },
        "طريقة الاستخدام": [
            "{tr}ضع صورة <قم بالرد ع الصورة>",
            "{tr}حذف صورة< لحذف صورة المجموعة>",
        ],
    },
    groups_only=True,
    require_admin=True,
)
async def set_group_photo(event):  # sourcery no-metrics
    "لتغير صورة المجموعة!"
    flag = (event.pattern_match.group(1)).strip()
    if flag == "ضع":
        replymsg = await event.get_reply_message()
        photo = None
        if replymsg and replymsg.media:
            if isinstance(replymsg.media, MessageMediaPhoto):
                photo = await event.client.download_media(message=replymsg.photo)
            elif "image" in replymsg.media.document.mime_type.split("/"):
                photo = await event.client.download_file(replymsg.media.document)
            else:
                return await edit_delete(event, INVALID_MEDIA)
        if photo:
            try:
                await event.client(
                    EditPhotoRequest(
                        event.chat_id, await event.client.upload_file(photo)
                    )
                )
                await edit_delete(event, CHAT_PP_CHANGED)
            except PhotoCropSizeSmallError:
                return await edit_delete(event, PP_TOO_SMOL)
            except ImageProcessFailedError:
                return await edit_delete(event, PP_ERROR)
            except Exception as e:
                return await edit_delete(
                    event, f"**▾∮ هنالك خطأ ... تحقق ↶**\n`{str(e)}`"
                )
            process = "تغيير"
    else:
        try:
            await event.client(EditPhotoRequest(event.chat_id, InputChatPhotoEmpty()))
        except Exception as e:
            return await edit_delete(event, f"**▾∮ هنالك خطأ ... تحقق ↶**\n`{str(e)}`")
        process = "حذف"
        await edit_delete(event, "**▾∮ تم حذف صورة المجموعة بنجاح ✓**")
    if BOTLOG:
        await event.client.send_message(
            BOTLOG_CHATID,
            "**⌔∮ صورة المجموعة 📷**\n\n"
            f"**⌔↫ تم** ┆__{process}__┆**صورة المجموعة**\n**⌔∮ اسم المجموعة ✎ ↫** 『`{event.chat.title}`』\n**⌔∮ ايدي المجموعة 🆔 ↫** 「`{event.chat_id}`」",
        )


@catub.cat_cmd(
    pattern="^رفع مشرف(?:\s|$)([\s\S]*)",
    command=("رفع مشرف", plugin_category),
    info={
        "عمل الملف": "لاعطاء صلاحيات مشرف (رفعة في قائمة المشرفين)",
        "الوصف": "لرفع مشرف في المجموعة بصلاحيات\n ويلزمك جميع الصلاحيات او ان تكون المالك",
        "طريقة الاستخدام": [
            "{tr}رفع مشرف <الايدي/المعرف-اسم المستخدم-/بالرد ع رسالتة>",
            "{tr}رفع مشرف <الايدي/المعرف-اسم المستخدم-/بالرد ع رسالتة> <عنوان مخصص>",
        ],
    },
    groups_only=True,
    require_admin=True,
)
async def promote(event):
    "لترقية شخص في المجموعة"
    new_rights = ChatAdminRights(
        add_admins=False,
        invite_users=True,
        change_info=False,
        ban_users=True,
        delete_messages=True,
        pin_messages=True,
    )
    user, rank = await get_user_from_event(event)
    if not rank:
        rank = "Admin"
    if not user:
        return
    catevent = await edit_or_reply(event, "**⌔∮ جاري رفعه مشرف في المجموعة ✓**")
    try:
        await event.client(EditAdminRequest(event.chat_id, user.id, new_rights, rank))
    except BadRequestError:
        return await catevent.edit(NO_PERM)
    await catevent.edit("**⌔∮ تمت عملية ┆رفع مشرف┆ بنجاح ✓**")
    if BOTLOG:
        await event.client.send_message(
            BOTLOG_CHATID,
            f"**⌔∮ تمت عملية رفع المشرف┆👮‍♂️**\n\n⌔∮ المستخدم ↫ [{user.first_name}](tg://user?id={user.id})**\n**⌔∮ اسم المجموعة ✎ ↫** 『`{event.chat.title}`』\n**⌔∮ ايدي المجموعة 🆔 ↫** 「`{event.chat_id}`」",
        )


@catub.cat_cmd(
    pattern="^تنزيل مشرف(?:\s|$)([\s\S]*)",
    command=("تنزيل مشرف", plugin_category),
    info={
        "عمل الملف": "لإزالة شخص من قائمة المشرفين",
        "وصف الملف": "لتنزيل المشرف من المجموعة \n ويلزمك جميع الصلاحيات او ان تكون المالك",
        "طريقة الاستخدام": [
            "{tr}تنزيل مشرف <الايدي/المعرف-اسم المستخدم-/بالرد ع رسالتة>",
            "{tr}تنزيل مشرف <الايدي/المعرف-اسم المستخدم-/بالرد ع رسالتة> <عنوان مخصص>",
        ],
    },
    groups_only=True,
    require_admin=True,
)
async def demote(event):
    "لتجريد شخص من الاشراف في المجموعة"
    user, _ = await get_user_from_event(event)
    if not user:
        return
    catevent = await edit_or_reply(event, "**⌔∮ جاري تنزيل المشرف من المجموعة ツ**")
    newrights = ChatAdminRights(
        add_admins=None,
        invite_users=None,
        change_info=None,
        ban_users=None,
        delete_messages=None,
        pin_messages=None,
    )
    rank = "admin"
    try:
        await event.client(EditAdminRequest(event.chat_id, user.id, newrights, rank))
    except BadRequestError:
        return await catevent.edit(NO_PERM)
    await catevent.edit("**⌔∮ تمت عملية ┆تنزيل مشرف┆ بنجاح ✓**")
    if BOTLOG:
        await event.client.send_message(
            BOTLOG_CHATID,
            f"**⌔∮ تمت عملية ┆تنزيل مشرف┆👮‍♂️**\n\n**⌔∮ المستخدم ↫ [{user.first_name}](tg://user?id={user.id})**\n**⌔∮ اسم المجموعة ✎ ↫** 『`{event.chat.title}`』\n**⌔∮ ايدي المجموعة 🆔 ↫** 「`{event.chat_id}`」",
        )


@catub.cat_cmd(
    pattern="^حظر(?:\s|$)([\s\S]*)",
    command=("حظر", plugin_category),
    info={
        "عمل الملف": "حظر الاشخاص من المجموعة",
        "وصف الملف": "لحظر شخص من المجموعة ولا يمكن له الانظمام الا عند الغاء حظرة\nتحتاج الى صلاحية حظر لاستخدام هذا الامر",
        "طريقة الاستخدام": [
            "{tr}حظر <الايدي/المعرف-اسم المستخدم-/بالرد ع رسالتة>",
            "{tr}حظر <الايدي/المعرف-اسم المستخدم-/بالرد ع رسالتة> <سبب>",
        ],
    },
    groups_only=True,
    require_admin=True,
)
async def _ban_person(event):
    "لحظر شخص من المجموعة"
    user, reason = await get_user_from_event(event)
    if not user:
        return
    if user.id == event.client.uid:
        return await edit_delete(event, "**⌔∮ عذرًا لا يمكنني ┆حظر┆ نفسي! ✘**")
    catevent = await edit_or_reply(event, "**⌔∮ جاري حظر المستخدم ✘ ...**")
    try:
        await event.client(EditBannedRequest(event.chat_id, user.id, BANNED_RIGHTS))
    except BadRequestError:
        return await catevent.edit(NO_PERM)
    try:
        reply = await event.get_reply_message()
        if reply:
            await reply.delete()
    except BadRequestError:
        return await catevent.edit("**⌔∮سيتم حظره عندما يتم اعطائي الصلاحيات ✓**")
    if reason:
        await catevent.edit(
            f"**⌔∮ تم حظر المستخدم ↫ **{_format.mentionuser(user.first_name ,user.id)} ✓\n**⌔∮ السبب 📝↫** `{reason}`"
        )
    else:
        await catevent.edit(
            f"**⌔∮ تم حظر المستخدم ↫ **{_format.mentionuser(user.first_name ,user.id)} ✓"
        )
    if BOTLOG:
        if reason:
            await event.client.send_message(
                BOTLOG_CHATID,
                "**⌔∮ عملية الحظر ⛔️**\n\n"
                f"**⌔∮ تم حظر المستخدم ↫ ** [{user.first_name}](tg://user?id={user.id}) ⛔️\n**⌔∮ اسم المجموعة ✎ ↫** 『`{event.chat.title}`』\n**⌔∮ ايدي المجموعة 🆔 ↫** 「`{event.chat_id}`」\n**⌔∮ السبب 📝 ↫** `{reason}`",
            )
        else:
            await event.client.send_message(
                BOTLOG_CHATID,
                "**⌔∮ عملية الحظر ⛔️**\n\n"
                f"**⌔∮ تم حظر المستخدم ↫ ** [{user.first_name}](tg://user?id={user.id}) ⛔️\n**⌔∮ اسم المجموعة ✎ ↫** 『`{event.chat.title}`』\n**⌔∮ ايدي المجموعة 🆔 ↫** 「`{event.chat_id}`」",
            )


@catub.cat_cmd(
    pattern="^الغاء حظر(?:\s|$)([\s\S]*)",
    command=("الغاء حظر", plugin_category),
    info={
        "عمل الملف": "الغاء حظر الاشخاص من المجموعة",
        "وصف الملف": "لالغاء حظر شخص من المجموعة\nتحتاج الى صلاحيات الحظر لاستخدام هذا الامر",
        "طريقة الاستخدام": [
            "{tr}الغاء حظر <الايدي/المعرف-اسم المستخدم-/بالرد ع رسالتة>",
            "{tr}الغاء حظر <الايدي/المعرف-اسم المستخدم-/بالرد ع رسالتة> <سبب>",
        ],
    },
    groups_only=True,
    require_admin=True,
)
async def nothanos(event):
    "لالغاء الحظر من شخص في المجموعة"
    user, _ = await get_user_from_event(event)
    if not user:
        return
    catevent = await edit_or_reply(event, "**⌔∮ جاري الغاء حظر المستخدم ✘ ...**")
    try:
        await event.client(EditBannedRequest(event.chat_id, user.id, UNBAN_RIGHTS))
        await catevent.edit(
            f"**⌔∮ تم الغاء حظر المستخدم ↫ ** [{user.first_name}](tg://user?id={user.id}) ✓\n**⌔∮ اسم المجموعة ✎ ↫** 『`{event.chat.title}`』\n**⌔∮ ايدي المجموعة 🆔 ↫** 「`{event.chat_id}`」"
        )
        if BOTLOG:
            await event.client.send_message(
                BOTLOG_CHATID,
                "**⌔∮ عملية رفع الحظر ☟**\n\n"
                f"**⌔∮ تم الغاء حظر المستخدم ↫ ** [{user.first_name}](tg://user?id={user.id}) ✓\n**⌔∮ اسم المجموعة ✎ ↫** 『`{event.chat.title}`』\n**⌔∮ ايدي المجموعة 🆔 ↫** 「`{event.chat_id}`」",
            )
    except UserIdInvalidError:
        await catevent.edit("**⌔∮ هذه العملية تم الغاؤها سابقًا!**")
    except Exception as e:
        await catevent.edit(f"**▾∮ هنالك خطأ ... تحقق ↶**\n`{e}`")


@catub.cat_cmd(incoming=True)
async def watcher(event):
    if is_muted(event.sender_id, event.chat_id):
        try:
            await event.delete()
        except Exception as e:
            LOGS.info(str(e))


@catub.cat_cmd(
    pattern="^كتم(?:\s|$)([\s\S]*)",
    command=("كتم", plugin_category),
    info={
        "عمل الملف": "لإيقاف إرسال الرسائل من المستخدم",
        "وصف الملف": "اذا كنت مالك المجموعة سيتم تنزيلة من المشرفين والغاء اذن الكتابة في المجموعة\n اذا كان مشرفًا فعند كتمة سيحذف جميع ما يكتبة\nتحتاج الى صلاحيات حذف الرسائل لاستخدام هذا الامر",
        "طريقة الاستخدام": [
            "{tr}كتم <الايدي/المعرف-اسم المستخدم-/بالرد ع رسالتة>",
            "{tr}كتم <الايدي/المعرف-اسم المستخدم-/بالرد ع رسالتة> <سبب>",
        ],
    },  # sourcery no-metrics
)
async def startmute(event):
    "لمنع شخص من الكتابة في المجموعة"
    if event.is_private:
        await event.edit("**⌔∮ قد تحدث مشاكل او اخطاء غير متوقعة! ** ")
        await sleep(2)
        await event.get_reply_message()
        await event.client(GetFullUserRequest(event.chat_id))
        if is_muted(event.chat_id, event.chat_id):
            return await event.edit("**⌔∮ تم كتم المستخدم مسبقًا 🔇**")
        if event.chat_id == catub.uid:
            return await edit_delete(event, "**⌔∮ عذرًا لا يمكنني ┆كتم┆ نفسي! ✘**")
        try:
            mute(event.chat_id, event.chat_id)
        except Exception as e:
            await event.edit(f"**▾∮ هنالك خطأ ... تحقق ↶**\n`{str(e)}`")
        else:
            await event.edit("**▾∮ تم كتم هذا المستخدم بنجاح 🚫**")
        if BOTLOG:
            await event.client.send_message(
                BOTLOG_CHATID,
                "**▾∮ عملية الكتم 🔇**\n\n"
                f"**⌔∮ تم كتم المستخدم 🔇 ↫ ** [{user.first_name}](tg://user?id={user.id}) بنجاح ✓\n**⌔∮ اسم المجموعة ✎ ↫** 『`{event.chat.title}`』\n**⌔∮ ايدي المجموعة 🆔 ↫** 「`{event.chat_id}`」",
            )
    else:
        chat = await event.get_chat()
        admin = chat.admin_rights
        creator = chat.creator
        if not admin and not creator:
            return await edit_or_reply(
                event, "**▾∮ عذرًا يلزمك صلاحيات لتنفيذ هذا الامر ❗️**"
            )
        user, reason = await get_user_from_event(event)
        if not user:
            return
        if user.id == catub.uid:
            return await edit_or_reply(event, "**⌔∮ عذرًا لا يمكنني ┆كتم┆ نفسي! ✘**")
        if is_muted(user.id, event.chat_id):
            return await edit_or_reply("**⌔∮ تم كتم المستخدم مسبقًا 🔇 ")
        result = await event.client(
            functions.channels.GetParticipantRequest(event.chat_id, user.id)
        )
        try:
            if result.participant.banned_rights.send_messages:
                return await edit_or_reply(event, "**⌔∮ تم كتم المستخدم مسبقًا 🔇 ")
        except AttributeError:
            pass
        except Exception as e:
            return await edit_or_reply(
                event, f"**▾∮ هنالك خطأ ... تحقق ↶**\n`{str(e)}`", 10
            )
        try:
            await event.client(EditBannedRequest(event.chat_id, user.id, MUTE_RIGHTS))
        except UserAdminInvalidError:
            if "admin_rights" in vars(chat) and vars(chat)["admin_rights"] is not None:
                if chat.admin_rights.delete_messages is not True:
                    return await edit_or_reply(
                        event,
                        "**▾∮ عذرًا يلزمك صلاحية حذف الرسائل❗️**",
                    )
            elif "creator" not in vars(chat):
                return await edit_or_reply(
                    event, "**▾∮ عذرًا يلزمك صلاحيات لتنفيذ هذا الامر ❗️**"
                )
            mute(user.id, event.chat_id)
        except Exception as e:
            return await edit_or_reply(
                event, f"**▾∮ هنالك خطأ ... تحقق ↶**\n`{str(e)}`", 10
            )
        if reason:
            await edit_or_reply(
                event,
                f"**⌔∮ تم كتم المستخدم 🔇 ↫ **{_format.mentionuser(user.first_name ,user.id)} ✓\n**⌔∮ السبب 📝↫** `{reason}`",
            )
        else:
            await edit_or_reply(
                event,
                f"**⌔∮ تم كتم المستخدم 🔇 ↫ **{_format.mentionuser(user.first_name ,user.id)} ✓\n",
            )
        if BOTLOG:
            await event.client.send_message(
                BOTLOG_CHATID,
                "**▾∮ عملية الكتم 🔇**\n\n"
                f"**⌔∮ تم كتم المستخدم 🔇 ↫ ** [{user.first_name}](tg://user?id={user.id}) بنجاح ✓\n**⌔∮ اسم المجموعة ✎ ↫** 『`{event.chat.title}`』\n**⌔∮ ايدي المجموعة 🆔 ↫** 「`{event.chat_id}`」",
            )


@catub.cat_cmd(
    pattern="^الغاء كتم(?:\s|$)([\s\S]*)",
    command=("الغاء كتم", plugin_category),
    info={
        "عمل الملف": "لتفعيل إرسال الرسائل على المستخدم",
        "وصف الملف": "تحتاج الى صلاحيات ادارة المجموعة لاستخدام هذا الامر",
        "طريقة الاستخدام": [
            "{tr}الغاء كتم <الايدي/المعرف-اسم المستخدم-/بالرد ع رسالتة>",
            "{tr}الغاء كتم <الايدي/المعرف-اسم المستخدم-/بالرد ع رسالتة> <سبب>",
        ],
    },
)
async def endmute(event):
    "لالغاء كتم المستخدم (منع الرسائل) من المجموعة"
    if event.is_private:
        await event.edit("**▾┇ سيتم الغاء كتمه من الخاص ㋡** ")
        await sleep(1)
        await event.client(GetFullUserRequest(event.chat_id))
        if not is_muted(event.chat_id, event.chat_id):
            return await event.edit("**▾┇ المستخدم لم يمنع من الكتابة في المجموعة 🔈 **")
        try:
            unmute(event.chat_id, event.chat_id)
        except Exception as e:
            await event.edit(f"**▾┇ هنالك خطأ ... تحقق ↶**\n`{str(e)}`")
        else:
            await event.edit(
                await event.edit("**▾┇ تم الغاء كتم هذا المستخدم بنجاح 🔈**")
            )
        if BOTLOG:
            await event.client.send_message(
                BOTLOG_CHATID,
                "**▾∮ عملية الغاء الكتم 🔈**\n\n"
                f"**▾┇ تم الغاء كتم المستخدم 🔈 ↫ ** [{user.first_name}](tg://user?id={user.id}) بنجاح ✓\n**▾┇ اسم المجموعة ✎ ↫** 『`{event.chat.title}`』\n**▾┇ ايدي المجموعة 🆔 ↫** 「`{event.chat_id}`」",
            )
    else:
        user, _ = await get_user_from_event(event)
        if not user:
            return
        try:
            if is_muted(user.id, event.chat_id):
                unmute(user.id, event.chat_id)
            else:
                result = await event.client(
                    functions.channels.GetParticipantRequest(event.chat_id, user.id)
                )
                if result.participant.banned_rights.send_messages:
                    await event.client(
                        EditBannedRequest(event.chat_id, user.id, UNBAN_RIGHTS)
                    )
        except AttributeError:
            return await edit_or_reply(
                event, "**⌔∮ المستخدم بالفعل يمكنه التحدث في المجموعة 🔈 "
            )
        except Exception as e:
            return await edit_or_reply(
                event, f"**▾∮ هنالك خطأ ... تحقق ↶**\n`{str(e)}`", 10
            )
        await edit_or_reply(
            event,
            f"**⌔∮ تم الغاء كتم المستخدم 🔈 ↫ **{_format.mentionuser(user.first_name ,user.id)} ✓\n",
        )
        if BOTLOG:
            await event.client.send_message(
                BOTLOG_CHATID,
                "**▾∮ عملية الغاء الكتم 🔈**\n\n"
                f"**⌔∮ تم الغاء كتم المستخدم 🔈 ↫ ** [{user.first_name}](tg://user?id={user.id}) بنجاح ✓\n**⌔∮ اسم المجموعة ✎ ↫** 『`{event.chat.title}`』\n**⌔∮ ايدي المجموعة 🆔 ↫** 「`{event.chat_id}`」",
            )


@catub.cat_cmd(
    pattern="^طرد(?:\s|$)([\s\S]*)",
    command=("^طرد", plugin_category),
    info={
        "عمل الملف": "لطرد الاشخاص من المجموعة وحتى نفسك!",
        "وصف الملف": "لطرد شخص من المجموعة ولا يمكن له الانظمام الا عند الغاء حظرة\nتحتاج الى صلاحية حظر لاستخدام هذا الامر",
        "طريقة الاستخدام": [
            "{tr}طرد <الايدي/المعرف-اسم المستخدم-/بالرد ع رسالتة>",
            "{tr}طرد <الايدي/المعرف-اسم المستخدم-/بالرد ع رسالتة> <سبب>",
        ],
    },
    groups_only=True,
    require_admin=True,
)
async def endmute(event):
    "لطرد شخص من المجموعة"
    user, reason = await get_user_from_event(event)
    if not user:
        return
    catevent = await edit_or_reply(event, "**⌔∮ جاري ┆طرد┆ المستخدم ✘ ...**")
    try:
        await event.client.kick_participant(event.chat_id, user.id)
    except Exception as e:
        return await catevent.edit(NO_PERM + f"\n{str(e)}")
    if reason:
        await catevent.edit(
            f"**⌔∮ تم ┆طرد┆ المستخدم 🚷 ↫ **『 [{user.first_name}](tg://user?id={user.id}) 』\n**⌔∮ السبب 📝↫** 「`{reason}`」"
        )
    else:
        await catevent.edit(
            f"**⌔∮ تم ┆طرد┆ المستخدم 🚷 ↫ **『 [{user.first_name}](tg://user?id={user.id}) 』❗️"
        )
    if BOTLOG:
        await event.client.send_message(
            BOTLOG_CHATID,
            "**⌔∮ عملية الطرد 🚷**\n\n"
            f"**⌔∮ تم┆طرد┆المستخدم 🚷 ↫ ** 『[{user.first_name}](tg://user?id={user.id})』\n**⌔∮ اسم المجموعة ✎ ↫** 『`{event.chat.title}`』\n**⌔∮ ايدي المجموعة 🆔 ↫** 「`{event.chat_id}`」\n**⌔∮ السبب 🆘 ↫** `「{reason}」`",
        )


@catub.cat_cmd(
    pattern="^تثبيت( بالتنبيه|$)",
    command=("تثبيت", plugin_category),
    info={
        "عمل الملف": "لـ تثبيت الرسائل في المجموعة",
        "وصف الملف": "قم بالرد ع الرسالة وبعدها اكتب الامر\
        \n* تحتاج الى صلاحية التثبيت لتنفيذ الامر.",
        "الخيارات": {
            "بالتنبيه": "لايصال تنبيه للجميع بدون هذا الامر\n سيتم تثبيته بصمت (بدون تنبيه)"
        },
        "طريقة الاستخدام": [
            "{tr}تثبيت <بالرد على الرسالة>",
            "{tr}تثبيت بالتنبيه <بالرد على الرسالة>",
        ],
    },
)
async def pin(event):
    "لتثبيت رسالة في المجموعة"
    to_pin = event.reply_to_msg_id
    if not to_pin:
        return await edit_delete(event, "**⌔∮ قم بالرد ع الرسالة ليتم تثبيتها! 📌**", 5)
    options = event.pattern_match.group(1)
    is_silent = bool(options)
    try:
        await event.client.pin_message(event.chat_id, to_pin, notify=is_silent)
    except BadRequestError:
        return await edit_delete(event, NO_PERM, 5)
    except Exception as e:
        return await edit_delete(event, f"**▾∮ هنالك خطأ ... تحقق ↶**\n`{str(e)}`", 5)
    await edit_delete(event, "**⌔∮ تم ┆تثبيت┆الرسالة بنجاح 📌**", 3)
    if BOTLOG and not event.is_private:
        await event.client.send_message(
            BOTLOG_CHATID,
            f"**⌔∮ عملية┆تثبيت┆رسالة في المجموعة 📌**\n\n**⌔∮ اسم المجموعة ✎ ↫** 『`{event.chat.title}`』\n**⌔∮ ايدي المجموعة 🆔 ↫** 「`{event.chat_id}`」",
        )


@catub.cat_cmd(
    pattern="^الغاء تثبيت( الكل|$)",
    command=("^الغاء تثبيت", plugin_category),
    info={
        "عمل الملف": "لـ الغاء تثبيت الرسائل المثبتة في المجموعة",
        "وصف الملف": "قم بالرد ع الرسالة وبعدها اكتب الامر\n او اكتب (الغاء تثبيت الكل) بدون رد\
        \n* تحتاج الى صلاحية التثبيت لتنفيذ الامر.",
        "الخيارات": {
            "الكل": "لالغاء تثبيت جميع الرسائل المثبتة\* تحتاج الى صلاحية التثبيت لتنفيذ الامر."
        },
        "طريقة الاستخدام": [
            "{tr}الغاء تثبيت <بالرد على الرسالة>",
            "{tr}الغاء تثبيت الكل <بالرد على الرسالة>",
        ],
    },
)
async def pin(event):
    "لالغاء تثبيت الرسائل في المجموعة"
    to_unpin = event.reply_to_msg_id
    options = (event.pattern_match.group(1)).strip()
    if not to_unpin and options != "الكل":
        return await edit_delete(
            event,
            "**⌔∮ قم بالرد ع الرسالة المُراد الغاء تثبيتها!**\n**↫ او قم بالغاء جميع الرسائل المثبتة ✂️**",
            5,
        )
    try:
        if to_unpin and not options:
            await event.client.unpin_message(event.chat_id, to_unpin)
        elif options == "الكل":
            await event.client.unpin_message(event.chat_id)
        else:
            return await edit_delete(
                event,
                "**⌔∮ قم بالرد ع الرسالة المُراد الغاء تثبيتها!**\n**↫ او قم بالغاء جميع الرسائل المثبتة ✂️**",
                5,
            )
    except BadRequestError:
        return await edit_delete(event, NO_PERM, 5)
    except Exception as e:
        return await edit_delete(event, f"`{str(e)}`", 5)
    await edit_delete(event, "**⌔∮ تم ┆الغاء تثبيت┆الرسالة بنجاح 📌**", 3)
    if BOTLOG and not event.is_private:
        await event.client.send_message(
            BOTLOG_CHATID,
            f"**⌔∮ عملية┆الغاء تثبيت┆رسالة  ✂️**\n\n**⌔∮ اسم المجموعة ✎ ↫** 『`{event.chat.title}`』\n**⌔∮ ايدي المجموعة 🆔 ↫** 「`{event.chat_id}`」",
        )


@catub.cat_cmd(
    pattern="^احداث( جلب)?(?: |$)(\d*)?",
    command=("احداث", plugin_category),
    info={
        "عمل الملف": "لمشاهدة وجلب الاحداث الاخيرة في المجموعة",
        "وصف الملف": "للتحقق وجلب الرسائل المحذوفة مؤخرًا في المجموعة ، ستظهر افتراضيًا 5. يمكنك الحصول على من 1 إلى 100 رسالة.",
        "الاوامر": {"جلب": "باستخدام هذا الامر ترسل لك الوسائط والرسائل بدون حذف"},
        "طريقة الاستخدام": [
            "{tr}احداث <عدد>",
            "{tr}احداث جلب <عدد>",
        ],
        "امثلة": [
            "{tr}احداث 10 (لرؤية 10 رسائل من الاحداث بشكل مؤقت وتحذف)",
            "{tr} احداث جلب 10 (لجلب 10 رسائل بدون حذف)",
        ],
    },
    groups_only=True,
    require_admin=True,
)
async def _iundlt(event):  # sourcery no-metrics
    "للتحقق ولجلب الاحداث الاخيرة في المجموعة"
    catevent = await edit_or_reply(event, "**⌔∮ جاري البحث عن ┆احداث┆المجموعة 🗑**")
    flag = event.pattern_match.group(1)
    if event.pattern_match.group(2) != "":
        lim = int(event.pattern_match.group(2))
        if lim > 100:
            lim = int(100)
        if lim <= 0:
            lim = int(1)
    else:
        lim = int(5)
    adminlog = await event.client.get_admin_log(
        event.chat_id, limit=lim, edit=False, delete=True
    )
    deleted_msg = f"**⌔∮ اخر 「{lim}」 رسائل محوذفة من المجموعة 🗑 ↶**"
    if not flag:
        for msg in adminlog:
            ruser = (
                await event.client(GetFullUserRequest(msg.old.from_id.user_id))
            ).user
            _media_type = media_type(msg.old)
            if _media_type is None:
                deleted_msg += f"\n**⌔ الرسالة ☜**『 {msg.old.message} 』\n**⌔∮ مُرسلة من ↫** 「 {_format.mentionuser(ruser.first_name ,ruser.id)} 」"
            else:
                deleted_msg += f"**⌔ الرسالة ☜** 『 {_media_type} 』\n**⌔∮ مُرسلة من ↫** 「 {_format.mentionuser(ruser.first_name ,ruser.id)} 」"
        await edit_or_reply(catevent, deleted_msg)
    else:
        main_msg = await edit_or_reply(catevent, deleted_msg)
        for msg in adminlog:
            ruser = (
                await event.client(GetFullUserRequest(msg.old.from_id.user_id))
            ).user
            _media_type = media_type(msg.old)
            if _media_type is None:
                await main_msg.reply(
                    f"**⌔ الرسالة ☜**『 {msg.old.message} 』\n**⌔∮ مُرسلة من ↫** 「 {_format.mentionuser(ruser.first_name ,ruser.id)} 」"
                )
            else:
                await main_msg.reply(
                    f"**⌔ الرسالة ☜**『 {msg.old.message} 』\n**⌔∮ مُرسلة من ↫** 「 {_format.mentionuser(ruser.first_name ,ruser.id)} 」",
                    file=msg.old.media,
                )
