from netbox_devtype_checker.compare import compare_interfaces
from netbox_devtype_checker.models import Iface


def test_missing_superfluous_and_ok() -> None:
    device = [Iface("Gi1/0/1", "1000base-t"), Iface("Gi1/0/99", "1000base-t")]
    template = [Iface("Gi1/0/1", "1000base-t"), Iface("Gi1/0/2", "1000base-t")]
    result = compare_interfaces(device, template)
    assert result.ok_count == 1
    assert result.missing == ("Gi1/0/2",)
    assert result.superfluous == (Iface("Gi1/0/99", "1000base-t"),)


def test_type_comparison_is_optional() -> None:
    device = [Iface("Gi1/0/1", "10gbase-x-sfpp")]
    template = [Iface("Gi1/0/1", "1000base-t")]
    assert not compare_interfaces(device, template).has_findings
    strict = compare_interfaces(device, template, compare_types=True)
    assert strict.ok_count == 0
    assert strict.type_mismatches[0].expected == "1000base-t"


def test_stack_member_position_sets_first_digit() -> None:
    device = [Iface("Gi2/0/1", None), Iface("Gi2/0/3/1", None), Iface("Gi0/0", None)]
    template = [Iface("Gi1/0/1", None), Iface("Gi1/0/3/1", None), Iface("Gi0/0", None)]
    assert not compare_interfaces(device, template, vc_position=2).has_findings
    result = compare_interfaces(device, template)
    assert result.missing == ("Gi1/0/1", "Gi1/0/3/1")
