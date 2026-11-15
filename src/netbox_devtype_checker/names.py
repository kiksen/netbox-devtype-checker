import re
from collections import defaultdict

# Cisco short forms -> canonical long form (lowercase). Only used for matching, never displayed.
_ALIASES = {
    "fa": "fastethernet",
    "gi": "gigabitethernet",
    "te": "tengigabitethernet",
    "twe": "twentyfivegige",
    "tw": "twogigabitethernet",
    "fo": "fortygige",
    "fortygigabitethernet": "fortygige",
    "hu": "hundredgige",
    "eth": "ethernet",
    "po": "port-channel",
    "vl": "vlan",
    "lo": "loopback",
}
_SPLIT = re.compile(r"^([A-Za-z-]+)(\d.*)$")
_TRAILING_NUM = re.compile(r"^(.*?)(\d+)$")
_MIN_RUN = 3


def normalize(name: str) -> str:
    """Matching key: lowercase with common interface prefix abbreviations expanded."""
    match = _SPLIT.match(name.strip())
    if not match:
        return name.strip().lower()
    prefix, rest = match.group(1).lower(), match.group(2)
    return f"{_ALIASES.get(prefix, prefix)}{rest}"


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
