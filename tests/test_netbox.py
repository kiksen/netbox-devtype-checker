from types import SimpleNamespace

from netbox_devtype_checker.netbox import NetBoxClient


def _template(name: str, device_type_id: int) -> SimpleNamespace:
    return SimpleNamespace(
        name=name,
        type=SimpleNamespace(value="1000base-t"),
        device_type=SimpleNamespace(id=device_type_id),
    )


class _FakeTemplates:
    """Mimics NetBox ignoring an unknown filter: returns templates of all types."""

    def filter(self, **_: int) -> list[SimpleNamespace]:
        return [_template("Gi1/0/1", 1), _template("Te1/0/1", 2)]


def test_templates_of_other_device_types_are_dropped() -> None:
    client = NetBoxClient.__new__(NetBoxClient)  # bypass __init__ (network)
    client._interface_filter = {}
    client._nb = SimpleNamespace(dcim=SimpleNamespace(interface_templates=_FakeTemplates()))
    data = client.device_type_data(SimpleNamespace(id=1, model="X"))
    assert [i.name for i in data.interfaces] == ["Gi1/0/1"]


class _Recorder:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def filter(self, **kwargs: object) -> list[SimpleNamespace]:
        self.calls.append(kwargs)
        return []


def test_interface_filter_is_passed_to_templates_and_interfaces() -> None:
    templates, interfaces = _Recorder(), _Recorder()
    client = NetBoxClient.__new__(NetBoxClient)  # bypass __init__ (network)
    client._interface_filter = {"mgmt_only": False, "type__n": ["virtual"]}
    client._nb = SimpleNamespace(
        dcim=SimpleNamespace(interface_templates=templates, interfaces=interfaces)
    )
    client.device_type_data(SimpleNamespace(id=1, model="X"))
    client.interfaces(5)
    assert templates.calls == [{"device_type_id": 1, "mgmt_only": False, "type__n": ["virtual"]}]
    assert interfaces.calls == [{"device_id": 5, "mgmt_only": False, "type__n": ["virtual"]}]
