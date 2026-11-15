import re
from collections import defaultdict

_TRAILING_NUM = re.compile(r"^(.*?)(\d+)$")
_MIN_RUN = 3
# Stack-style names: prefix, member number, then at least two more numbers (1/0/1, 1/0/3/1).
_STACK_NAME = re.compile(r"^([A-Za-z-]+)\d+((?:/\d+){2,})$")


def for_stack_position(name: str, position: int | None) -> str:
    """Set the member number of a stack-style name: Gi1/0/1 at position 2 -> Gi2/0/1."""
    match = _STACK_NAME.match(name) if position is not None else None
    return name if match is None else f"{match.group(1)}{position}{match.group(2)}"


def collapse(names: list[str] | tuple[str, ...]) -> list[str]:
    """Naturally sort names and fold consecutive runs: Gi1/0/10..12 -> Gi1/0/10-12."""
    groups: dict[str, list[int]] = defaultdict(list)
    singles: list[str] = []
    for name in names:
        match = _TRAILING_NUM.match(name)
        if match:
            groups[match.group(1)].append(int(match.group(2)))
        else:
            singles.append(name)

    out: list[tuple[str, int, str]] = [(n, -1, n) for n in singles]
    for stem, nums in groups.items():
        nums.sort()
        run = [nums[0]]
        for n in [*nums[1:], None]:
            if n is not None and n == run[-1] + 1:
                run.append(n)
                continue
            if len(run) >= _MIN_RUN:
                out.append((stem, run[0], f"{stem}{run[0]}-{run[-1]}"))
            else:
                out += [(stem, r, f"{stem}{r}") for r in run]
            run = [n] if n is not None else []
    return [label for _, _, label in sorted(out, key=lambda t: (t[0], t[1]))]
