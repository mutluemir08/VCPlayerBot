#!/usr/bin/env python3
# Copyright (C) @subinps
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from utils import LOGGER
from youtube_search import YoutubeSearch
from contextlib import suppress
from pyrogram.types import Message
from yt_dlp import YoutubeDL
from datetime import datetime
from pyrogram import filters
from config import Config
from PTN import parse
import re
from utils import (
    add_to_db_playlist, 
    clear_db_playlist, 
    delete_messages, 
    download, 
    get_admins, 
    get_duration,
    is_admin, 
    get_buttons, 
    get_link, 
    import_play_list, 
    is_audio, 
    leave_call, 
    play, 
    get_playlist_str, 
    send_playlist, 
    shuffle_playlist, 
    start_stream, 
    stream_from_link, 
    chat_filter,
    c_play,
    is_ytdl_supported
)
from pyrogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton
    )
from pyrogram.errors import (
    MessageIdInvalid, 
    MessageNotModified,
    UserNotParticipant,
    PeerIdInvalid,
    ChannelInvalid
    )
from pyrogram import (
    Client, 
    filters
    )


admin_filter=filters.create(is_admin) 

@Client.on_message(filters.command(["play", "fplay", f"play@{Config.BOT_USERNAME}", f"fplay@{Config.BOT_USERNAME}"]) & chat_filter)
async def add_to_playlist(_, message: Message):
    with suppress(MessageIdInvalid, MessageNotModified):
        admins = await get_admins(Config.CHAT)
        if Config.ADMIN_ONLY:
            if not (message.from_user is None and message.sender_chat or message.from_user.id in admins):
                k=await message.reply_sticker("CAADBQADsQIAAtILIVYld1n74e3JuQI")
                await delete_messages([message, k])
                return
        type=""
        yturl=""
        ysearch=""
        url=""
        if message.command[0] == "fplay":
            if not (message.from_user is None and message.sender_chat or message.from_user.id in admins):
                k=await message.reply("Bu komut sadece yöneticiler içindir.")
                await delete_messages([message, k])
                return
        msg = await message.reply_text("⚡️ **Alınan dosya kontrol ediliyor..**")
        if message.reply_to_message and message.reply_to_message.video:
            await msg.edit("⚡️ **Medya Kontrol Ediliyor...**")
            type='video'
            m_video = message.reply_to_message.video       
        elif message.reply_to_message and message.reply_to_message.document:
            await msg.edit("⚡️ **Medya Kontrol Ediliyor...**")
            m_video = message.reply_to_message.document
            type='video'
            if not "video" in m_video.mime_type:
                return await msg.edit("Verilen Dosya Bulunamadı")
        elif message.reply_to_message and message.reply_to_message.audio:
            #if not Config.IS_VIDEO:
                #return await message.reply("Play from audio file is available only if Video Mode if turned off.\nUse /settings to configure ypur player.")
            await msg.edit("⚡️ **Medya Kontrol Ediliyor...**")
            type='audio'
            m_video = message.reply_to_message.audio       
        else:
            if message.reply_to_message and message.reply_to_message.text:
                query=message.reply_to_message.text
            elif " " in message.text:
                text = message.text.split(" ", 1)
                query = text[1]
            else:
                await msg.edit("Oynatılacak bir şey vermilmedi. Bir videoya, bir youtube bağlantısına veya doğrudan bir bağlantıya yanıt verin.")
                await delete_messages([message, msg])
                return
            regex = r"^(?:https?:\/\/)?(?:www\.)?youtu\.?be(?:\.com)?\/?.*(?:watch|embed)?(?:.*v=|v\/|\/)([\w\-_]+)\&?"
            match = re.match(regex,query)
            if match:
                type="youtube"
                yturl=query
            elif query.startswith("http"):
                try:
                    has_audio_ = await is_audio(query)
                except:
                    has_audio_ = False
                    LOGGER.error("Ses özellikleri zaman içinde alınamıyor.")
                if has_audio_:
                    try:
                        dur=await get_duration(query)
                    except:
                        dur=0
                    if dur == 0:
                        await msg.edit("Bu bir canlı yayındır, /stream komutunu kullanın.")
                        await delete_messages([message, msg])
                        return 
                    type="direct"
                    url=query
                else:
                    if is_ytdl_supported(query):
                        type="ytdl_s"
                        url=query
                    else:
                        await msg.edit("Bu geçersiz bir bağlantı, bana doğrudan bir bağlantı veya bir youtube bağlantısı sağlayın.")
                        await delete_messages([message, msg])
                        return
            else:
                type="query"
                ysearch=query
        if not message.from_user is None:
            user=f"[{message.from_user.first_name}](tg://user?id={message.from_user.id})"
            user_id = message.from_user.id
        else:
            user="Anonymous"
            user_id = "anonymous_admin"
        now = datetime.now()
        nyav = now.strftime("%d-%m-%Y-%H:%M:%S")
        if type in ["video", "audio"]:
            if type == "audio":
                if m_video.title is None:
                    if m_video.file_name is None:
                        title_ = "Music"
                    else:
                        title_ = m_video.file_name
                else:
                    title_ = m_video.title
                if m_video.performer is not None:
                    title = f"{m_video.performer} - {title_}"
                else:
                    title=title_
                unique = f"{nyav}_{m_video.file_size}_audio"
            else:
                title=m_video.file_name
                unique = f"{nyav}_{m_video.file_size}_video"
                if Config.PTN:
                    ny = parse(title)
                    title_ = ny.get("title")
                    if title_:
                        title = title_
            file_id=m_video.file_id
            if title is None:
                title = 'Music'
            data={1:title, 2:file_id, 3:"telegram", 4:user, 5:unique}
            if message.command[0] == "fplay":
                pla = [data] + Config.playlist
                Config.playlist = pla
            else:
                Config.playlist.append(data)
            await add_to_db_playlist(data)        
            await msg.edit("Medya Çalma Listesine Eklendi.")
        elif type in ["youtube", "query", "ytdl_s"]:
            if type=="youtube":
                await msg.edit("⚡️ **Youtube Üzerinden Video Alınıyor...**")
                url=yturl
            elif type=="query":
                try:
                    await msg.edit("⚡️ **Youtube Üzerinden Video Alınıyor...**")
                    ytquery=ysearch
                    results = YoutubeSearch(ytquery, max_results=1).to_dict()
                    url = f"https://youtube.com{results[0]['url_suffix']}"
                    title = results[0]["title"][:40]
                except Exception as e:
                    await msg.edit(
                        "Şarkı bulunamadı \n İnline modda tekrar deneyin.."
                    )
                    LOGGER.error(str(e), exc_info=True)
                    await delete_messages([message, msg])
                    return
            elif type == "ytdl_s":
                url=url
            else:
                return
            ydl_opts = {
                "quite": True,
                "geo-bypass": True,
                "nocheckcertificate": True
            }
            ydl = YoutubeDL(ydl_opts)
            try:
                info = ydl.extract_info(url, False)
            except Exception as e:
                LOGGER.error(e, exc_info=True)
                await msg.edit(
                    f"Youtube hatası ❌\nError:- {e}"
                    )
                LOGGER.error(str(e))
                await delete_messages([message, msg])
                return
            if type == "ytdl_s":
                title = "Music"
                try:
                    title = info['title']
                except:
                    pass
            else:
                title = info["title"]
                if info['duration'] is None:
                    await msg.edit("Bu bir canlı yayındır, /stream komutunu kullanın.")
                    await delete_messages([message, msg])
                    return 
            data={1:title, 2:url, 3:"youtube", 4:user, 5:f"{nyav}_{user_id}"}
            if message.command[0] == "fplay":
                pla = [data] + Config.playlist
                Config.playlist = pla
            else:
                Config.playlist.append(data)
            await add_to_db_playlist(data)
            await msg.edit(f"[{title}]({url}) added to playist", disable_web_page_preview=True)
        elif type == "direct":
            data={1:"Music", 2:url, 3:"url", 4:user, 5:f"{nyav}_{user_id}"}
            if message.command[0] == "fplay":
                pla = [data] + Config.playlist
                Config.playlist = pla
            else:
                Config.playlist.append(data)
            await add_to_db_playlist(data)        
            await msg.edit("Bağlantı Çalma Listesine Eklendi")
        if not Config.CALL_STATUS \
            and len(Config.playlist) >= 1:
            await msg.edit("İndiriliyor ve İşleniyor...")
            await download(Config.playlist[0], msg)
            await play()
        elif (len(Config.playlist) == 1 and Config.CALL_STATUS):
            await msg.edit("İndiriliyor ve İşleniyor...")
            await download(Config.playlist[0], msg)  
            await play()
        elif message.command[0] == "fplay":
            await msg.edit("İndiriliyor ve İşleniyor...")
            await download(Config.playlist[0], msg)  
            await play()
        else:
            await send_playlist()  
        await msg.delete()
        pl=await get_playlist_str()
        if message.chat.type == "private":
            await message.reply(pl, reply_markup=await get_buttons() ,disable_web_page_preview=True)       
        elif not Config.LOG_GROUP and message.chat.type == "supergroup":
            if Config.msg.get('playlist') is not None:
                await Config.msg['playlist'].delete()
            Config.msg['playlist']=await message.reply(pl, disable_web_page_preview=True, reply_markup=await get_buttons())    
            await delete_messages([message])  
        for track in Config.playlist[:2]:
            await download(track)


