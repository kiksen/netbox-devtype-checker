from collections import defaultdict
from datetime import date
from pathlib import Path

from .models import DeviceResult, Iface
from .names import collapse


def _plural(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def _with_types(ifaces: tuple[Iface, ...]) -> list[str]:
    """One line per interface type, runs folded within a type: - `Gi1/0/10-12` (1000base-t)."""
    by_type: dict[str, list[str]] = defaultdict(list)
    for i in ifaces:
        by_type[i.type or "unknown type"].append(i.name)
    return [
        f"- `{label}` ({kind})"
        for kind, names in sorted(by_type.items())
        for label in collapse(names)
    ]


def render_device(r: DeviceResult, change_limit: int) -> str:
    c = r.comparison
    vc = f" / VC Member Position {r.device.vc_position}" if r.device.vc_position else ""
    lines = [
        f"## {r.device.name} ({r.type_model}){vc}",
        "",
        f"{_plural(c.ok_count, 'interface')} correct",
        "",
    ]
    if c.missing:
        lines += [
            "**Missing** (in device type, not on device)",
            *(f"- `{n}`" for n in collapse(c.missing)),
            "",
        ]
    if c.superfluous:
        lines += [
            "**Wrong interface** - exists on device, but not in template!",
            *_with_types(c.superfluous),
            "",
        ]
    if c.type_mismatches:
        lines += [
            "**Type mismatch**",
            *(
                f"- `{m.name}`: device type `{m.expected}`, device `{m.actual}`"
                for m in c.type_mismatches
            ),
            "",
        ]
    if r.changes_by_user:
        who = ", ".join(f"{user}: {_plural(n, 'change')}" for user, n in r.changes_by_user.items())
        scope = "device and its interfaces"
        lines.append(f"**Last {r.changes_total} changes** ({scope}, max {change_limit}): {who}")
    else:
        lines.append("**Recent changes**: none found")
    return "\n".join(lines).rstrip()


def render_site(site_slug: str, results: list[DeviceResult], change_limit: int) -> str:
    with_findings = sum(r.comparison.has_findings for r in results)
    header = [
        f"# Site {site_slug}",
        "",
        f"{_plural(len(results), 'device')} checked, {with_findings} with deviations",
        "",
    ]
    flagged = sorted((r for r in results if r.comparison.has_findings), key=lambda r: r.device.name)
    clean = sorted(r.device.name for r in results if not r.comparison.has_findings)
    sections = [render_device(r, change_limit) for r in flagged]
    if clean:
        sections.append(f"## Clean devices ({len(clean)})\n\n" + ", ".join(clean))
    return "\n".join(header) + "\n" + "\n\n".join(sections) + "\n"


def write_site_report(
    output_dir: Path,
    site_slug: str,
    results: list[DeviceResult],
    change_limit: int,
    today: date | None = None,
) -> Path:
    path = output_dir / f"{(today or date.today()).isoformat()}-{site_slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_site(site_slug, results, change_limit))
    return path
