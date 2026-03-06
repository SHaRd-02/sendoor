from http.server import BaseHTTPRequestHandler

door_status = "closed"

class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        global door_status

        door_status = "open"

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(door_status.encode())