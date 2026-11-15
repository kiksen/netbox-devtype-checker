from collections.abc import Iterable

from .models import Comparison, Iface, TypeMismatch
from .names import for_stack_position, normalize


def compare_interfaces(
    device: Iterable[Iface],
    template: Iterable[Iface],
    compare_types: bool = False,
    vc_position: int | None = None,
) -> Comparison:
    # Keys are normalized (Gi1/0/1 == GigabitEthernet1/0/1); original names are kept for display.
    dev = {normalize(i.name): i for i in device}
    # Templates describe member 1; a stack member at position N carries N as first number.
    tpl = {
        normalize(name): Iface(name, i.type)
        for i in template
        for name in [for_stack_position(i.name, vc_position)]
    }

    mismatches = tuple(
        TypeMismatch(dev[name].name, tpl[name].type, dev[name].type)
        for name in sorted(dev.keys() & tpl.keys())
        if compare_types and dev[name].type != tpl[name].type
    )
    common = len(dev.keys() & tpl.keys())
    return Comparison(
        ok_count=common - len(mismatches),
        missing=tuple(tpl[k].name for k in sorted(tpl.keys() - dev.keys())),
        superfluous=tuple(dev[k] for k in sorted(dev.keys() - tpl.keys())),
        type_mismatches=mismatches,
    )
