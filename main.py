import requests
import json
import sqlite3
import logging
import math
import random
import os

from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from yandex_music import Client

import aiohttp

API_TOKEN = os.environ.get('ApiToken')

endpoint_base = "https://api.music.yandex.net/users/"
my_token = os.environ.get('MyToken')
 
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

conn = sqlite3.connect('/home/evgenia//musicparty/my_db.db')
cursor = conn.cursor()


cursor.execute('''DROP TABLE IF EXISTS "Users"''')
cursor.execute('''CREATE TABLE IF NOT EXISTS "Users" (
    UserId INTEGER PRIMARY KEY,
    user_email TEXT NOT NULL UNIQUE,
    user_score REAL DEFAULT 0.0
)''')

cursor.execute('''DROP TABLE IF EXISTS "Playlists"''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS "Playlists"
    (
        "Playlist_Id"  INTEGER PRIMARY KEY AUTOINCREMENT,
        "kind" integer NOT NULL,
        "User_email" "char" NOT NULL,
         FOREIGN KEY(User_email) REFERENCES Users(user_email) ON DELETE CASCADE
    );
''')

cursor.execute('''DROP TABLE IF EXISTS "Songs"''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS "Songs"
    (
        "Song_Id"  INTEGER PRIMARY KEY AUTOINCREMENT,
        "Id_in_music" integer NOT NULL UNIQUE,
        "Album_id" "char" NOT NULL,
        "User_email" "char" NOT NULL,
         FOREIGN KEY(User_email) REFERENCES Users(user_email) ON DELETE CASCADE
    );
''')

cursor.execute('''DROP TABLE IF EXISTS "Sessions"''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS "Sessions"
    (
        "Ses_Id" INTEGER PRIMARY KEY AUTOINCREMENT,
        "Status" "char" NOT NULL,
        "Chat_Id" integer NOT NULL
    );
''')

cursor.execute('''DROP TABLE IF EXISTS "Candidates_to_playlist"''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS "Candidates_to_playlist"
    (
        "Cand_Id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
        "Ses_Id" integer NOT NULL,
        "User_Id" integer NOT NULL,
        "Playlist_Id" integer NOT NULL,
        FOREIGN KEY(User_Id) REFERENCES Users(UserId) ON DELETE CASCADE,
        CONSTRAINT "Playlist_Id_to_Playlists" FOREIGN KEY ("Playlist_Id")
            REFERENCES "Playlists" ("Playlist_Id") MATCH SIMPLE
            ON UPDATE NO ACTION
            ON DELETE NO ACTION,
        CONSTRAINT "session_Id_to_session" FOREIGN KEY ("Ses_Id")
            REFERENCES "Sessions" ("Ses_Id") MATCH SIMPLE
            ON UPDATE NO ACTION
            ON DELETE NO ACTION
    );
''')


cursor.execute('''DROP TABLE IF EXISTS "Reactions"''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS "Reactions"
    (
        "ReactionID" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
        "UserID" integer NOT NULL,
        "ReceiverID" integer NOT NULL,
        "Type" "char" NOT NULL,
        FOREIGN KEY(UserID) REFERENCES Users(UserId) ON DELETE CASCADE,
        CONSTRAINT "Unique_combin" UNIQUE ("UserID", "ReceiverID"),
        CONSTRAINT "Reactions_to_Users" FOREIGN KEY ("ReceiverID")
            REFERENCES "Users" ("User_Id") MATCH SIMPLE
            ON UPDATE NO ACTION
            ON DELETE NO ACTION
    );

 ''')

conn.commit()


def user_rank():
    cursor.execute('SELECT * FROM Reactions')
    reactions = cursor.fetchall()
    print("мы в user_rank, вот инфа из библиотеки:", reactions)
    user_likes = {}

    for reaction in reactions:
        user_id = reaction[1]
        like_value = 1 if reaction[3] == 'like' else -1
        user_likes[user_id] = user_likes.get(user_id, 0) + like_value

    total_likes = sum(user_likes.values())
    user_ratings = []

    for user_id, likes in user_likes.items():
        rating = round(8 * likes / total_likes) + 2
        user_ratings.append((user_id, rating))

    print("\n мы в user_rank, вот рейтинги: ", user_ratings)
    return user_ratings


def kind_from_title(info_d: dict, title: str) -> str:
    for item in info_d.get("result", []):
        if item.get("title") == title:
            return item.get("kind")
    raise ValueError(f"Kind not found for {title}")


