from http.server import BaseHTTPRequestHandler
import json

door_status = "closed"

class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        global door_status

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body.decode())
            door_status = data.get("door", "closed")
            print("Door status updated:", door_status)
        except Exception as e:
            print("Error parsing JSON:", e)

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(door_status.encode())