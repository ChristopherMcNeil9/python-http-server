import socket
import sys
import os
import requests
from datetime import datetime
from multiprocessing import Process
from pathlib import Path

# ENABLE BROWSER CACHING OF IMAGES ON THE SITE TO HELP SPEED UP SITE
def main():
    # pings google DNS and returns with local ip value
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    host = s.getsockname()[0]
    port = 4200
    s.close()

    # creates Logs file on initial startup and verifies its existence on further boots.
    if not os.path.isdir('Logs'):
        os.mkdir('Logs')
    # creates and sets up socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen(64)
        # loop handling connections
        while True:
            conn, address = s.accept()
            # handles request for data
            process = Process(target=handle_connection, args=(conn, address,))
            process.start()


# used to validate that the path is not outside of local directory
# check to make sure this is working
def is_safe_path(basedir, path, follow_symlinks=True):
    # resolves symbolic links
    if follow_symlinks:
        return os.path.realpath(path).startswith(basedir)

    return os.path.abspath(path).startswith(basedir)


# Logs all connections to server, but only performs country analysis on html files, or other non-standard requests
#   if user-name is implemented replace - - with User id
def log_connection(address, request, response_code, message):
    # prevents logging of local IP addresses due to failure interactions with ipdata.co processing these addresses
    if '192.168' not in address:
        # handles logging with common log format
        access_log = open(Path('Logs/access_log.txt'), 'a+')
        timestamp = datetime.now().strftime('%d/%b/%Y:%H:%M:%S %z')
        data = address + ' - - [' + timestamp + '] "' + request.split('\n', 1)[0].rstrip() + '" ' + response_code + ' ' + str(len(message)) + '\n'
        access_log.write(data)
        access_log.close()

        # logs full request when response_code is not 200
        if not response_code == '200':
            request_log = open(Path('Logs/Requests_log.txt'), 'a+')
            request_log.write(data + request.rstrip() + '\n___________________________________________________\n')

        # logs state and country of html file requests for analytical purposes
        ## This should use sitemap.xml, not just html for finding real visits.
        if 'html' in request.split(' ')[1][1:]:
            country_log = open(Path('Logs/Country_log.txt'), 'a+')
            ip_data = 'https://api.ipdata.co/' + address + '/?api-key=test'
            response = requests.get(ip_data).json()
            data = address + ' ' + response['region'] + ', ' + response['country_name'] + '\n'
            country_log.write(data)
            country_log.close()


def handle_connection(connection, address):
    # handles reading the request, up to 1 megabyte in size, after which size it sends 413 error
    request = ''
    # WARNING THIS LOOP IS UNTESTED, MAY NOT PROPERLY LOOP RECEIVE REQUESTS
    while True:
        part = connection.recv(1024).decode('utf-8')
        request += part
        # 4096 used as block size
        if len(part) < 4096:
            break
        elif len(request) > 4096 * 256:
            # sends 413 error to sender
            message = 'HTTP/2 413 Request Entity Too Large\n\n<html><body><center><h3>Error 413: Request Entity Too Large</h3></center></body></html>'
            response_code = '413'
            message = message.encode('utf-8')
            connection.send(message)
            connection.close()
            log_connection(address[0], request, response_code, message)
            sys.exit()

    # path of http request
    path = request.split('\n', 1)[0].split(' ')[1][1:]

    if 'GET' in request.split('\n', 1)[0]:
        message = 'HTTP/2 200 OK\nHost: www.margaretsmorsels.com\nContent-Type: '
        response_code = '200'
        # checks for illegal path traversal
        if not is_safe_path(os.getcwd(), path):
            message = 'HTTP/2 403 Forbidden\n\n<html><body><center><h3>Error 403: Forbidden</h3></center></body></html>'
            response_code = '403'
            message = message.encode('utf-8')
        else:
            # handles special exception for favicon
            if 'favicon' in path:
                path = 'site/logos/favicon.ico'
            # if 'search?' in path:
            #     term = path.split('=')[1]
            #     content = search_engine.searcher(term).encode('utf-8')
            #     message += 'text/html\nContent-Length: ' + str(len(content)) + '\n\n'
            #     message = message.encode('utf-8') + content
            else:
                if os.path.exists(path):
                    # reads file to be sent
                    # file = open(path, 'rb')
                    file = open(Path(path), 'rb')
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
                else:
                    if path == '':
                        message = 'HTTP/2 301 Moved Permanently\nLocation: /site/home.html\n\n'
                        response_code = '301'
                    else:
                        message = 'HTTP/2 404 Not Found\n\n<html><body><center><h3>Error 404: File not found</h3></center></body></html>'
                        response_code = '404'
                    message = message.encode('utf-8')
        # sends the message over socket connection
        connection.sendall(message)
        connection.close()
        # handles logging of connections
        log_connection(address[0], request, response_code, message)
        sys.exit(0)


if __name__ == "__main__":
    main()
