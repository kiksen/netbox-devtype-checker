from collections.abc import Iterable

from .models import Comparison, Iface, TypeMismatch
from .names import normalize


def is_ignored(iface: Iface, patterns: Iterable[str]) -> bool:
    """Case-insensitive substring match of a pattern on interface name or type."""
    haystacks = (iface.name.lower(), (iface.type or "").lower())
    return any(p.lower() in h for p in patterns for h in haystacks)


def compare_interfaces(
    device: Iterable[Iface],
    template: Iterable[Iface],
    ignore: Iterable[str] = (),
    compare_types: bool = False,
) -> Comparison:
    patterns = tuple(ignore)
    # Keys are normalized (Gi1/0/1 == GigabitEthernet1/0/1); original names are kept for display.
    dev = {normalize(i.name): i for i in device if not is_ignored(i, patterns)}
    tpl = {normalize(i.name): i for i in template if not is_ignored(i, patterns)}

    mismatches = tuple(
        TypeMismatch(dev[name].name, tpl[name].type, dev[name].type)
        for name in sorted(dev.keys() & tpl.keys())
        if compare_types and dev[name].type != tpl[name].type
    )
    common = len(dev.keys() & tpl.keys())
    return Comparison(
        ok_count=common - len(mismatches),
        missing=tuple(tpl[k].name for k in sorted(tpl.keys() - dev.keys())),
        superfluous=tuple(dev[k].name for k in sorted(dev.keys() - tpl.keys())),
        type_mismatches=mismatches,
    )
