from netbox_devtype_checker.compare import compare_interfaces
from netbox_devtype_checker.models import Iface


def test_missing_superfluous_and_ok() -> None:
    device = [Iface("Gi1/0/1", "1000base-t"), Iface("Gi1/0/99", "1000base-t")]
    template = [Iface("Gi1/0/1", "1000base-t"), Iface("Gi1/0/2", "1000base-t")]
    result = compare_interfaces(device, template)
    assert result.ok_count == 1
    assert result.missing == ("Gi1/0/2",)
    assert result.superfluous == ("Gi1/0/99",)


def test_ignore_matches_name_or_type_case_insensitive() -> None:
    device = [Iface("Vlan1", "virtual"), Iface("StackPort1", "other")]
    template = [Iface("Gi1/0/1", "1000base-t")]
    result = compare_interfaces(device, template, ignore=["stack", "VIRTUAL"])
    assert result.superfluous == ()
    assert result.missing == ("Gi1/0/1",)


def test_type_comparison_is_optional() -> None:
    device = [Iface("Gi1/0/1", "10gbase-x-sfpp")]
    template = [Iface("Gi1/0/1", "1000base-t")]
    assert not compare_interfaces(device, template).has_findings
    strict = compare_interfaces(device, template, compare_types=True)
    assert strict.ok_count == 0
    assert strict.type_mismatches[0].expected == "1000base-t"
