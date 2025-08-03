from bleak import BleakClient, BleakScanner

FTMS_UUID = "00001826-0000-1000-8000-00805f9b34fb"
ROWER_DATA_UUID = "00002ad1-0000-1000-8000-00805f9b34fb"


def parse_rower_data(data: bytearray):
    offset = 0
    flags = int.from_bytes(data[offset:offset + 2], byteorder="little")
    offset += 2
    result = {}

    def read(size: int, scale: float = 1.0):
        nonlocal offset
        val = int.from_bytes(data[offset:offset + size], byteorder="little")
        offset += size
        return val * scale

    fields = [
        (0, "cadenceSpm", 1),
        (1, "strokeCount", 2),
        (2, "avgCadenceSpm", 1),
        (3, "distanceM", 3),
        (4, "powerW", 2),
        (5, "avgPowerW", 2),
        (6, "resistanceLevel", 1),
        (7, "caloriesKcal", 2),
        (8, "heartRateBpm", 1),
        (9, "elapsedTimeS", 2, 0.1),
        (10, "remainingTimeS", 2, 0.1),
        (11, "avgPace500mS", 2, 0.01),
        (12, "instPace500mS", 2, 0.01),
    ]

    for bit, name, size, *scale in fields:
        if flags & (1 << bit):
            result[name] = read(size, scale[0] if scale else 1.0)

    return result


async def get_real_client():
    print("🔍 Recherche d’un périphérique FTMS...")
    devices = await BleakScanner.discover()
    target = None
    for device in devices:
        uuids = device.metadata.get("uuids", [])
        if uuids and FTMS_UUID.lower() in [s.lower() for s in uuids]:
            target = device
            break

    if not target:
        raise Exception("Aucun périphérique FTMS trouvé.")

    print(f"✅ Périphérique trouvé : {target.name} ({target.address})")
    client = BleakClient(target)
    return client, ROWER_DATA_UUID, parse_rower_data
