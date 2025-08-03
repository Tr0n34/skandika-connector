import asyncio
import random


def parse_rower_data(data: bytearray):
    flags = int.from_bytes(data[0:2], byteorder="little")
    offset = 2
    result = {}

    def read(size: int, scale: float = 1.0):
        nonlocal offset
        val = int.from_bytes(data[offset:offset + size], byteorder="little")
        offset += size
        return val * scale

    fields = [
        (0,  "cadence_spm",         1, 1.0),
        (1,  "stroke_count",        2, 1.0),
        (2,  "avg_cadence_spm",     1, 1.0),
        (3,  "distance_m",          3, 1.0),
        (4,  "power_w",             2, 1.0),
        (5,  "avg_power_w",         2, 1.0),
        (6,  "resistance_level",    1, 1.0),
        (7,  "calories_kcal",       2, 1.0),
        (8,  "heart_rate_bpm",      1, 1.0),
        (9,  "elapsed_time_s",      2, 0.1),
        (10, "remaining_time_s",    2, 0.1),
        (11, "avg_pace_500m_s",     2, 0.01),
        (12, "inst_pace_500m_s",    2, 0.01),
    ]

    for bit, key, size, scale in fields:
        if flags & (1 << bit):
            result[key] = read(size, scale)

    return result


def fake_rower_data():
    # Simule des flags pour : cadence, stroke count, power, calories, heart rate, elapsed time
    flags = (
        (1 << 0) |  # stroke rate
        (1 << 1) |  # stroke count
        (1 << 4) |  # power
        (1 << 7) |  # calories
        (1 << 8) |  # heart rate
        (1 << 9)    # elapsed time
    )

    data = bytearray()
    data += flags.to_bytes(2, "little")
    data += random.randint(20, 35).to_bytes(1, "little")          # cadence
    data += random.randint(100, 500).to_bytes(2, "little")        # stroke count
    data += random.randint(150, 300).to_bytes(2, "little")        # power
    data += random.randint(0, 0).to_bytes(2, "little")            # padding for distance (not used)
    data += random.randint(50, 150).to_bytes(2, "little")         # calories
    data += random.randint(80, 130).to_bytes(1, "little")         # heart rate
    data += random.randint(100, 300).to_bytes(2, "little")        # elapsed time (10s unit)

    return data


class MockBleakClient:
    def __init__(self):
        self.connected = False

    async def __aenter__(self):
        self.connected = True
        print("✅ Mock connecté")
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.connected = False
        print("🔌 Mock déconnecté")

    async def start_notify(self, uuid, callback):
        async def simulate():
            while self.connected:
                data = fake_rower_data()
                callback(uuid, data)
                await asyncio.sleep(1)

        asyncio.create_task(simulate())


async def get_mock_client():
    return MockBleakClient(), "mock-rower-data", parse_rower_data