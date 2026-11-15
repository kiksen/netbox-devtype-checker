from collections import Counter
from collections.abc import Mapping
from itertools import islice
from typing import Any

import pynetbox

from .config import FilterValue, Settings
from .models import DeviceData, DeviceTypeData, Iface

# pynetbox is untyped; its records are dynamic attribute bags.
type Record = Any


def _value(field: Record) -> str | None:
    """Choice fields come back as {'value': ..., 'label': ...} or None."""
    return None if field is None else str(field.value)


class NetBoxClient:
    """Read-only access to the NetBox objects ndc needs."""

    def __init__(self, settings: Settings, interface_filter: Mapping[str, FilterValue]) -> None:
        self._interface_filter = dict(interface_filter)
        self._nb = pynetbox.api(
            settings.netbox_api.rstrip("/"), token=settings.netbox_token.get_secret_value()
        )

    def site_slugs(self) -> list[str]:
        return sorted(s.slug for s in self._nb.dcim.sites.all())

    def device_types(self, filters: Mapping[str, FilterValue]) -> list[DeviceTypeData]:
        return [self.device_type_data(dt) for dt in self._nb.dcim.device_types.filter(**filters)]

    def device_type_by_id(self, device_type_id: int) -> DeviceTypeData:
        return self.device_type_data(self._nb.dcim.device_types.get(device_type_id))

    def device_type_data(self, dt: Record) -> DeviceTypeData:
        # NetBox silently ignores unknown filter names and returns all templates,
        # so also verify ownership on the records themselves.
        templates = [
            t
            for t in self._nb.dcim.interface_templates.filter(
                device_type_id=dt.id, **self._interface_filter
            )
            if t.device_type.id == dt.id
        ]
        return DeviceTypeData(
            id=dt.id,
            model=dt.model,
            interfaces=tuple(Iface(t.name, _value(t.type)) for t in templates),
        )

    def devices(self, site_slug: str, filters: Mapping[str, FilterValue]) -> list[DeviceData]:
        found = self._nb.dcim.devices.filter(site=site_slug, **filters)
        return [
            DeviceData(d.id, d.name or f"device-{d.id}", d.device_type.id, d.vc_position)
            for d in found
        ]

    def interfaces(self, device_id: int) -> list[tuple[int, Iface]]:
        found = self._nb.dcim.interfaces.filter(device_id=device_id, **self._interface_filter)
        return [(i.id, Iface(i.name, _value(i.type))) for i in found]

    def changes_by_user(
        self,
        device_id: int,
        interface_ids: list[int],
        missing_names: tuple[str, ...],
        limit: int,
    ) -> tuple[dict[str, int], int]:
        """Last `limit` changes on the device and its interfaces, counted per user."""
        changes = self._nb.core.object_changes
        records: list[Any] = list(
            islice(
                changes.filter(changed_object_type="dcim.device", changed_object_id=device_id),
                limit,
            )
        )
        if interface_ids:
            records += islice(
                changes.filter(
                    changed_object_type="dcim.interface", changed_object_id=interface_ids
                ),
                limit,
            )
        # Deleted interfaces no longer have an ID we know; look them up by name.
        for name in missing_names:
            deletions = changes.filter(
                changed_object_type="dcim.interface", action="delete", object_repr=name
            )
            records += [
                c
                for c in islice(deletions, limit)
                if (c.prechange_data or {}).get("device") == device_id
            ]

        records.sort(key=lambda c: c.time, reverse=True)
        latest = records[:limit]
        counts = Counter(c.user_name or "unknown" for c in latest)
        return dict(counts.most_common()), len(latest)
