from http.server import BaseHTTPRequestHandler
import json
import redis

# Redis connection (used to store push subscriptions)
r = redis.Redis(host="localhost", port=6379, decode_responses=True)

from pywebpush import webpush

# VAPID configuration (replace with your generated keys)
VAPID_PRIVATE_KEY = "MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgfclRPjJjSQ0kmNL6I4Vwy+NfjHbwznOYTd/B8ACfLPihRANCAAQuxeKOWturjBqhK+3vRG421ifNH+z7jKNJQkmDHxRA2L8/36pg76w3g49bEseYNgYErG7QMIIEx6dIcaaQkIQj"
VAPID_SUB = "mailto:admin@example.com"


def send_notification(subscription, title, body):

    webpush(
        subscription_info=subscription,
        data=json.dumps({
            "title": title,
            "body": body
        }),
        vapid_private_key=VAPID_PRIVATE_KEY,
        vapid_claims={
            "sub": VAPID_SUB
        }
    )


def notify_all(title, body):

    subs = r.lrange("subscriptions", 0, -1)

    for s in subs:
        try:
            send_notification(json.loads(s), title, body)
        except Exception as e:
            print("Notification error:", e)


sensor_status = {
    "door": "closed",
    "gas": "normal"
}

class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        global sensor_status

        # Endpoint to register push subscriptions
        if self.path == "/subscribe":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)

            try:
                subscription = json.loads(body.decode())
                r.rpush("subscriptions", json.dumps(subscription))
                print("New subscription saved")
            except Exception as e:
                print("Subscription error:", e)

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"subscribed")
            return

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body.decode())
            sensor = data.get("sensor")
            status = data.get("status")

            if sensor and status:
                sensor_status[sensor] = status
                print(f"Sensor '{sensor}' updated:", status)
            
            if sensor == "gas" and status == "alert":
                notify_all("⚠ Gas Alert", "Gas detected!")

            if sensor == "door" and status == "open":
                notify_all("🚪 Door Open", "The door has been opened")

        except Exception as e:
            print("Error parsing JSON:", e)

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def do_GET(self):

        response = {
            "door": door_status,
            "gas": gas_status
        }

        self.send_response(200)
        self.send_header("Content-Type","application/json")
        self.end_headers()

        self.wfile.write(json.dumps(response).encode())