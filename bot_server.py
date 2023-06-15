import sqlite3
import socket
import ssl
import json
import logging
from threading import Thread
import math
import random
import gzip

import requests

logging.basicConfig(level=logging.DEBUG)

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

conn = sqlite3.connect('/home/evgenia//musicparty/my_db.db')
cursor = conn.cursor()

API_TOKEN = '5689948994:AAF2t_F-XVKejZvyHe_h0nH_bxDwsrxJS64'

endpoint_base = "https://api.music.yandex.net/"
my_token = "OAuth y0_AgAAAAAumIzbAAAgQwAAAADbGftvzdzGGejhT96Ze_Lqx4dctLXppSI"

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


class Bot:
    def __init__(self, token, answer_callback):
        self.token = token

        self.webhook_sslcontext = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)  # encriptition
        self.webhook_sslcontext.load_cert_chain(certfile='cert.pem', keyfile='key.pem')
        self.webhook_sslcontext.options &= ~ssl.OP_NO_SSLv3

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket = self.webhook_sslcontext.wrap_socket(self.server_socket)

        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('0.0.0.0', 8443))
        self.server_socket.listen(1)
        self.answer_callback = answer_callback
        print('Listening on port %s ...' % 8443)

        self.answer_queue = []

        # start answer thread

        def answer_loop():
            while True:
                if self.answer_queue:
                    answer_string, chat_id = self.answer_queue.pop(0)
                    self.send_message(answer_string, chat_id)

        thread = Thread(target=answer_loop)
        thread.start()

    def __del__(self):
        self.server_socket.close()

    def send_message(self, msg: str, chat_id: int):
        sslcontext = ssl.create_default_context()
        HOST = 'api.telegram.org'
        PORT = 443

        header = 'POST /bot%s/sendMessage HTTP/1.1\r\nHost:\
         api.telegram.org\r\nContent-Type: application/json\r\nContent-Length: %d\r\nConnection: close\r\n\r\n%s'
        json_response = json.dumps(
            {
                'chat_id': chat_id,
                'text': msg
            }
        )
        header = header % (self.token, len(json_response), json_response)

        sd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sd = sslcontext.wrap_socket(sd, server_hostname=HOST)
        sd.connect((HOST, PORT))

        sd.sendall(header.encode())
        response = sd.recv(1024).decode()
        return response

    def listen(self):
        try:
            print('tried')
            client_connection, client_address = self.server_socket.accept()   # Wait for client connections
            cl = HTTPS()
            request = cl.recv(client_connection)
            print("request = ",  request)

            # parse request, get json
            header, body = request
            if len(body) < 2:
                print("wrong request " + header + body)
                return 'wrong request 178'

            short_response = 'HTTP/1.1 200 OK\r\n\r\n'  # Send HTTP response
            encoded = short_response.encode()
            # print(encoded)
            client_connection.sendall(encoded)
            client_connection.close()

            print('body decoded', body.decode())
            json_request = json.loads(body.decode())
            # json_request = json.loads(str_request)

            # print(json_request, "the json")
            chat_id = json_request['message']['chat']['id']
            # text_from_user = json_request['message']['text']
            answer_string = self.answer_callback(json_request)
            print("answer_string = ", answer_string)
            self.answer_queue.append((answer_string, chat_id,))
            # print("", self.answer_queue)
            # self.send_message(answer_string, chat_id)
        except Exception as e:
            print('exeption189: ', e)


