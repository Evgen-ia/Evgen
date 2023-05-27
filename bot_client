import socket
import ssl
import json
import logging

logging.basicConfig(level=logging.DEBUG)

sslcontext = ssl.create_default_context()

HOST = 'api.telegram.org'
PORT = 443

msg = 'Hello World!'

header = 'POST /bot6040427045:AAGKubfcG3zd3CX4edoVGYBZ35B-k3qNmis/sendMessage HTTP/1.1\r\nHost: api.telegram.org\r\nContent-Type: application/json\r\nContent-Length: %d\r\nConnection: close\r\n\r\n%s'
json_response = json.dumps(
    {
        'chat_id': 921325020,
        'text': 'Hello World!'
    }
)
header = header % (len(json_response), json_response)


sd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sd = sslcontext.wrap_socket(sd, server_hostname=HOST)
sd.connect((HOST, PORT))

# Отправка запроса
sd.sendall(header.encode())

# Получение ответа
response = sd.recv(1024).decode()

print(response)

sd.shutdown(socket.SHUT_RDWR)

# Закрытие соединения
sd.close()
