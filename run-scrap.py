import asyncio
import time
import uuid
from configuration.confliguration_loader import load_config
from mora.sender_api import send_one
from mora.sender_api import send_batch
from mora.scraper import get_real_client
from mora.scraper_mock import get_mock_client

BATCH = []

last_send_time = time.time()
data_counter: int = 0

configuration = load_config()
BATCH_BY_SIZE = configuration.batch.bysize.isActive
BATCH_BY_TIME = configuration.batch.bytime.isActive
API_URL = configuration.server.address
CONTEXT_ROOT = configuration.server.context_root
RESOURCE_BATCH = configuration.server.resource_batch
RESOURCE_ONE = configuration.server.resource_one
SEND_INTERVAL_TIME = configuration.batch.bytime.interval_seconds
BATCH_SIZE = configuration.batch.bysize.size
IS_BATCH = configuration.batch.isActive
SCRAP_INTERVAL = configuration.bluetooth.scrap.interval

stop_time = None
start_time = time.time()
first_send_done = False
last_received_metrics = None


async def main():
    if not configuration.mock.send.isActive:
        client, notify_uuid, parser = await get_real_client()

        data = {
            "cadence": 25,
            "power": 180,
            "calories": 37
        }

    else:
        print("🧪 Passage en mode mock.")
        client, notify_uuid, parser = await get_mock_client()

    async with client:
        entrainement_id = str(uuid.uuid4())
        def on_notify(_, data):
            global last_send_time, data_counter, first_send_done, last_received_metrics, start_time
            raw_metrics = parser(data)
            data_counter += 1
            add_start = not first_send_done
            enriched = enrich_metrics(raw_metrics, add_start=True)
            if add_start:
                first_send_done = True
            print(f"📈 Données reçues : {enriched}")
            current_time = time.time()
            last_received_metrics = enriched
            if IS_BATCH:
                BATCH.append(enriched)

                if BATCH_BY_SIZE and data_counter >= BATCH_SIZE:
                    send_batch(BATCH, API_URL, CONTEXT_ROOT, RESOURCE_BATCH)
                    reset_data_counter()
                    BATCH.clear()
                    last_send_time = current_time

                elif BATCH_BY_TIME and (current_time - last_send_time) >= SEND_INTERVAL_TIME:
                    send_batch(BATCH, API_URL, CONTEXT_ROOT, RESOURCE_BATCH)
                    BATCH.clear()
                    last_send_time = current_time

            else:
                send_one(enriched, API_URL, CONTEXT_ROOT, RESOURCE_ONE)

        def enrich_metrics(metrics, add_start=True, add_stop=False):
            enriched = metrics.copy()
            enriched["entrainementId"] = entrainement_id
            if add_start:
                enriched["startDate"] = start_time
            if add_stop:
                enriched["stopDate"] = time.time()
            return enriched

        try:
            await client.start_notify(notify_uuid, on_notify)
            print("📡 En attente de données... (CTRL+C pour quitter)")
            while True:
                await asyncio.sleep(SCRAP_INTERVAL)
        except KeyboardInterrupt:
            print("\n🛑 Arrêt détecté, envoi de la dernière donnée avec stopDate...")
            if last_received_metrics:
                enriched_with_stop = last_received_metrics.copy()
                enriched_with_stop["stopDate"] = time.time()
                if IS_BATCH:
                    BATCH.append(enriched_with_stop)
                    send_batch(BATCH, API_URL, CONTEXT_ROOT, RESOURCE_BATCH)
                else:
                    send_one(enriched_with_stop, API_URL, CONTEXT_ROOT, RESOURCE_ONE)
        finally:
            await client.stop_notify(notify_uuid)
            await client.disconnect()




def reset_data_counter():
    global data_counter
    data_counter = 0


if __name__ == "__main__":
    asyncio.run(main())