def music_answer_callback(json_request):
    chat_id = json_request['message']['chat']['id']
    text_from_user = json_request['message']['text']
    answer = None

    if text_from_user == '/start':
        cursor.execute(f"INSERT INTO Sessions (Status, Chat_ID) VALUES ('started', {chat_id})")
        conn.commit()
        cursor.execute(f'SELECT ses_id FROM Sessions WHERE Chat_Id = {chat_id}')
        result = cursor.fetchone()
        print('res =', result[0])
        answer = 'Hi! We`ve just sterted your music party)'

    if text_from_user == '/finish':
        cursor.execute(f"SELECT MAX(Ses_Id) FROM Sessions WHERE Chat_Id = {chat_id}")
        max_ses_id = cursor.fetchone()[0]
        cursor.execute(f"UPDATE Sessions SET Status = 'finished', Chat_ID = {chat_id} WHERE Ses_id = ?", (max_ses_id,))
        conn.commit()
        answer = creating_final(chat_id)

    sess = f"SELECT Status FROM Sessions WHERE chat_id = {chat_id}"
    exists = cursor.fetchone() is not None

    if exists is None:
        return 'сессия не открыта'     # creating_final(chat_id)

    yandex = YandexAPI(my_token)
    user_email = None
    pll_kind = None
    track_id = None
    album_id = None
    message_text = text_from_user

    if message_text.startswith("https://music.yandex.ru/users/"):
        parts = message_text.split('/')
        user_email = parts[4]
        pll_kind = parts[6].split('?')[0]
        print("got email, pll_kind")
    elif message_text.startswith("https://music.yandex.ru/album/"):
        parts = message_text.split('/')
        album_id = parts[4]
        track_id = parts[6].split('?')[0]
        print("got track_id, album_id = ", track_id, album_id)

    if track_id is not None:
        # print('got in track_id 238')
        # info1_dict = yandex.create_playlist('extra song')
        # print('created pll extra song')

        endp1 = endpoint_base + "/users/yampolskaya.eugenie/playlists/create"
        data1 = {"visibility": "public", "title": "song1"}
        headers1 = {"Authorization": my_token}
        # print(endp1)
        # print(data1)
        # print(headers1)
        info1_json = requests.post(endp1, data=data1, headers=headers1).json()  # creating playlist
        info1_str = json.dumps(info1_json)
        info1_dict = json.loads(info1_str)
        # print(info1_dict)

        song_pll_kind = str(info1_dict["result"]["kind"])
        revis = str(info1_dict["result"]["revision"])

        diff = [{"op": "insert", "at": 0, "tracks": [{"id": track_id, "albumId": album_id}]}]

        endpoint2 = "https://api.music.yandex.net/users/781749467/playlists/" + song_pll_kind + "/change"
        # print(endpoint2)
        data2 = {"diff": json.dumps(diff), "revision": revis}
        # print(data2)
        headers2 = {"Authorization": my_token}
        result = requests.post(url=endpoint2, data=data2, headers=headers2)
        # print(result)
        pll_kind = song_pll_kind
        answer = f"сделал сонгу: user_email=yampolskaya.eugenie, playlist_kind={pll_kind}"

    if user_email is not None:
        owner_uid = uid_from_email(user_email)
        cursor.execute('SELECT Ses_Id FROM Sessions ORDER BY Ses_Id DESC LIMIT 1')
        ses_id = cursor.fetchone()[0]
        print("мы внутри хендлера, заполняем базу")
        print("user_email, pll_kind, ses_id = ", user_email, pll_kind, ses_id)
        cursor.execute(
            f"INSERT INTO Playlists (kind, User_email) VALUES ({pll_kind}, '{user_email}')")
        conn.commit()
        # cursor.execute(
        # f"INSERT INTO Users (UserID, User_email, user_score) VALUES ({message.from_user.id}, '{user_email}', '{0}')")
        # conn.commit()

        cursor.execute('SELECT Playlist_Id FROM Playlists ORDER BY Playlist_Id DESC LIMIT 1')
        pll_id = cursor.fetchone()[0]
        print("pll_id = ", pll_id)
        cursor.execute(
            "INSERT INTO Candidates_to_playlist (Ses_Id, User_Id, Playlist_Id)\
             VALUES (?, ?, ?)", (ses_id, owner_uid, pll_id))
        conn.commit()
        answer = "обработал плэйлист"
    return answer


def uid_from_email(user_email: str) -> str:
    endpoint1 = endpoint_base + str(user_email) + "/playlists/list"
    headers1 = {"Authorization": my_token}
    info1_json = requests.get(endpoint1, headers=headers1).json()
    info1_str = json.dumps(info1_json)
    info1_dict = json.loads(info1_str)
    # print("uid_from_email_info = ", info1_dict)
    owner_uid = str(info1_dict["result"][0]["owner"]["uid"])

    return owner_uid


