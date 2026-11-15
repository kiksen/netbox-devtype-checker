from datetime import date
from pathlib import Path

from .models import DeviceResult
from .names import collapse


def _plural(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def render_device(r: DeviceResult, change_limit: int) -> str:
    c = r.comparison
    lines = [
        f"## {r.device.name} ({r.type_model})",
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
            "**Superfluous** (on device, not in device type)",
            *(f"- `{n}`" for n in collapse(c.superfluous)),
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
