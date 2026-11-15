from datetime import date
from pathlib import Path

from netbox_devtype_checker.models import Comparison, DeviceData, DeviceResult, Iface
from netbox_devtype_checker.report import render_site, write_site_report


def _result(name: str, missing: tuple[str, ...], users: dict[str, int]) -> DeviceResult:
    comparison = Comparison(ok_count=42, missing=missing, superfluous=(), type_mismatches=())
    return DeviceResult(DeviceData(1, name, 1), "C3850", comparison, users, sum(users.values()))


def test_render_lists_findings_and_counts_ok() -> None:
    text = render_site("berlin", [_result("sw-1", ("Gi1/0/48",), {"Max": 20, "Christian": 1})], 20)
    assert "- `Gi1/0/48`" in text
    assert "42 interfaces correct" in text
    assert "Max: 20 changes, Christian: 1 change" in text


def test_clean_device_has_no_change_summary() -> None:
    text = render_site("berlin", [_result("sw-1", (), {})], 20)
    assert "## Clean devices (1)" in text
    assert "## sw-1 " not in text
    assert "changes" not in text


def test_filename_has_date_and_slug(tmp_path: Path) -> None:
    path = write_site_report(tmp_path, "berlin", [], 20, today=date(2025, 5, 12))
    assert path.name == "2025-05-12-berlin.md"


def test_long_missing_list_is_collapsed() -> None:
    missing = tuple(f"GigabitEthernet1/0/{n}" for n in range(1, 25))
    text = render_site("berlin", [_result("sw-1", missing, {"Max": 3})], 20)
    assert "- `GigabitEthernet1/0/1-24`" in text


def test_heading_shows_vc_member_position() -> None:
    comparison = Comparison(ok_count=1, missing=("Gi2/0/2",), superfluous=(), type_mismatches=())
    result = DeviceResult(DeviceData(1, "sw-2", 1, 2), "C9200L-24P-4G", comparison)
    assert "## sw-2 (C9200L-24P-4G) / VC Member Position 2\n" in render_site("x", [result], 20)


def test_wrong_interfaces_show_their_type() -> None:
    wrong = (Iface("Po1", "lag"), Iface("Te2/1/1", "10gbase-x-sfpp"), Iface("Te2/1/2", None))
    comparison = Comparison(ok_count=1, missing=(), superfluous=wrong, type_mismatches=())
    text = render_site("x", [DeviceResult(DeviceData(1, "sw", 1), "T", comparison)], 20)
    assert "- `Po1` (lag)" in text
    assert "- `Te2/1/1` (10gbase-x-sfpp)" in text
    assert "- `Te2/1/2` (unknown type)" in text