@Client.on_message(filters.command(["leave", f"leave@{Config.BOT_USERNAME}"]) & admin_filter & chat_filter)
async def leave_voice_chat(_, m: Message):
    if not Config.CALL_STATUS:        
        k=await m.reply("Sesli sohbet aktif değil")
        await delete_messages([m, k])
        return
    await leave_call()
    k=await m.reply("Asistan Sesli Sohbetten Ayrıldı.")
    await delete_messages([m, k])



@Client.on_message(filters.command(["shuffle", f"shuffle@{Config.BOT_USERNAME}"]) & admin_filter & chat_filter)
async def shuffle_play_list(client, m: Message):
    if not Config.CALL_STATUS:
        k = await m.reply("Sesli Sohbet Aktif Değil.")
        await delete_messages([m, k])
        return
    else:
        if len(Config.playlist) > 2:
            k=await m.reply_text(f"Çalma Listesi Karıştırıldı.")
            await shuffle_playlist()
            await delete_messages([m, k])            
        else:
            k=await m.reply_text(f"3'ten az şarkı içeren çalma listesini karıştıramazsınız.")
            await delete_messages([m, k])


@Client.on_message(filters.command(["clearplaylist", f"clearplaylist@{Config.BOT_USERNAME}"]) & admin_filter & chat_filter)
async def clear_play_list(client, m: Message):
    if not Config.playlist:
        k = await m.reply("Çalma Listesi Şuan Boş.")  
        await delete_messages([m, k])
        return
    Config.playlist.clear()
    k=await m.reply_text(f"Çalma Listesi Temizlendi.")
    await clear_db_playlist(all=True)
    if Config.IS_LOOP \
        and not (Config.YPLAY or Config.CPLAY):
        await start_stream()
    else:
        await leave_call()
    await delete_messages([m, k])



