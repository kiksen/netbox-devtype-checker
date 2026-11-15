import hashlib
import json
import time
from collections.abc import Mapping
from pathlib import Path

from .config import Filters
from .models import DeviceTypeData, Iface

DEFAULT_CACHE_FILE = Path(".cache/device_types.json")
DEFAULT_TTL_SECONDS = 24 * 3600
# Bump when the cached data may be wrong (e.g. after a fetch bug), so old caches are discarded.
CACHE_VERSION = 3


def filter_hash(filters: Mapping[str, Filters]) -> str:
    return hashlib.sha256(json.dumps(filters, sort_keys=True).encode()).hexdigest()[:16]


def load_cache(
    path: Path, filters: Mapping[str, Filters], ttl: int = DEFAULT_TTL_SECONDS
) -> dict[int, DeviceTypeData] | None:
    """Return cached device types, or None if missing, stale or built for other filters."""
    try:
        raw = json.loads(path.read_text())
    except OSError, json.JSONDecodeError:
        return None
    if (
        raw.get("version") != CACHE_VERSION
        or raw.get("filter_hash") != filter_hash(filters)
        or time.time() - raw.get("fetched_at", 0) > ttl
    ):
        return None
    return {
        int(dt_id): DeviceTypeData(
            id=int(dt_id),
            model=dt["model"],
            interfaces=tuple(Iface(i["name"], i["type"]) for i in dt["interfaces"]),
        )
        for dt_id, dt in raw["device_types"].items()
    }


def save_cache(
    path: Path, filters: Mapping[str, Filters], types: Mapping[int, DeviceTypeData]
) -> None:
    payload = {
        "version": CACHE_VERSION,
        "filter_hash": filter_hash(filters),
        "fetched_at": time.time(),
        "device_types": {
            str(t.id): {
                "model": t.model,
                "interfaces": [{"name": i.name, "type": i.type} for i in t.interfaces],
            }
            for t in types.values()
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))
