from http.server import BaseHTTPRequestHandler
import json


sensor_status = {
    "door": "closed",
    "gas": "normal"
}

subscriptions = []

class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        global sensor_status, subscriptions

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        # Route: /api/subscribe  -> save push subscription
        if self.path == "/api/subscribe":
            try:
                data = json.loads(body.decode())
                subscriptions.append(data)
                print("New push subscription registered")
            except Exception as e:
                print("Error parsing subscription:", e)

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Subscription stored")
            return

        # Default route -> sensor updates
        try:
            data = json.loads(body.decode())
            sensor = data.get("sensor")
            status = data.get("status")

            if sensor and status:
                sensor_status[sensor] = status
                print(f"Sensor '{sensor}' updated:", status)
        except Exception as e:
            print("Error parsing JSON:", e)

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps(sensor_status).encode())