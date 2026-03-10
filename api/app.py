from http.server import BaseHTTPRequestHandler
import json
from pywebpush import webpush, WebPushException
import os
import redis

# Intentamos obtener cualquiera de las dos, priorizando REDIS_URL
redis_url = os.environ.get("KV_REDIS_URL") or os.environ.get("REDIS_URL")

# decode_responses=True es clave para que Redis nos devuelva texto y no bytes
redis_client = redis.Redis.from_url(
    redis_url, 
    decode_responses=True
)

VAPID_PUBLIC_KEY = "BPsTWW0G_JdU2W6jAFIhH2PEOostqSapMWugVE-uRB4vOgvWi3g1CO-3y2u4srA4B69RtcVXntVtGITQmhZ6Joo"
VAPID_PRIVATE_KEY = "hm67NPd_NvUU12h9IlLRhR4WTesxO3tAvwcldZQAGNw"
VAPID_CLAIMS = {
    "sub": "mailto:test@example.com"
}


sensor_status = {
    "door": "closed",
    "gas": "normal"
}

# Control remoto de detección (guardado en Redis)
def detection_enabled():
    state = redis_client.get("detection_enabled")
    if state is None:
        # default habilitado
        redis_client.set("detection_enabled", "true")
        return True
    return state == "true"


def set_detection_state(value: bool):
    redis_client.set("detection_enabled", "true" if value else "false")


def send_push_notification(payload_dict):
    payload = json.dumps(payload_dict)

    subs = redis_client.smembers("subscriptions")

    for sub_json in subs:
        sub = json.loads(sub_json)

        try:
            webpush(
                subscription_info=sub,
                data=payload,
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=VAPID_CLAIMS,
                ttl=60
            )

            print("Push notification sent")

        except WebPushException as ex:
            print("Push failed:", ex)

            if ex.response and ex.response.status_code in [404, 410]:
                redis_client.srem("subscriptions", sub_json)

class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            self.send_response(400)
            self.end_headers()
            return

        body = self.rfile.read(content_length)

        try:
            data = json.loads(body.decode())
        except Exception as e:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Malformed JSON"}).encode())
            return

        # Control remoto de detección
        if "detection" in data:
            new_state = data.get("detection")

            if isinstance(new_state, bool):
                set_detection_state(new_state)
            elif isinstance(new_state, str):
                set_detection_state(new_state.lower() in ["true", "on", "1", "enabled"])

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "detection": detection_enabled()
            }).encode())
            return

        # Registro de suscripciones
        if "endpoint" in data:
            redis_client.sadd("subscriptions", json.dumps(data))
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "stored"}).encode())
            return

        # Actualización de sensores
        sensor = data.get("sensor")
        status = data.get("status")

        if sensor in sensor_status:
            sensor_status[sensor] = status
            
            # Notificaciones Push (solo si detección está habilitada)
            try:
                if not detection_enabled():
                    print("Detección deshabilitada, no se envía push")
                else:
                    if sensor == "door" and status == "open":
                        send_push_notification({"title": "Alerta Puerta", "body": "Abierta"})
                    
                    # REVISA ESTO: En tu ESP32 mandas "danger", pero aquí buscas "alert"
                    if sensor == "gas" and (status == "alert" or status == "danger"):
                        send_push_notification({"title": "Alerta Gas", "body": "Peligro detectado"})
            except Exception as e:
                print(f"Error en Push: {e}") 
                # No retornamos error 400 aquí para que el ESP32 reciba el OK
        
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode())

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        response = {
            "sensors": sensor_status,
            "detection_enabled": detection_enabled()
        }

        self.wfile.write(json.dumps(response).encode())