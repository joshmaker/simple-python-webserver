import os
import socket


class BrowserRequest(object):
    """Represents a browser request

    Userful parameters include:
    request.verb         -- GET, POST, HEAD, etc
    request.path         -- /path/to/file.html
    request.http_version -- HTTP
    request.user_agent   -- Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) Ap..
    """

    def __init__(self, text):
        self.info = {}
        lines = [r.strip() for r in text.split("\n")]

        # First line takes the form of
        # GET /file/path/ HTTP/1.1
        action = lines.pop(0).split(" ")
        self.info['verb'] = action[0]  # GET, POST, etc
        if os.path.basename(action[1]) == "":
            self.info['path'] = os.path.join(action[1], 'index.html')
        else:
            self.info['path'] = action[1]
        self.info['http_version'] = action[0]

        for line in lines:
            i = line.find(':')
            var = line[:i].strip().lower().replace('-', '_')
            val = line[i + 1:].strip()
            self.info[var] = val

    def __getattr__(self, attr):
        return self.info.get(attr)


class ServerSocketError(Exception):
    pass


class ServerSocket(object):
    """Simplified interface for interacting with a web server socket"""

    def __init__(self, host='', port=80, buffer_size=1024,
            max_queued_connections=5):
        self.is_open = False
        self.client_conn = None
        self.server_conn = None
        self.host = host
        self.port = int(port)
        self.buffer_size = buffer_size
        self.max_queued_connections = max_queued_connections

    def open(self):
        if self.is_open:
            raise ServerSocketError('Socket is already open')

        self.server_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_conn.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_conn.bind((self.host, self.port))
        self.server_conn.listen(self.max_queued_connections)
        self.is_open = True

    def recieve(self, buffer_size=None):
        self.close_open_client_connections()
        self.client_conn, _ = self.server_conn.accept()
        return self.client_conn.recv(buffer_size or self.buffer_size)

    def send(self, data=None):
        if not self.client_conn:
            raise ServerSocketError('No client connection open for sending')
        for d in data:
            self.client_conn.send(d)

    def close_open_client_connections(self):
        if self.client_conn:
            self.client_conn.close()
            self.client_conn = None

    def close(self):
        self.close_open_client_connections()
        self.server_conn.close()
        self.is_open = False


class SimpleServer(object):
    """A Simple webserver implemented in Python. NOT FOR PRODUCTION USE"""

    STATUSES = {
        200: 'OK',
        404: 'File not found',
    }
    default_404 = '<html><h1>404 File Not Found</h1></html>'

    def __init__(self, port=80, homedir='./', page404=None):
        """Initialize a webserver

        port    -- port to server requests from
        homedir -- path to serve files out of
        page404 -- optional path to HTML file for 404 errors
        """

        self.socket = ServerSocket(port=port)
        self.homedir = os.path.abspath(homedir)
        self.page404 = page404

    def log(self, msg):
        """Logs a message. By default, prints to the screen but this
        could be overwritten to write to a file, etc
        """
        print msg

    def log_request(self, status, request):
        self.log("{status} - {verb} {path} {user_agent}".format(
                status=status, verb=request.verb,
                path=self.get_requested_path(request),
                user_agent=request.user_agent))

    def start(self):
        self.log("Listening on port {0}, serving files in {1}".format(
                self.port, self.homedir))
        self.socket.open()

    def serve(self):
        if not self.socket.is_open:
            self.start()

        request = self.socket.recieve()
        if request:
            request = BrowserRequest(request)
            status, data = self.process_request(request)
            self.log_request(status, request)
            self.socket.send(data)
        return request

    def serve_forever(self):
        while True:
            self.serve()

    def process_request(self, request):
        requested_file = self.get_requested_path(request)
        if os.path.exists(requested_file):
            status = 200
            data = (self.get_header(status), open(requested_file).read())
            return (status, data)
        else:
            status = 404
            html = open(self.page404).read() if self.page404 else self.default_404
            data = (self.get_header(status), html)
            return (status, data)

    def get_header(self, code):
        return "HTTP/1.0 {0} {1}\n\n".format(code, self.STATUSES[code])

    def get_requested_path(self, request):
        path = request.path
        if path[0] == '/':
            path = path[1:]
        return os.path.join(self.homedir, path)

    def stop(self):
        self.log('Shutting down server')
        self.socket.close()
