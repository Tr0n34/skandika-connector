import requests
import json
from urllib.parse import urljoin


def build_url(server_addr: str, root_context: str, resource: str) -> str:
    root = "/".join(part.strip("/") for part in [root_context, resource])
    url = urljoin(server_addr.rstrip("/") + "/", root)
    print(f"🔗 URL construite : {url}")
    return url


def send_one(data: dict, server_addr: str, root_context: str, resource: str):
    send(data, server_addr, root_context, resource)


def send_batch(data: list[dict], server_addr: str, root_context: str, resource: str):
    send(data, server_addr, root_context, resource)


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
