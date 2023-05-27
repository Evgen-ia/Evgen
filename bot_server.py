import socket
import ssl
import json


class Bot:
    def __init__(self, token):
        self.token = token

    @staticmethod
    def send_message(msg: str):
        sslcontext = ssl.create_default_context()
        HOST = 'api.telegram.org'
        PORT = 443

        header = 'POST /bot6040427045:AAGKubfcG3zd3CX4edoVGYBZ35B-k3qNmis/sendMessage HTTP/1.1\r\nHost:\
         api.telegram.org\r\nContent-Type: application/json\r\nContent-Length: %d\r\nConnection: close\r\n\r\n%s'
        json_response = json.dumps(
            {
                'chat_id': 921325020,
                'text': msg
            }
        )
        header = header % (len(json_response), json_response)

        sd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sd = sslcontext.wrap_socket(sd, server_hostname=HOST)
        sd.connect((HOST, PORT))

        sd.sendall(header.encode())
        response = sd.recv(1024).decode()
        return response

    @staticmethod
    def listening_on_tg():
        sslcontext = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        sslcontext.load_cert_chain(certfile='cert.pem', keyfile='key.pem')
        sslcontext.options &= ~ssl.OP_NO_SSLv3
        # print(sslcontext.get_ciphers())

        SERVER_HOST = '0.0.0.0'
        SERVER_PORT = 8443

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket = sslcontext.wrap_socket(server_socket)

        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((SERVER_HOST, SERVER_PORT))
        server_socket.listen(1)
        print('Listening on port %s ...' % SERVER_PORT)

        try:
            client_connection, client_address = server_socket.accept()   # Wait for client connections

            request = client_connection.recv(1024).decode()  # Get the client request
            print(request)

            short_response = 'HTTP/1.1 200 OK\r\n\r\n'  # Send HTTP response
            encoded = short_response.encode()
            # print(encoded)
            client_connection.sendall(encoded)
            client_connection.close()
        except Exception as e:
            print(e)
        server_socket.close()  # Close socket


Bot.send_message("I`m good, thanks")

while True:
    Bot.listening_on_tg()



