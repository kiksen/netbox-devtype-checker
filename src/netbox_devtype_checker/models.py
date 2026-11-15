from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Iface:
    name: str
    type: str | None


@dataclass(frozen=True, slots=True)
class DeviceTypeData:
    id: int
    model: str
    interfaces: tuple[Iface, ...]


@dataclass(frozen=True, slots=True)
class DeviceData:
    id: int
    name: str
    device_type_id: int
    vc_position: int | None = None


@dataclass(frozen=True, slots=True)
class TypeMismatch:
    name: str
    expected: str | None
    actual: str | None


@dataclass(frozen=True, slots=True)
class Comparison:
    ok_count: int
    missing: tuple[str, ...]
    superfluous: tuple[Iface, ...]
    type_mismatches: tuple[TypeMismatch, ...]

    @property
    def has_findings(self) -> bool:
        return bool(self.missing or self.superfluous or self.type_mismatches)


@dataclass(frozen=True, slots=True)
class DeviceResult:
    device: DeviceData
    type_model: str
    comparison: Comparison
    changes_by_user: dict[str, int] = field(default_factory=dict)
    changes_total: int = 0
