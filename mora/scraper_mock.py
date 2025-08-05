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
    flags = (
        (1 << 0) |  # stroke rate
        (1 << 1) |  # stroke count
        (1 << 2) |  # avg_cadence_spm
        (1 << 3) |  # distance_m
        (1 << 4) |  # power_w
        (1 << 5) |  # avg_power_w
        (1 << 6) |  # resistance_level
        (1 << 7) |  # calories_kcal
        (1 << 8) |  # heart_rate_bpm
        (1 << 9) |  # elapsed time
        (1 << 10) |  # remaining_time_s
        (1 << 11) |  # avg_pace_500m_s
        (1 << 12)   # inst_pace_500m_s
    )

    data = bytearray()
    data += flags.to_bytes(2, "little")
    data += random.randint(20, 35).to_bytes(1, "little")          # cadence_spm (1 byte)
    data += random.randint(100, 500).to_bytes(2, "little")        # stroke_count (2 bytes)
    data += random.randint(20, 35).to_bytes(1, "little")          # avg_cadence_spm (1 byte)
    data += random.randint(1000, 5000).to_bytes(3, "little")      # distance_m (3 bytes)
    data += random.randint(100, 300).to_bytes(2, "little")        # power_w (2 bytes)
    data += random.randint(100, 300).to_bytes(2, "little")        # avg_power_w (2 bytes)
    data += random.randint(1, 10).to_bytes(1, "little")           # resistance_level (1 byte)
    data += random.randint(50, 300).to_bytes(2, "little")         # calories_kcal (2 bytes)
    data += random.randint(80, 160).to_bytes(1, "little")         # heart_rate_bpm (1 byte)
    data += random.randint(100, 1000).to_bytes(2, "little")       # elapsed_time_s (×0.1) (2 bytes)
    data += random.randint(100, 1000).to_bytes(2, "little")       # remaining_time_s (×0.1) (2 bytes)
    data += random.randint(200, 500).to_bytes(2, "little")        # avg_pace_500m_s (×0.01) (2 bytes)
    data += random.randint(200, 500).to_bytes(2, "little")        # inst_pace_500m_s (×0.01) (2 bytes)

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

    async def stop_notify(self, uuid):
        pass

    async def disconnect(self):
        pass


async def get_mock_client():
    return MockBleakClient(), "mock-rower-data", parse_rower_data