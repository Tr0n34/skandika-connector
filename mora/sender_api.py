import requests
import json
from urllib.parse import urljoin
from typing import Optional


def build_url(server_addr: str, root_context: str, resource: str) -> str:
    root = "/".join(part.strip("/") for part in [root_context, resource])
    url = urljoin(server_addr.rstrip("/") + "/", root)
    print(f"🔗 URL construite : {url}")
    return url


def send_one(data: dict, server_addr: str, root_context: str, resource: str):
    send(data, server_addr, root_context, resource)


def send_batch(data: list[dict], server_addr: str, root_context: str, resource: str):
    send(data, server_addr, root_context, resource)


def start(device_id: str, server_addr: str, root_context: str, resource: str, verb: str) -> Optional[str]:
    try:
        print(f"START")
        url = f"{server_addr}{root_context}{resource}{verb}"
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json={
                "device_id": device_id
            }
        )
        if response.ok:
            print(f"✅ Démarrage entraînement ({response.status_code}) : {response.headers}")
            training_id = response.json()
        else:
            print(f"❌ Échec de l’envoi (HTTP {response.status_code}) : {response.text}")
        return training_id
    except Exception as e:
        print(f"❌ Échec de l’envoi : {e}")


def stop(training_id: int, device_id: str, server_addr: str, root_context: str, resource: str, verb: str):
    try:
        print(f"STOP")
        url = f"{server_addr}{root_context}{resource}/{training_id}{verb}"
        response = requests.patch(
            url,
            headers={"Content-Type": "application/json"},
            json={
                "device_id": device_id
            }
        )
        if response.ok:
            print(f"✅ Fin de l'entraînement ({response.status_code}) : {response.headers}")
            response_data = response.json()
        else:
            print(f"❌ Échec de l’envoi (HTTP {response.status_code}) : {response.text}")
    except Exception as e:
        print(f"❌ Échec de l’envoi : {e}")


def send(data: list[dict], server_addr: str, root_context: str, resource: str):
    try:
        url = build_url(server_addr, root_context, resource)
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(data)
        )
        if response.ok:
            print(f"✅ Envoi réussi ({response.status_code}) : {response.headers}")
        else:
            print(f"❌ Échec de l’envoi (HTTP {response.status_code}) : {response.text}")
    except Exception as e:
        print(f"❌ Échec de l’envoi : {e}")