@Client.on_message(filters.command(["cplay", f"cplay@{Config.BOT_USERNAME}"]) & admin_filter & chat_filter)
async def channel_play_list(client, m: Message):
    with suppress(MessageIdInvalid, MessageNotModified):
        k=await m.reply("Kanal oynatma için ayarlandı..")
        if " " in m.text:
            you, me = m.text.split(" ", 1)
            if me.startswith("-100"):
                try:
                    me=int(me)
                except:
                    await k.edit("Verilen Grup ID bulunamadı")
                    await delete_messages([m, k])
                    return
                try:
                    await client.get_chat_member(int(me), Config.USER_ID)
                except (ValueError, PeerIdInvalid, ChannelInvalid):
                    LOGGER.error(f"Verilen Kanal Yanlış yada @{Config.BOT_USERNAME} yönetici değil.", exc_info=True)
                    await k.edit(f"Verilen Kanal Yanlış yada @{Config.BOT_USERNAME} yönetici değil.", Kanal gizli değilse lütfen kanalın kullanıcı adını belirtin.")
                    await delete_messages([m, k])
                    return
                except UserNotParticipant:
                    LOGGER.error("Verilen kanal özeldir ve KULLANICI hesabı kanala üye değildir.")
                    await k.edit("Verilen kanal özeldir ve KULLANICI hesabı kanala üye değildir.")
                    await delete_messages([m, k])
                    return
                except Exception as e:
                    LOGGER.error(f"Kanal hakkında veri alınırken hatalar oluştu - {e}", exc_info=True)
                    await k.edit(f"Yanlış birşeyler var- {e}")
                    await delete_messages([m, k])
                    return
                await k.edit("Kanaldan dosya arama, kanaldaki dosya sayısına bağlı olarak biraz zaman alabilir..")
                st, msg = await c_play(me)
                if st == False:
                    await m.edit(msg)
                else:
                    await k.edit(f"Başarıyla {msg} dosyaları playliste eklendi.")
            elif me.startswith("@"):
                me = me.replace("@", "")
                try:
                    chat=await client.get_chat(me)
                except Exception as e:
                    LOGGER.error(f"Kanal hakkında bilgi alınırken hatalar oluştu - {e}", exc_info=True)
                    await k.edit(f"Kanal hakkında bilgi alınırken hatalar oluştu - {e}")
                    await delete_messages([m, k])
                    return
                await k.edit("Kanaldan dosya aramak, kanaldaki dosya sayısına bağlı olarak biraz zaman alabilir.")
                st, msg=await c_play(me)
                if st == False:
                    await k.edit(msg)
                    await delete_messages([m, k])
                else:
                    await k.edit(f"Başarıyla {msg} dosyaları {chat.title} playliste eklendi")
                    await delete_messages([m, k])
            else:
                await k.edit("Verilen kanal geçersiz. Özel kanallarda -100 ile, genel kanallarda ise -100 ile başlamalıdır. @\nExamples - `/cplay @VCPlayerFiles or /cplay -100125369865\n\nÖzel kanal için hem bot hem de KULLANICI hesabı kanalın üyesi olmalıdır.")
                await delete_messages([m, k])
        else:
            await k.edit("Kanal verilmedi. Dosyaları oynatmam gereken bir kanal kimliği veya kullanıcı adı verin. \nÖzel kanallarda -100 ile, genel kanallarda ise -100 ile başlamalıdır. @\nExamples - `/cplay @VCPlayerFiles or /cplay -100125369865\n\nFor private channel, both bot and the USER account should be members of channel.")
            await delete_messages([m, k])



@Client.on_message(filters.command(["yplay", f"yplay@{Config.BOT_USERNAME}"]) & admin_filter & chat_filter)
async def yt_play_list(client, m: Message):
    with suppress(MessageIdInvalid, MessageNotModified):
        if m.reply_to_message is not None and m.reply_to_message.document:
            if m.reply_to_message.document.file_name != "YouTube_PlayList.json":
                k=await m.reply("Geçersiz Oynatma Listesi dosyası verildi. Bir çalma listesi dosyası almak için @GetPlayListBot'u kullanın veya @DumpPlaylist'te bir çalma listesi arayın.")
                await delete_messages([m, k])
                return
            ytplaylist=await m.reply_to_message.download()
            status=await m.reply("Oynatma listesinden ayrıntılar alınıyor.")
            n=await import_play_list(ytplaylist)
            if not n:
                await status.edit("Oynatma listesi içe aktarılırken hata oluştu.")
                await delete_messages([m, status])
                return
            if Config.SHUFFLE:
                await shuffle_playlist()
            pl=await get_playlist_str()
            if m.chat.type == "private":
                await status.edit(pl, disable_web_page_preview=True, reply_markup=await get_buttons())        
            elif not Config.LOG_GROUP and m.chat.type == "supergroup":
                if Config.msg.get("playlist") is not None:
                    await Config.msg['playlist'].delete()
                Config.msg['playlist']=await status.edit(pl, disable_web_page_preview=True, reply_markup=await get_buttons())
                await delete_messages([m])
            else:
                await delete_messages([m, status])
        else:
            k=await m.reply("Oynatma Listesi dosyası verilmedi. Bir çalma listesi dosyası almak için @GetPlayListBot'u kullanın veya @DumpPlaylist'te bir çalma listesi arayın.")
            await delete_messages([m, k])


@Client.on_message(filters.command(["stream", f"stream@{Config.BOT_USERNAME}"]) & admin_filter & chat_filter)
async def stream(client, m: Message):
    with suppress(MessageIdInvalid, MessageNotModified):
        msg=await m.reply("Medya Kontrol Ediliyor.")
        if m.reply_to_message and m.reply_to_message.text:
            link=m.reply_to_message.text
        elif " " in m.text:
            text = m.text.split(" ", 1)
            link = text[1]
        else:
            k = await msg.edit("Akış için bir bağlantı verin!")
            await delete_messages([m, k])
            return
        regex = r"^(?:https?:\/\/)?(?:www\.)?youtu\.?be(?:\.com)?\/?.*(?:watch|embed)?(?:.*v=|v\/|\/)([\w\-_]+)\&?"
        match = re.match(regex,link)
        if match:
            stream_link=await get_link(link)
            if not stream_link:
                k = await msg.edit("Verilen Link Geçersiz.")
                await delete_messages([m, k])
                return
        else:
            stream_link=link
        try:
            is_audio_ = await is_audio(stream_link)
        except:
            is_audio_ = False
            LOGGER.error("Ses özellikleri zaman içinde alınamıyor.")
        if not is_audio_:
            k = await msg.edit("Bu geçersiz bir bağlantı, bana doğrudan bir bağlantı veya bir youtube bağlantısı sağlayın.")
            await delete_messages([m, k])
            return
        try:
            dur=await get_duration(stream_link)
        except:
            dur=0
        if dur != 0:
            k = await msg.edit("Bu bir canlı yayın değil, /play komutunu kullanın.")
            await delete_messages([m, k])
            return
        k, msg_=await stream_from_link(stream_link)
        if k == False:
            k = await msg.edit(msg_)
            await delete_messages([m, k])
            return
        if Config.msg.get('player'):
            await Config.msg['player'].delete()
        Config.msg['player']=await msg.edit(f"[Streaming]({stream_link}) Started. ㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤ", disable_web_page_preview=True, reply_markup=await get_buttons())
        await delete_messages([m])
        


admincmds=["yplay", "leave", "pause", "resume", "skip", "restart", "volume", "shuffle", "clearplaylist", "export", "import", "update", 'replay', 'logs', 'stream', 'fplay', 'schedule', 'record', 'slist', 'cancel', 'cancelall', 'vcpromote', 'vcdemote', 'refresh', 'rtitle', 'seek', 'vcmute', 'unmute',
f'stream@{Config.BOT_USERNAME}', f'logs@{Config.BOT_USERNAME}', f"replay@{Config.BOT_USERNAME}", f"yplay@{Config.BOT_USERNAME}", f"leave@{Config.BOT_USERNAME}", f"pause@{Config.BOT_USERNAME}", f"resume@{Config.BOT_USERNAME}", f"skip@{Config.BOT_USERNAME}", 
f"restart@{Config.BOT_USERNAME}", f"volume@{Config.BOT_USERNAME}", f"shuffle@{Config.BOT_USERNAME}", f"clearplaylist@{Config.BOT_USERNAME}", f"export@{Config.BOT_USERNAME}", f"import@{Config.BOT_USERNAME}", f"update@{Config.BOT_USERNAME}",
f'play@{Config.BOT_USERNAME}', f'schedule@{Config.BOT_USERNAME}', f'record@{Config.BOT_USERNAME}', f'slist@{Config.BOT_USERNAME}', f'cancel@{Config.BOT_USERNAME}', f'cancelall@{Config.BOT_USERNAME}', f'vcpromote@{Config.BOT_USERNAME}', 
f'vcdemote@{Config.BOT_USERNAME}', f'refresh@{Config.BOT_USERNAME}', f'rtitle@{Config.BOT_USERNAME}', f'seek@{Config.BOT_USERNAME}', f'mute@{Config.BOT_USERNAME}', f'vcunmute@{Config.BOT_USERNAME}'
]

allcmd = ["play", "player", f"play@{Config.BOT_USERNAME}", f"player@{Config.BOT_USERNAME}"] + admincmds

@Client.on_message(filters.command(admincmds) & ~admin_filter & chat_filter)
async def notforu(_, m: Message):
    k = await _.send_cached_media(chat_id=m.chat.id, file_id="CAADBQADEgQAAtMJyFVJOe6-VqYVzAI", caption="You Are Not Authorized", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('⚡️Join Here', url='https://t.me/subin_works')]]))
    await delete_messages([m, k])

@Client.on_message(filters.command(allcmd) & ~chat_filter & filters.group)
async def not_chat(_, m: Message):
    if m.from_user is not None and m.from_user.id in Config.SUDO:
        buttons = [
            [
                InlineKeyboardButton('⚡️Change CHAT', callback_data='set_new_chat'),
            ],
            [
                InlineKeyboardButton('No', callback_data='closesudo'),
            ]
            ]
        await m.reply("Bu, oynamak için yapılandırdığım grup değil, Bu grubu varsayılan CHAT olarak ayarlamak istiyor musunuz?", reply_markup=InlineKeyboardMarkup(buttons))
        await delete_messages([m])
    else:
        buttons = [
            [
                InlineKeyboardButton('⚡️Kendi Botunu Yap', url='https://github.com/mutluemir08/VCPlayerBot'),
                InlineKeyboardButton('🧩 Katıl', url='https://t.me/theagencysohbet'),
            ]
            ]
        await m.reply("<b>Bu botu bu grupta kullanamazsınız, bunun için kendi botunuzu oluşturmalısınız. [SOURCE CODE](https://github.com/mutluemir08/VCPlayerBot) below.</b>", disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(buttons))

