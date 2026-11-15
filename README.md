# netbox-devtype-checker (ndc)

Prüft, ob die Interfaces von NetBox-Devices zu ihrem Device-Type passen. So werden überflüssige und fehlende Interfaces sichtbar.

## Funktionsweise

1. ndc liest alle Device-Types, die über `filter.yaml` definiert sind, in einen Cache ein.
2. Die Devices, die geprüft werden sollen, werden ebenfalls über `filter.yaml` bestimmt. Die Filter werden dazu an die NetBox-API übergeben.
3. Für jedes Device werden die Interfaces gegen den Device-Type verglichen, in beide Richtungen:
   - **Überflüssig:** Interface am Device, aber nicht im Device-Type.
   - **Fehlend:** Interface im Device-Type, aber nicht am Device.
4. Interfaces, die in `interface_filter` eingetragen sind, werden nicht geprüft.

Der Cache liegt in `.cache/device_types.json` (JSON), gilt 24 Stunden und wird bei geänderten `device_types`-Filtern oder mit `--refresh` neu aufgebaut.

## Installation

Voraussetzung: Python `>=3.14` und [uv](https://docs.astral.sh/uv/).

```sh
uv sync
```

## Konfiguration

Die NetBox-Zugangsdaten kommen aus Umgebungsvariablen oder alternativ aus einer `.env`-Datei im Arbeitsverzeichnis (via pydantic-settings). Echte Umgebungsvariablen haben Vorrang vor `.env`. Vorlage: `cp .env.example .env`.

| Variable        | Bedeutung                                  |
| --------------- | ------------------------------------------ |
| `NETBOX_API`    | Adresse der NetBox-API (Basis-URL ohne `/api`, z. B. `http://netbox.example.com`)  |
| `NETBOX_TOKEN`  | API-Token                                  |

## filter.yaml

```yaml
device_types:
  manufacturer: cisco
devices:
  manufacturer: cisco
interface_filter:
  - stack
  - virtual
```

| Schlüssel          | Bedeutung                                           |
| ------------------ | --------------------------------------------------- |
| `device_types`     | Filter für die Device-Types, die in den Cache kommen |
| `devices`          | Filter für die Devices, die geprüft werden          |
| `interface_filter` | Interfaces, die nicht geprüft werden (case-insensitive Teilstring-Match auf Interface-Name oder -Typ) |

## Verwendung

| Option              | Bedeutung                                   |
| ------------------- | ------------------------------------------- |
| `--filter <datei>`  | Filterdatei, Default: `filter.yaml`         |
| `--siteslug <slug>` | Nur Devices dieser Site prüfen              |
| `--all`             | Alle Sites prüfen (Alternative zu `--siteslug`) |
| `--compare-types`   | Zusätzlich den Interface-Typ vergleichen (Default: nur Namen) |
| `--changes <n>`     | Letzte n Changes je Device mit Abweichungen, pro User gezählt (Default 20, 0 = aus) |
| `--refresh`         | Device-Type-Cache ignorieren und neu laden |
| `--output-dir <dir>`| Zielordner für die Reports (Default `output`) |

Exit-Code: `0` keine Abweichungen, `1` Abweichungen gefunden, `2` Fehler in Aufruf oder Konfiguration.

```sh
uv run ndc --siteslug berlin
uv run ndc --all
uv run ndc --all --filter andere-filter.yaml
```

## Ausgabe

Das Ergebnis wird als Markdown-Datei in `output/` gespeichert (Ordner ist in `.gitignore`). Pro Site entsteht eine Datei, z. B. `output/<YYYY-MM-DD>-<siteslug>.md`, mit einem Abschnitt je Device. Bei `--all` entsteht eine Datei je Site.

Pro Device werden nur Abweichungen aufgelistet. Passende Interfaces werden nicht einzeln genannt, nur ihre Anzahl. Devices ohne Abweichungen stehen gesammelt am Ende unter „Clean devices". Aufeinanderfolgende Interfaces (ab drei) werden zu Bereichen zusammengefasst (`Gi1/0/10-24`).

Der Namensvergleich normalisiert gängige Cisco-Kürzel (`Gi1/0/1` = `GigabitEthernet1/0/1`, `Te`, `Fa`, `Eth`, `Po` usw.) und ist case-insensitive. Im Report stehen die Originalnamen.

```markdown
# Site berlin

2 devices checked, 1 with deviations

## sw-berlin-01 (WS-C3850-48P)

42 interfaces correct

**Missing** (in device type, not on device)
- `GigabitEthernet1/0/10-24`
- `GigabitEthernet1/0/47`

**Superfluous** (on device, not in device type)
- `GigabitEthernet1/0/99`

**Last 20 changes** (device and its interfaces, max 20): Max: 19 changes, Christian: 1 change

## Clean devices (1)

sw-berlin-02
```

Der Report ist englisch. Bei Devices mit Abweichungen steht zusätzlich die Zeile mit den letzten Changes pro User. Berücksichtigt werden Changes am Device und an seinen Interfaces (inkl. gelöschter Interfaces).

Umsetzung: einfache String-Ausgabe mit `pathlib.Path.write_text`, kein Template-Paket nötig. Pro Device ein `##`-Abschnitt, Fett-Überschriften und Bullet-Listen mit Inline-Code für Interface-Namen.

## Entwicklung

Verwendete Bibliotheken:

- [pynetbox](https://github.com/netbox-community/pynetbox) – NetBox-API-Client
- [typer](https://typer.tiangolo.com/) – CLI
- [rich](https://github.com/Textualize/rich) – Ausgabe
- [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) – Konfiguration aus ENV und `.env`
