from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        print("Door opened")
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"door_open")