from http.server import BaseHTTPRequestHandler
import json

sensor_status = {
    "door": "closed",
    "gas": "normal"
}

class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        global sensor_status

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

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