from http.server import BaseHTTPRequestHandler
import json
import time

door_status = "closed"
last_open_time = 0

COOLDOWN = 40  # segundos

class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        global door_status, last_open_time

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body.decode())

            if data.get("door") == "open":
                door_status = "open"
                last_open_time = time.time()
                print("Door opened")

        except Exception as e:
            print("Error parsing JSON:", e)

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")


    def do_GET(self):
        global door_status

        # revisar cooldown
        if door_status == "open":
            if time.time() - last_open_time > COOLDOWN:
                door_status = "closed"
                print("Door auto closed")

        self.send_response(200)
        self.end_headers()
        self.wfile.write(door_status.encode())