# Python-http-Server
This project is designed to create a lightweight python3 http server that can be used to host websites without a need for a LAMP service stack.
There is a non secure version that uses standard HTTP and a secure version that uses TLS (SSL certificates acquired separately).
# How to use
This project is designed to create a lightweight python3 http server that can be used to host websites without a need for a LAMP service stack.
There is a non secure version that uses standard HTTP and a secure version that uses TLS (SSL certificates acquired separately).

# How to use non-secure version
Place the server.py file in the topmost directory of your website's directories.  Start the server using python3.  Using a browser you can now access your website using your local ip (192.168.XXX.XXX) and your chosen port (default port of 4200) followed by the path and filename of the html file.

For example:

192.168.XXX.XXX:4200/file.html

192.168.XXX.XXX:4200/path/to/file/file.html


This project does not currently work on linux and has not been tested for mac