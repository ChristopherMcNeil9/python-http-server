import socket
import sys
import os
import ssl
from multiprocessing import Process
from python import search_engine

HOST = os.popen('hostname --all-ip-addresses').read().strip()
PORT = 4200
BUFF_SIZE = 4096

# Things to add
# LOAD ITEMS INTO A CACHE WHEN SERVER IS SET UP TO REDUCE READ/WRITE TIME?
# ENABLE BROWSER CACHING OF IMAGES ON THE SITE TO HELP SPEED UP SITE


def main():
    # creates and sets up socket
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain('certificate.pem', 'privkey.pem')

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((HOST, PORT))
        sock.listen(64)
        # loop handling connections
        with context.wrap_socket(sock, server_side=True) as ssock:
            while True:
                for i in range(2):
                    try:
                        conn, address = ssock.accept()
                        process = Process(target=handle_connection, args=(conn, address))
                        process.start()
                    except ssl.SSLError:
                        pass
                    except OSError:
                        conn, address = sock.accept()
                        process = Process(target=handle_connection, args=(conn, address))
                        process.start()


# used to validate that the path is not outside of local directory
def is_safe_path(basedir, path, follow_symlinks=True):
    # resolves symbolic links
    if follow_symlinks:
        return os.path.realpath(path).startswith(basedir)

    return os.path.abspath(path).startswith(basedir)


def handle_connection(connection, address):
    # handles reading the request, up to 1 megabyte in size, after which size it sends 413 error
    request = ''
    # WARNING THIS LOOP IS UNTESTED, MAY NOT PROPERLY LOOP RECEIVE REQUESTS
    while True:
        part = connection.recv(1024).decode('utf-8')
        request += part
        if len(part) < BUFF_SIZE:
            break
        elif len(request) > BUFF_SIZE*256:
            # sends 413 error to sender
            message = 'HTTP/2 413 Request Entity Too Large\n\n<html><body><center><h3>Error 413: Request Entity Too Large</h3></center></body></html>'
            message = message.encode('utf-8')
            connection.send(message)
            connection.close()
            sys.exit()

    # print(request)

    if 'GET' in request.split('\n', 1)[0]:
        message = 'HTTP/2 200 OK\nContent-Type: '
        path = request.split('\n', 1)[0].split(' ')[1][1:]
        if not is_safe_path(os.getcwd(), path):
            message = 'HTTP/2 403 Forbidden\n\n<html><body><center><h3>Error 403: Forbidden</h3></center></body></html>'
            message = message.encode('utf-8')
        else:
            # handles special exception for favicon
            if 'favicon' in path:
                path = 'site/logos/favicon.ico'
            if 'search?' in path:
                term = path.split('=')[1]
                content = search_engine.searcher(term).encode('utf-8')
                message += 'text/html\nContent-Length: ' + str(len(content)) + '\n\n'
                message = message.encode('utf-8') + content
            else:
                try:
                    # reads file to be sent
                    file = open(path, 'rb')
                    content = file.read()
                    file.close()

                    # handles adding additional information to the http header
                    extension = path.split('.')[1]
                    if extension in {'jpg', 'png', 'ico'}:
                        message += 'image/' + extension + '\n'
                    elif extension == 'svg':
                        message += 'image/svg+xml\n'
                    elif extension == 'css':
                        message += 'text/css\n'
                    else:
                        message += 'text/html\n'
                    message += 'Content-Length: ' + str(len(content)) + '\n\n'
                    # adds file contents to the message
                    message = message.encode('utf-8') + content
                # handles various other potential issues
                except:
                    if path == '':
                        message = 'HTTP/2 301 Moved Permanently\nLocation: /site/home.html\n\n'
                    else:
                        message = 'HTTP/2 404 Not Found\n\n<html><body><center><h3>Error 404: File not found</h3></center></body></html>'
                    message = message.encode('utf-8')

        # sends the message over socket connection
        connection.sendall(message)
        connection.close()
        sys.exit()


if __name__ == "__main__":
    main()