def info_list(user_email: str) -> dict:
    endpoint1 = endpoint_base + str(user_email) + "/playlists/list"
    headers1 = {"Authorization": my_token}

    info1_json = requests.get(endpoint1, headers=headers1).json()

    info1_str = json.dumps(info1_json)
    info1_dict = json.loads(info1_str)
    return info1_dict


def uid_from_email(user_email: str) -> str:
    endpoint1 = endpoint_base + str(user_email) + "/playlists/list"
    headers1 = {"Authorization": my_token}
    info1_json = requests.get(endpoint1, headers=headers1).json()
    info1_str = json.dumps(info1_json)
    info1_dict = json.loads(info1_str)
    print("aaaaaaaaaaa", info1_dict)
    # print("uid_from_email_info = ", info1_dict)
    owner_uid = str(info1_dict["result"][0]["owner"]["uid"])

    return owner_uid


def add_recommendations(user_email: str, kind: int, n: int, revis: int):
    # print("n = ", n)
    endpoint1 = endpoint_base + user_email + "/playlists/" + str(kind) + "/recommendations?limit = [" + str(n) + "]"
    # data1 = {"visibility": "public", "title": "Playlist from bot"}
    headers1 = {"Authorization": my_token}

    info1_json = requests.get(endpoint1, headers=headers1).json()
    info1_str = json.dumps(info1_json)
    info1_dict = json.loads(info1_str)

    new_tracks = []
    for i in range(n):
        tr_id, al_id = info1_dict["result"]["tracks"][i]["id"], info1_dict["result"]["tracks"][i]["albums"][0]["id"]
        new_dict = {"id": tr_id, "albumId": al_id}
        new_tracks.append(new_dict)

    # print("\n AAAAAAAAAAA \n я зашел в новые трэки, вот они:", new_tracks, '\n')
    diff = [{"op": "insert", "at": 0, "tracks": new_tracks}]
    # print("new_tracks = ", new_tracks)
    endpoint2 = "https://api.music.yandex.net/users/781749467/playlists/" + str(kind) + "/change"
    data2 = {"diff": json.dumps(diff), "revision": revis}
    headers2 = {"Authorization": my_token}

    requests.post(url=endpoint2, data=data2, headers=headers2).json()


def creating_final(chat_id: int) -> str:
    endpoint1 = endpoint_base + "yampolskaya.eugenie/playlists/create"
    data1 = {"visibility": "public", "title": "Playlist from bot"}
    headers1 = {"Authorization": my_token}
    # print('\n request \n')
    info1_json = requests.post(endpoint1, data=data1, headers=headers1).json()  # creating playlist
    # print('info1_json = ', info1, '\n')
    # info1_json = info1.json()

    info1_str = json.dumps(info1_json)
    info1_dict = json.loads(info1_str)

    new_pll_kind = str(info1_dict["result"]["kind"])
    revis = info1_dict["result"]["revision"]

    # ratings = user_rank()
    # print("ratings = ", ratings)
    # print("\nЩа будут айдишки сессий \n")
    # cursor.execute("SELECT ses_id FROM sessions")
    # idss = cursor.fetchall()
    # for row in idss:
    #     print(row[0])

    cursor.execute(f"SELECT Playlists.kind, Playlists.User_email\
                    FROM Playlists\
                    JOIN Candidates_to_playlist ON Playlists.Playlist_Id = Candidates_to_playlist.Playlist_Id\
                    JOIN Sessions ON Candidates_to_playlist.Ses_Id = Sessions.Ses_Id\
                    WHERE Sessions.Chat_Id = {chat_id} AND Sessions.Ses_Id = (SELECT MAX(Ses_Id)\
                    FROM Sessions WHERE Chat_Id = {chat_id})")
    results = cursor.fetchall()
    num_results = len(results)
    # print(f"Number of results: {num_results}")
    print(f"Results: {results}")
    n: int = 0
    list_of_all_tracks = []
    for row in results:
        # print("рас-рас\n")
        kind = row[0]
        user_email = row[1]
        endp = "https://api.music.yandex.net/users/" + user_email + "/playlists/" + str(kind) + "?rich-tracks=false"
        head = {"Authorization": my_token}
        info_j = requests.get(url=endp, headers=head).json()
        info_str = json.dumps(info_j)
        info_d = json.loads(info_str)
        track_count = info_d["result"]["trackCount"]
        print("trackCount = ", track_count)
        n = track_count/5
        skip_iterations = set(random.sample(range(track_count), n))
        i = 0
        while i < track_count:
            if i not in skip_iterations:
                t_id, al_id = info_d["result"]["tracks"][i]["id"], info_d["result"]["tracks"][i]["albumId"]
                new_dict = {"id": t_id, "albumId": al_id}
                list_of_all_tracks.append(new_dict)
                print(new_dict, "песня", i)
            i += 1

        print("i =", i)
    diff = [{"op": "insert", "at": 0, "tracks": list_of_all_tracks}]
    # print(diff)

    endpoint2 = "https://api.music.yandex.net/users/781749467/playlists/" + new_pll_kind + "/change"
    data2 = {"diff": json.dumps(diff), "revision": str(revis)}
    headers2 = {"Authorization": my_token}

    requests.post(url=endpoint2, data=data2, headers=headers2).json()
    revis += 1
    add_recommendations("781749467", int(new_pll_kind), n, revis)
    return "https://music.yandex.ru/users/yampolskaya.eugenie/playlists/" + new_pll_kind + "?utm_medium=copy_link"


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    chat_id = message.chat.id
    # bot.session._trace_configs = [trace_config]
    await message.reply("Hello!\n I am a music bot, i can create a new playlist for your company.\
    Please text me how long do you want to listen to music. After that you can just sand all music,\
     by one or a whole playlist together! Just command me '/finish' and i'll sendback your new prepeared playlist!")
    cursor.execute(f"INSERT INTO Sessions (Status, Chat_ID) VALUES ('started', {chat_id})")
    conn.commit()
    print("got start")


