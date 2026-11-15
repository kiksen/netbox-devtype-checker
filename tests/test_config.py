from pathlib import Path

import pytest
from pydantic import ValidationError

from netbox_devtype_checker.config import Settings, load_filter


@pytest.mark.parametrize("name", ["NETBOX_API", "NETBOX_URL"])
def test_url_accepted_under_both_names(name: str, monkeypatch: pytest.MonkeyPatch) -> None:
    for var in ("NETBOX_API", "NETBOX_URL"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv(name, "http://netbox.example.com")
    monkeypatch.setenv("NETBOX_TOKEN", "t")
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.netbox_api == "http://netbox.example.com"


def test_netbox_api_wins_over_netbox_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NETBOX_API", "http://api.example.com")
    monkeypatch.setenv("NETBOX_URL", "http://url.example.com")
    monkeypatch.setenv("NETBOX_TOKEN", "t")
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.netbox_api == "http://api.example.com"


def test_repo_filter_yaml_passes_rest_syntax_through() -> None:
    cfg = load_filter(Path("filter.yaml"))
    assert cfg.interface_filter["mgmt_only"] is False
    assert cfg.interface_filter["type__n"] != []
    assert cfg.devices == {"manufacturer": "cisco"}


def test_unknown_top_level_key_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "f.yaml"
    path.write_text("interface_filters:\n  mgmt_only: false\n")
    with pytest.raises(ValidationError):
        load_filter(path)
