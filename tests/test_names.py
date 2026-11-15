from netbox_devtype_checker.compare import compare_interfaces
from netbox_devtype_checker.models import Iface
from netbox_devtype_checker.names import collapse, for_stack_position


def test_short_form_does_not_match_long_form() -> None:
    result = compare_interfaces([Iface("Gi1/0/1", None)], [Iface("GigabitEthernet1/0/1", None)])
    assert result.missing == ("GigabitEthernet1/0/1",)
    assert result.superfluous == (Iface("Gi1/0/1", None),)


def test_collapse_folds_runs_of_three_or_more() -> None:
    names = [f"GigabitEthernet1/0/{n}" for n in (10, 11, 12, 13, 2, 3, 20)]
    assert collapse(names) == [
        "GigabitEthernet1/0/2",
        "GigabitEthernet1/0/3",
        "GigabitEthernet1/0/10-13",
        "GigabitEthernet1/0/20",
    ]


def test_collapse_keeps_names_without_number() -> None:
    assert collapse(["mgmt", "Gi0/1"]) == ["Gi0/1", "mgmt"]


def test_for_stack_position() -> None:
    assert for_stack_position("Gi1/0/4", 3) == "Gi3/0/4"
    assert for_stack_position("TenGigabitEthernet1/0/3/1", 2) == "TenGigabitEthernet2/0/3/1"
    assert for_stack_position("Gi0/0", 2) == "Gi0/0"
    assert for_stack_position("Gi1/0/4", None) == "Gi1/0/4"