@dp.message_handler(commands=['finish'])
async def send_bye(message: types.Message):
    chat_id = message.chat.id
    await message.reply("я фсё сделяль")

    cursor.execute(f"SELECT MAX(Ses_Id) FROM Sessions WHERE Chat_Id = {chat_id}")
    max_ses_id = cursor.fetchone()[0]
    cursor.execute(f"UPDATE Sessions SET Status = 'finished', Chat_ID = {chat_id} WHERE Ses_id = ?", (max_ses_id,))

    conn.commit()
    await message.reply(creating_final(chat_id))
    print("got finish")


# @dp.message_handler(regexp='https://api.music.yandex.net')
# async def handle_message(message: Message):
#     print("keyboard start")
#     # создаем инлайн-клавиатуру
#     keyboard = InlineKeyboardMarkup(row_width=2)
#     keyboard.add(InlineKeyboardButton(text='nice', callback_data='like'),
#                  InlineKeyboardButton(text='not nice..', callback_data='dislike'))
#
#     # отправляем сообщение с инлайн-клавиатурой
#     await bot.send_message(chat_id=message.chat.id, text='Выберите действие:', reply_markup=keyboard)


async def get_user_id_by_message_id(bot, chat_id, message_id):
    message = await bot.get_message(chat_id, message_id)
    user = await bot.get_chat_member(chat_id, message.from_user.id)
    return user.user.id


# @dp.message_handler(commands=['rang'])
# async def rank_command_handler(message: types.Message):
#     # Получаем список пользователей и их оценок с помощью ранее написанной функции
#     users_ratings = user_rank()
#     print("user_rank = ", user_rank())
#     # Создаем сообщение с списком пользователей и их оценками
#     text = "Список пользователей и их оценки:\n\n"
#     for user, rating in users_ratings:
#         text += f"{user}: {rating}\n"
#
#     await message.answer(text)   # Отправляем сообщение с списком пользователей и их оценками


