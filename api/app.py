from http.server import BaseHTTPRequestHandler
import json
from pywebpush import webpush, WebPushException

VAPID_PUBLIC_KEY = "BPsTWW0G_JdU2W6jAFIhH2PEOostqSapMWugVE-uRB4vOgvWi3g1CO-3y2u4srA4B69RtcVXntVtGITQmhZ6Joo"
VAPID_PRIVATE_KEY = "hm67NPd_NvUU12h9IlLRhR4WTesxO3tAvwcldZQAGNw"
VAPID_CLAIMS = {
    "sub": "mailto:test@example.com"
}


sensor_status = {
    "door": "closed",
    "gas": "normal"
}


subscriptions = []

def send_push_notification(payload_dict):
    payload = json.dumps(payload_dict)

    for sub in subscriptions:
        try:
            webpush(
                subscription_info=sub,
                data=payload,
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=VAPID_CLAIMS
            )
            print("Push notification sent")
        except WebPushException as ex:
            print("Push failed:", ex)

class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        global sensor_status, subscriptions

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body.decode())
        except Exception as e:
            print("Error parsing JSON:", e)
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode())
            return

        # If payload contains a push subscription
        if "endpoint" in data:
            subscriptions.append(data)
            print("New push subscription registered")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "subscription stored"}).encode())
            return

        # Otherwise treat it as a sensor update
        sensor = data.get("sensor")
        status = data.get("status")

        if sensor and status:
            sensor_status[sensor] = status
            print(f"Sensor '{sensor}' updated:", status)

            # If door opens, send push notification
            if sensor == "door" and status == "open":
                send_push_notification({
                    "title": "Door Alert",
                    "body": "The door was opened"
                })

             # If door opens, send push notification
            if sensor == "gas" and status == "alert":
                send_push_notification({
                    "title": "Gas Alert",
                    "body": "Dangerous gas has been detected"
                })
            

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode())

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(sensor_status).encode())