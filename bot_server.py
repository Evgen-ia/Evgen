import sqlite3
import socket
import ssl
import json
import logging
from threading import Thread

logging.basicConfig(level=logging.INFO)

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


class Bot:
    def __init__(self, token, answer_callback):
        self.token = token

        self.webhook_sslcontext = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
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
                    print("resp = ", self.send_message(answer_string, chat_id))

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

    def listen_step(self):
        try:
            client_connection, client_address = self.server_socket.accept()   # Wait for client connections

            request = client_connection.recv(1024).decode()  # Get the client request
            print(request)

            short_response = 'HTTP/1.1 200 OK\r\n\r\n'  # Send HTTP response
            encoded = short_response.encode()
            # print(encoded)
            client_connection.sendall(encoded)
            client_connection.close()

            # parse request, get json
            data = request.split('\r\n\r\n', 1)[1]
            json_request = json.loads(data)
            # print(json_request, "the json")
            chat_id = json_request['message']['chat']['id']
            # text_from_user = json_request['message']['text']
            answer_string = answer_callback(json_request)
            print("answer_string = ", answer_string)
            self.answer_queue.append((answer_string, chat_id,))
            print(self.answer_queue)
            #self.send_message(answer_string, chat_id)
        except Exception as e:
            print(e)


def answer_callback(request):
    chat_id = request['message']['chat']['id']
    text_from_user = request['message']['text']
    if(text_from_user == '/sta'):
        cursor.execute(f"INSERT INTO Sessions (Status, Chat_ID) VALUES ('started', {chat_id})")
        conn.commit()
        return '/start'

    else: return 'ты че про мою маму вякнул?'


def message_received(json_request):
    #TODO
    return 'Text of bot to user message'


bot = Bot('6040427045:AAGKubfcG3zd3CX4edoVGYBZ35B-k3qNmis', message_received)
#bot.listen_step()
# print(bot.send_message("I`m good, thanks", 921325020))

while True:
    bot.listen_step()



    # def myreceive(self):
    #     chunks = []
    #     bytes_recd = 0
    #     while bytes_recd < MSGLEN:
    #         chunk = self.sock.recv(min(MSGLEN - bytes_recd, 2048))
    #         if chunk == b'':
    #             raise RuntimeError("socket connection broken")
    #         chunks.append(chunk)
    #         bytes_recd = bytes_recd + len(chunk)
    #     return b''.join(chunks)
