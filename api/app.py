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
    "garden_door": "closed",
    "gas": "normal"
}

# Control de cooldown para evitar spam de notificaciones
import time
import random
last_sent = {
    "door": 0,
    "garden_door": 0,
    "gas": 0
}
COOLDOWN_SECONDS = 5

# Control remoto de detección (guardado en Redis)
def get_sensor_state(sensor):
    state = redis_client.get(f"detection:{sensor}")
    if state is None:
        redis_client.set(f"detection:{sensor}", "true")
        return True
    return state == "true"


def set_sensor_state(sensor, value: bool):
    redis_client.set(f"detection:{sensor}", "true" if value else "false")


def send_push_notification(payload_dict):
    # Agregar ID corto + timestamp para hacer cada notificación única
    unique_id = random.randint(1000, 9999)
    payload_dict["id"] = unique_id
    payload_dict["timestamp"] = time.time()

    # Hacer el mensaje único directamente en el backend (visible)
    if "body" in payload_dict:
        payload_dict["body"] = f'{payload_dict["body"]} #{unique_id}'

    payload = json.dumps(payload_dict)

    subs = redis_client.smembers("subscriptions")

    for sub_json in subs:
        try:
            sub = json.loads(sub_json)
            print(f"Enviando a: {sub.get('endpoint')[:30]}...")
            webpush(
                subscription_info=sub,
                data=payload,
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=VAPID_CLAIMS,
                ttl=86400 # 24 horas para asegurar entrega
            )
            print("✅ Push notification sent successfully")

        except WebPushException as ex:
            print(f"❌ Push failed: {ex}")
            if ex.response and ex.response.status_code in [404, 410]:
                print("Eliminando suscripción caducada")
                redis_client.srem("subscriptions", sub_json)
        except Exception as e:
            print(f"⚠️ Error general en webpush: {e}")

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

        # Control remoto por sensor
        if "sensor_control" in data:
            sensor = data.get("sensor_control")
            state = data.get("state")

            if sensor in ["door", "garden_door", "gas"]:
                if isinstance(state, bool):
                    set_sensor_state(sensor, state)
                elif isinstance(state, str):
                    set_sensor_state(sensor, state.lower() in ["true", "on", "1", "enabled"])

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "door": get_sensor_state("door"),
                "garden_door": get_sensor_state("garden_door"),
                "gas": get_sensor_state("gas")
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
            
            # Notificaciones Push (solo si detección está habilitada + cooldown)
            try:
                current_time = time.time()

                # DOOR
                if sensor == "door" and status == "open":
                    if get_sensor_state("door"):
                        if current_time - last_sent.get("door", 0) > COOLDOWN_SECONDS:
                            send_push_notification({
                                "title": "Alerta Puerta",
                                "body": "Abierta"
                            })
                            last_sent["door"] = current_time

                # GARDEN DOOR
                if sensor == "garden_door" and status == "open":
                    if get_sensor_state("garden_door"):
                        if current_time - last_sent.get("garden_door", 0) > COOLDOWN_SECONDS:
                            send_push_notification({
                                "title": "Alerta Puerta Jardín",
                                "body": "Abierta"
                            })
                            last_sent["garden_door"] = current_time

                # GAS
                if sensor == "gas" and (status == "alert" or status == "danger"):
                    if get_sensor_state("gas"):
                        if current_time - last_sent["gas"] > COOLDOWN_SECONDS:
                            send_push_notification({
                                "title": "Alerta Gas",
                                "body": "Peligro detectado"
                            })
                            last_sent["gas"] = current_time

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
            "detection": {
                "door": get_sensor_state("door"),
                "garden_door": get_sensor_state("garden_door"),
                "gas": get_sensor_state("gas")
            }
        }

        self.wfile.write(json.dumps(response).encode())