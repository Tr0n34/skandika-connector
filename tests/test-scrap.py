import asyncio
import random


# 👇 Ceci simule ce que tu reçois du rameur réel
def fake_rower_data():
    cadence = random.randint(20, 30)
    power = random.randint(100, 300)
    calories = random.randint(10, 50)

    # ⚠️ Structure binaire simplifiée (8+ octets selon FTMS)
    return bytearray([
        0x00, 0x00,  # Flags (fictif)
        cadence,  # Stroke rate
        power & 0xFF,  # Power LSB
        (power >> 8) & 0xFF,  # Power MSB
        0x00, 0x00,  # Placeholder
        calories & 0xFF,
        (calories >> 8) & 0xFF
    ])


# 👻 Mock du client BLE
class MockBleakClient:
    def __init__(self, *args, **kwargs):
        self.connected = False

    async def __aenter__(self):
        print("✅ Mock client connecté")
        self.connected = True
        return self

    async def __aexit__(self, exc_type, exc, tb):
        print("🔌 Mock client déconnecté")
        self.connected = False

    async def start_notify(self, uuid, callback):
        print(f"📡 Simule les notifications sur {uuid}")

        # Boucle de test : envoie des données toutes les secondes
        async def fake_loop():
            while self.connected:
                data = fake_rower_data()
                callback(uuid, data)
                await asyncio.sleep(1)

        await asyncio.create_task(fake_loop())


def parse_rower_data(data: bytearray):
    flags = int.from_bytes(data[0:2], byteorder="little")
    stroke_rate = data[2]
    power = int.from_bytes(data[3:5], byteorder="little")
    calories = int.from_bytes(data[7:9], byteorder="little")

    return {
        "cadence": stroke_rate,
        "power": power,
        "calories": calories
    }


# 🎬 Programme principal avec injection du mock
async def main():
    async with MockBleakClient() as client:
        def handle_notification(_, data):
            row = parse_rower_data(data)
            print(f"📈 Données simulées : {row}")

        await client.start_notify("mock-rower-data", handle_notification)
        while True:
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