class HTTPS:
    http_header_delimiter = b'\r\n\r\n'
    content_length_field = b'Content-Length:'

    def __init__(self):
        self.header = bytes()
        self.content_length = 0
        self.body = bytes()

    def separate_header_and_body(self, data):
        try:
            index = data.index(self.http_header_delimiter)
        except:
            return data, bytes()
        else:
            index += len(self.http_header_delimiter)
            return data[:index], data[index:]

    @classmethod
    def get_content_length(cls, header):
        for line in header.split(b'\r\n'):
            if cls.content_length_field in line:
                return int(line[len(cls.content_length_field):])

        return 0

    def read_until(self, sock, condition, length_start=0, chunk_size=4096):
        data = bytes()
        chunk = bytes()
        length = length_start
        try:
            # print('here')
            while not condition(length, chunk):
                chunk = sock.recv(chunk_size)
                # print('condition', condition, 'chunk = ', chunk.decode())
                if not chunk:
                    break
                else:
                    data += chunk
                    length += len(chunk)
        except socket.timeout:
            print('timeout')
            pass
        return data

    def end_of_header(self, length, data):
        return b'\r\n\r\n' in data

    def end_of_content(self, length, data):
        return self.content_length <= int(length)

    def recv(self, sock):
        # read until end of header
        data = self.read_until(sock, self.end_of_header)

        # separate our body and header
        self.header, self.body = self.separate_header_and_body(data)

        # get the Content Length from the header
        self.content_length = self.get_content_length(self.header)

        # read until end of Content Length
        self.body += self.read_until(sock, self.end_of_content, len(self.body))

        return self.header, self.body


class YandexAPI:
    def __init__(self, token):
        self.host = "api.music.yandex.net"
        self.port = 443
        self.token = token

    def create_playlist(self, title: str) -> json:
        print('in yandex.create_playlist')
        body = f"visibility=public&title={title}"
        encoded_body = body.encode('utf-8')

        request = (
            f"POST /users/781749467/playlists/create HTTP/1.1\r\n"
            f"Host: " + self.host + f"\r\n"
            f"Content-Type: application/x-www-form-urlencoded;charset=utf-8\r\n"  
            f"Accept-Encoding: gzip, deflate\r\n"
            f"Accept: */*\r\n"
            f"User-Agent: Yandex-Music-API\r\n"
            f"Content-Length: " + str(len(encoded_body)) + f"\r\n"
            f"Authorization: " + self.token + f"\r\n"
            f"Connection: keep-alive\r\n\r\n" +
            body
        )

        encoded = request.encode('utf-8')

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.host, self.port))
        ssl_sock = ssl.wrap_socket(sock)

        ssl_sock.write(encoded)

        cl = HTTPS()
        data = cl.recv(ssl_sock)

        ssl_sock.close()

        sock.close()

        return data

    def uid_from_email(self, user_email):
        request = f"GET /users/yampolskaya.eugenie/playlists/list HTTP/1.1\r\n" \
                  f"Host: {self.host}\r\n" \
                  f"Authorization: OAuth y0_AgAAAAAumIzbAAAgQwAAAADbGftvzdzGGejhT96Ze_Lqx4dctLXppSI\r\n" \
                  f"Connection: keep-alive\r\n\r\n"

        # Create a socket connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.host, self.port))

        # Send the request
        request = request.encode('utf-8')
        sock.sendall(request)

        cl = HTTPS()
        response_head, response_body = cl.recv(sock)
        print("uid_from_email_info = ", response_body)
        owner_uid = str(response_body["result"][0]["owner"]["uid"])

        return owner_uid


def recv_chunks(sock):
    chunk_size = 4096
    data = b''

    while True:
        inf = b''

        inf += sock.recv(chunk_size)
        # with gzip.GzipFile(fileobj=inf, mode='rb') as gz_file:
        #     # Чтение исходных данных из распакованного потока
        #     uncompressed_data = gz_file.read()
        # print('\ninf =', uncompressed_data)

        # Получаем размер чанка из прочитанных данных
        # chunk_size_str, size_data = inf.split(b'\r\n', 1)
        # chunk_size = int(chunk_size_str, 16)
        data += sock.recv(chunk_size)
        print('\n data =',  data.decode())          # gzip.decompress(

        _ = sock.recv(2)

        if inf == 0:
            break

    return data


def creating_final(chat_id: int) -> str:
    # print('\n start yandex \n')
    # yandex = YandexAPI(my_token)
    # info1_dict = yandex.create_playlist("PartyBot playlist")
    # print('\n finish yandex \n')
    print('in final')
    endpoint1 = endpoint_base + "yampolskaya.eugenie/playlists/create"
    data1 = {"visibility": "public", "title": "Playlist from bot"}
    headers1 = {"Authorization": my_token}

    info1_json = requests.post(endpoint1, data=data1, headers=headers1).json()  # creating playlist

    info1_str = json.dumps(info1_json)
    info1_dict = json.loads(info1_str)

    new_pll_kind = str(info1_dict["result"]["kind"])
    revis = info1_dict["result"]["revision"]


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


if __name__ == '__main__':
    bot = Bot('6040427045:AAGKubfcG3zd3CX4edoVGYBZ35B-k3qNmis', music_answer_callback)
    while True:
        bot.listen()