@dp.message_handler(regexp='https://music.yandex.ru')
async def handle_message(message: types.Message):
    print("in handle")
    chat_id = message.chat.id
    # kreating inline-keyboard
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(InlineKeyboardButton(text='nice', callback_data='like'),
                 InlineKeyboardButton(text='not nice..', callback_data='dislike'))

    # receiving ChatMember для бота
    # bot_user = await bot.get_chat_member(chat_id, bot.id)

    await bot.send_message(chat_id=message.chat.id, text="choose your reaction:",
                           reply_to_message_id=message.message_id, reply_markup=keyboard)
    # message_id = sent_message.message_id

    # chat = await bot.get_chat(chat_id)

    user_email = None
    pll_kind = None
    track_id = None
    album_id = None
    message_text = message.text
    print("here")
    if message_text.startswith("https://music.yandex.ru/users/"):
        parts = message_text.split('/')
        user_email = parts[4]
        pll_kind = parts[6].split('?')[0]
        await bot.send_message(chat_id, f"Получены данные: user_email={user_email}, playlist_kind={pll_kind}")
        print("got email, pll_kind")

    elif message.text.startswith("https://music.yandex.ru/album/"):
        parts = message_text.split('/')
        album_id = parts[4]
        track_id = parts[6].split('?')[0]
        await bot.send_message(chat_id, f"Получены данные: track_id={track_id}, album_id={album_id}")
        print("got track_id, album_id = ", track_id, album_id)

    if track_id is not None:
        endp1 = endpoint_base + "yampolskaya.eugenie/playlists/create"
        data1 = {"visibility": "public", "title": "extra song"}
        headers1 = {"Authorization": my_token}

        info1_json = requests.post(endp1, data=data1, headers=headers1).json()  # creating playlist

        info1_str = json.dumps(info1_json)
        info1_dict = json.loads(info1_str)
        song_pll_kind = str(info1_dict["result"]["kind"])
        revis = str(info1_dict["result"]["revision"])

        diff = [{"op": "insert", "at": 0, "tracks": [{"id": track_id, "albumId": album_id}]}]

        endpoint2 = "https://api.music.yandex.net/users/781749467/playlists/" + song_pll_kind + "/change"
        data2 = {"diff": json.dumps(diff), "revision": revis}
        headers2 = {"Authorization": my_token}

        requests.post(url=endpoint2, data=data2, headers=headers2).json()
        user_email = "yampolskaya.eugenie"
        print("внутри хендлера, это имейл - ", user_email)
        pll_kind = song_pll_kind
        await bot.send_message(chat_id, f"сделал сонгу: user_email={user_email}, playlist_kind={pll_kind}")

    if user_email is not None:
        owner_uid = uid_from_email(user_email)
        cursor.execute('SELECT Ses_Id FROM Sessions ORDER BY Ses_Id DESC LIMIT 1')
        ses_id = cursor.fetchone()[0]
        print("мы внутри хендлера, заполняем базу")
        print("user_email, pll_kind, ses_id = ", user_email, pll_kind, ses_id)
        cursor.execute(
            f"INSERT INTO Playlists (kind, User_email) VALUES ({pll_kind}, '{user_email}')")
        # cursor.execute(
        #     f"INSERT INTO Users (UserID, User_email, user_score) VALUES ({message.from_user.id}, '{user_email}', '{0}')")
        # conn.commit()


        cursor.execute('SELECT Playlist_Id FROM Playlists ORDER BY Playlist_Id DESC LIMIT 1')
        pll_id = cursor.fetchone()[0]
        print("pll_id = ", pll_id)
        cursor.execute(
            "INSERT INTO Candidates_to_playlist (Ses_Id, User_Id, Playlist_Id) VALUES (?, ?, ?)", (ses_id, owner_uid, pll_id))
        conn.commit()


@dp.callback_query_handler(lambda c: c.data == 'like')
async def process_callback_button1(callback_query: types.CallbackQuery):
    user = callback_query.from_user.id
    message_id = callback_query.message.message_id
    receiver = callback_query.message.from_user.id

    cursor.execute("SELECT user_email from Users WHERE UserId = ?", (user))
    user_id = cursor.fetchone()
    cursor.execute("SELECT user_email from Users WHERE UserId = ?", (receiver))
    receiver_id = cursor.fetchone()
    print("inside like bottom, here are ids: ", user_id, receiver_id)
    cursor.execute(
        "INSERT INTO Reactions (UserId, ReceiverID, Type) VALUES (?, ?, ?)",
        (user_id, receiver_id, "like"))
    conn.commit()
    print("записал лайк")
    pass




@dp.callback_query_handler(lambda c: c.data == 'dislike')
async def process_callback_button1(callback_query: types.CallbackQuery):
    user = callback_query.from_user.id
    # message_id = callback_query.message.message_id
    receiver = callback_query.message.from_user.id
    cursor.execute("SELECT user_email from Users WHERE UserId = ?", (user,))
    user_id = cursor.fetchone()
    cursor.execute("SELECT user_email from Users WHERE UserId = ?", (receiver,))
    receiver_id = cursor.fetchone()
    cursor.execute(
        "INSERT INTO Reactions (UserId, ReceiverID, Type) VALUES (?, ?, ?)",
        (user_id, receiver_id, "dislike"))
    conn.commit()
    print("записал дизлайк")
    pass

def del_from_bot():
    endpoint1 = endpoint_base + "yampolskaya.eugenie/playlists/list"
    headers1 = {"Authorization": my_token}
    info1 = requests.get(endpoint1, headers=headers1)



client = Client('y0_AgAAAAAumIzbAAAgQwAAAADbGftvzdzGGejhT96Ze_Lqx4dctLXppSI').init()
#print("client connected")
#client.users_likes_tracks()[0]

if __name__ == '__main__':
    #print("before polling")
    executor.start_polling(dp, skip_updates=True)
    print("The last line and my patient")







#y0_AgAAAAAumIzbAAAgQwAAAADbGftvzdzGGejhT96Ze_Lqx4dctLXppSI - токен яндекса






