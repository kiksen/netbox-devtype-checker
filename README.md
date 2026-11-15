# netbox-devtype-checker (ndc)

Checks whether the interfaces of NetBox devices match their device type, so that missing and wrong interfaces become visible.

## How it works

1. ndc loads all device types defined via `filter.yaml` into a cache.
2. The devices to check are also defined via `filter.yaml`. The filters are passed on to the NetBox API.
3. For each device, its interfaces are compared against the device type in both directions:
   - **Wrong interface:** interface on the device, but not in the device type.
   - **Missing:** interface in the device type, but not on the device.
4. Which interfaces are compared is controlled solely by the `interface_filter` section of `filter.yaml`.

The cache lives in `.cache/device_types.json` (JSON), is valid for 24 hours, and is rebuilt when the `device_types` or `interface_filter` filters change or with `--refresh`.

## Installation

Requires Python `>=3.14` and [uv](https://docs.astral.sh/uv/).

```sh
uv sync
```

## Configuration

The NetBox credentials come from environment variables or, alternatively, from a `.env` file in the working directory (via pydantic-settings). Real environment variables take precedence over `.env`. Template: `cp .env.example .env`.

| Variable                       | Meaning                                                                          |
| ------------------------------ | -------------------------------------------------------------------------------- |
| `NETBOX_API` or `NETBOX_URL`   | NetBox base URL without `/api`, e.g. `http://netbox.example.com` (`NETBOX_API` wins if both are set) |
| `NETBOX_TOKEN`                 | API token                                                                        |

## filter.yaml

The content of the three sections is passed unchanged as query parameters to the NetBox REST API. The [NetBox filtering syntax](https://netboxlabs.com/docs/netbox/reference/filtering/) applies: a field name with an optional lookup suffix (`name__ic`, `type__n`, …). A list is sent as a repeated parameter (several values = OR, with `__n` = none of them).

```yaml
device_types:
  manufacturer: cisco
devices:
  manufacturer: cisco
interface_filter:
  mgmt_only: false
  type__n:
    - virtual
    - lag
    - cisco-stackwise
    - cisco-flexstack
```

| Key                | Passed to                                                     | Meaning |
| ------------------ | ------------------------------------------------------------- | ------- |
| `device_types`     | `/api/dcim/device-types/`                                     | Device types that go into the cache |
| `devices`          | `/api/dcim/devices/` (`ndc` adds the site slug)               | Devices that are checked |
| `interface_filter` | `/api/dcim/interfaces/` and `/api/dcim/interface-templates/`  | Interfaces that are compared (device and device type alike) |

All keys are optional; whatever is not set is not filtered. The example skips management-only, virtual, LAG and stack interfaces. The valid values for `type` are the interface types in NetBox, and NetBox rejects unknown ones with a 400 error. Filtering happens server-side. When the filter changes, the cache is rebuilt.

## Usage

| Option               | Meaning |
| -------------------- | ------- |
| `--filter <file>`    | Filter file, default `filter.yaml` |
| `--siteslug <slug>`  | Check only devices of this site |
| `--all`              | Check all sites (alternative to `--siteslug`) |
| `--compare-types`    | Also compare the interface type (default: names only) |
| `--changes <n>`      | Last n changes per device with deviations, counted per user (default 20, 0 = off) |
| `--refresh`          | Ignore the device type cache and reload it |
| `--output-dir <dir>` | Target folder for the reports (default `output`) |

Exit code: `0` no deviations, `1` deviations found, `2` error in invocation or configuration.

```sh
uv run ndc --siteslug berlin
uv run ndc --all
uv run ndc --all --filter other-filter.yaml
```

While running, `ndc` prints each device as it is checked (`site [3/42] device-name`).

## Output

The result is saved as a Markdown file in `output/` (the folder is in `.gitignore`). One file is created per site, e.g. `output/<YYYY-MM-DD>-<siteslug>.md`, with one section per device. With `--all`, one file per site is created.

Only deviations are listed per device. Matching interfaces are not listed individually, only counted. Devices without deviations are collected at the end under "Clean devices". Consecutive interfaces (three or more) are folded into ranges (`Gi1/0/10-24`). Wrong interfaces are listed with their NetBox type in parentheses, so the type can be added to `interface_filter` directly.

Every device is checked individually, including stack / virtual chassis members. For members, the VC position determines the first digit of the interface names: the template describes member 1 (`Gi1/0/1`), at position 2 `Gi2/0/1` is expected, at position 3 `Gi3/0/4` and so on. This also works for four-part names (`Gi2/0/3/1`). Names with fewer than three numbers (e.g. `Gi0/0`) are left unchanged. The device heading shows the position (`/ VC Member Position 2`).

Name comparison normalizes common Cisco abbreviations (`Gi1/0/1` = `GigabitEthernet1/0/1`, `Te`, `Fa`, `Eth`, `Po`, etc.) and is case-insensitive. The report shows the original names.

```markdown
# Site berlin

2 devices checked, 1 with deviations

## sw-berlin-01 (WS-C3850-48P) / VC Member Position 2

42 interfaces correct

**Missing** (in device type, not on device)
- `GigabitEthernet1/0/10-24`
- `GigabitEthernet1/0/47`

**Wrong interface** - exists on device, but not in template!
- `GigabitEthernet1/0/99` (1000base-t)

**Last 20 changes** (device and its interfaces, max 20): Max: 19 changes, Christian: 1 change

## Clean devices (1)

sw-berlin-02
```

For devices with deviations, the report also contains a line with the last changes per user. Changes to the device and its interfaces (including deleted interfaces) are taken into account.

Implementation: plain string output with `pathlib.Path.write_text`, no template package needed. One `##` section per device, bold headings, and bullet lists with inline code for interface names.

## Development

Libraries used:

- [pynetbox](https://github.com/netbox-community/pynetbox) – NetBox API client
- [typer](https://typer.tiangolo.com/) – CLI
- [rich](https://github.com/Textualize/rich) – output
- [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) – configuration from env and `.env`
