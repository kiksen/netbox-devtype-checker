import json
from pathlib import Path

from netbox_devtype_checker.cache import load_cache, save_cache
from netbox_devtype_checker.models import DeviceTypeData, Iface


def test_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "c.json"
    types = {1: DeviceTypeData(1, "X", (Iface("Gi1/0/1", "1000base-t"),))}
    save_cache(path, {}, types)
    assert load_cache(path, {}) == types


def test_cache_without_current_version_is_discarded(tmp_path: Path) -> None:
    path = tmp_path / "c.json"
    save_cache(path, {}, {})
    raw = json.loads(path.read_text())
    del raw["version"]
    path.write_text(json.dumps(raw))
    assert load_cache(path, {}) is None
