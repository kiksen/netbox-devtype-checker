from pathlib import Path
from typing import Annotated

import pydantic
import typer
from rich.console import Console
from rich.table import Table

from .cache import DEFAULT_CACHE_FILE, load_cache, save_cache
from .compare import compare_interfaces
from .config import FilterConfig, Filters, Settings, load_filter
from .models import DeviceResult, DeviceTypeData
from .netbox import NetBoxClient
from .report import write_site_report

app = typer.Typer(
    add_completion=False, help="Check NetBox device interfaces against their device type."
)
console = Console()
err = Console(stderr=True)


def _fail(message: str) -> typer.Exit:
    err.print(f"[red]error:[/red] {message}")
    return typer.Exit(code=2)


def _cache_key(cfg: FilterConfig) -> dict[str, Filters]:
    # Templates are fetched with interface_filter, so it must invalidate the cache too.
    return {"device_types": cfg.device_types, "interface_filter": cfg.interface_filter}


def _device_types(
    client: NetBoxClient, cfg: FilterConfig, refresh: bool
) -> dict[int, DeviceTypeData]:
    cached = None if refresh else load_cache(DEFAULT_CACHE_FILE, _cache_key(cfg))
    if cached is not None:
        console.print(f"Device types: {len(cached)} from cache ({DEFAULT_CACHE_FILE})")
        return cached
    types = {t.id: t for t in client.device_types(cfg.device_types)}
    save_cache(DEFAULT_CACHE_FILE, _cache_key(cfg), types)
    console.print(f"Device types: {len(types)} fetched from NetBox")
    return types


def _check_site(
    client: NetBoxClient,
    site: str,
    cfg: FilterConfig,
    types: dict[int, DeviceTypeData],
    compare_types: bool,
    change_limit: int,
) -> list[DeviceResult]:
    results: list[DeviceResult] = []
    devices = client.devices(site, cfg.devices)
    for n, device in enumerate(devices, start=1):
        console.print(f"[dim]{site} [{n}/{len(devices)}][/dim] {device.name}")
        if device.device_type_id not in types:  # type outside the device_types filter
            types[device.device_type_id] = client.device_type_by_id(device.device_type_id)
        dtype = types[device.device_type_id]
        found = client.interfaces(device.id)
        comparison = compare_interfaces(
            (i for _, i in found),
            dtype.interfaces,
            compare_types,
            device.vc_position,
        )
        by_user: dict[str, int] = {}
        total = 0
        if comparison.has_findings and change_limit > 0:
            by_user, total = client.changes_by_user(
                device.id, [i for i, _ in found], comparison.missing, change_limit
            )
        results.append(DeviceResult(device, dtype.model, comparison, by_user, total))
    return results


@app.command()
def main(
    filter_file: Annotated[Path, typer.Option("--filter", help="Filter YAML file.")] = Path(
        "filter.yaml"
    ),
    siteslug: Annotated[str | None, typer.Option(help="Check only this site.")] = None,
    all_sites: Annotated[bool, typer.Option("--all", help="Check all sites.")] = False,
    compare_types: Annotated[
        bool,
        typer.Option("--compare-types", help="Also compare interface types (default: names only)."),
    ] = False,
    changes: Annotated[
        int,
        typer.Option(
            help="Recent changes to summarize per user for devices with findings (0 = off)."
        ),
    ] = 20,
    refresh: Annotated[
        bool, typer.Option(help="Ignore the device type cache and re-fetch.")
    ] = False,
    output_dir: Annotated[Path, typer.Option(help="Directory for the markdown reports.")] = Path(
        "output"
    ),
) -> None:
    if bool(siteslug) == all_sites:
        raise _fail("use exactly one of --siteslug <slug> or --all")
    try:
        settings = Settings()  # type: ignore[call-arg]  # values come from env / .env
        cfg = load_filter(filter_file)
    except pydantic.ValidationError as exc:
        names = ", ".join(str(e["loc"][0]) for e in exc.errors())
        raise _fail(
            f"invalid configuration: {names} (set NETBOX_API and NETBOX_TOKEN in env or .env)"
        ) from exc
    except OSError as exc:
        raise _fail(f"cannot read filter file: {exc}") from exc

    client = NetBoxClient(settings, cfg.interface_filter)
    types = _device_types(client, cfg, refresh)
    sites = client.site_slugs() if all_sites else [siteslug or ""]

    table = Table("Site", "Devices", "With deviations", "Report")
    any_findings = False
    known = set(types)
    for site in sites:
        results = _check_site(client, site, cfg, types, compare_types, changes)
        if not results:
            continue
        path = write_site_report(output_dir, site, results, changes)
        flagged = sum(r.comparison.has_findings for r in results)
        any_findings |= flagged > 0
        table.add_row(site, str(len(results)), str(flagged), str(path))
    # Only write when new types were fetched; rewriting would renew the TTL of stale data.
    if set(types) != known:
        save_cache(DEFAULT_CACHE_FILE, _cache_key(cfg), types)
    console.print(table)
    raise typer.Exit(code=1 if any_findings else 0)
