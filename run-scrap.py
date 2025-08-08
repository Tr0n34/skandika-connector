import asyncio
import time
import uuid
from configuration.confliguration_loader import load_config
from mora.sender_api import send_one
from mora.sender_api import send_batch
from mora.sender_api import start
from mora.sender_api import stop
from mora.scraper import get_real_client
from mora.scraper_mock import get_mock_client

BATCH = []

data_counter: int = 0

configuration = load_config()
BATCH_BY_SIZE = configuration.batch.bysize.isActive
BATCH_BY_TIME = configuration.batch.bytime.isActive
API_URL = configuration.server.address
CONTEXT_ROOT = configuration.server.context_root
RESOURCE_BATCH = configuration.resources.row_data.url_batch
RESOURCE_ONE = configuration.resources.row_data.url_one
RESOURCE_TRAINING = configuration.resources.trainings.uri
VERB_START = configuration.resources.trainings.verbs.start
VERB_STOP = configuration.resources.trainings.verbs.stop
SEND_INTERVAL_TIME = configuration.batch.bytime.interval_seconds
BATCH_SIZE = configuration.batch.bysize.size
IS_BATCH = configuration.batch.isActive
SCRAP_INTERVAL = configuration.bluetooth.scrap.interval

last_send_time = None
first_data_received = asyncio.Event()


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
        device_id = str(uuid.uuid4())

        def on_notify(_, data):
            global data_counter, last_send_time
            if not first_data_received.is_set():
                first_data_received.set()
            # Appeler start training renvoie un trainingId
            raw_metrics = parser(data)
            data_counter += 1
            enriched = enrich_metrics(raw_metrics)
            print(f"📈 Données reçues : {enriched}")
            current_time = time.time()
            if IS_BATCH:
                BATCH.append(enriched)
                if BATCH_BY_SIZE and data_counter >= BATCH_SIZE:
                    send_batch(BATCH, API_URL, CONTEXT_ROOT, RESOURCE_BATCH)
                    reset_data_counter()
                    BATCH.clear()
                elif BATCH_BY_TIME and (current_time - last_send_time) >= SEND_INTERVAL_TIME:
                    send_batch(BATCH, API_URL, CONTEXT_ROOT, RESOURCE_BATCH)
                    BATCH.clear()
                    last_send_time = current_time
            else:
                send_one(enriched, API_URL, CONTEXT_ROOT, RESOURCE_ONE)

        def enrich_metrics(metrics):
            enriched = metrics.copy()
            enriched["device_id"] = device_id
            enriched["training_id"] = training_id
            return enriched

        try:
            training_id = start(device_id, API_URL, CONTEXT_ROOT, RESOURCE_TRAINING, VERB_START)
            await client.start_notify(notify_uuid, on_notify)
            while True:
                await asyncio.sleep(SCRAP_INTERVAL)
        except asyncio.CancelledError:
            print("🛑 Tâche annulée proprement.")
        except KeyboardInterrupt:
            print("\n🛑 Arrêt détecté, envoi de la dernière donnée avec stopDate...")
        finally:
            stop(training_id, device_id, API_URL, CONTEXT_ROOT, RESOURCE_TRAINING, VERB_STOP)
            await client.stop_notify(notify_uuid)
            await client.disconnect()


def reset_data_counter():
    global data_counter
    data_counter = 0


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    main_task = loop.create_task(main())

    try:
        loop.run_until_complete(main_task)
    except KeyboardInterrupt:
        print("⏹️ Arrêt manuel détecté, annulation de la tâche...")
        main_task.cancel()
        loop.run_until_complete(main_task)
    finally:
        loop.close()
