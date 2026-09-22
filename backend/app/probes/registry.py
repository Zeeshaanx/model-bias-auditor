from __future__ import annotations

from app.probes.base import BiasProbe
from app.probes.builtins import BUILTIN_PROBES


class ProbeRegistry:
    """Holds every probe the platform can run. New probes register here without touching workflow code."""

    def __init__(self) -> None:
        self._probes: dict[str, BiasProbe] = {}
        for probe in BUILTIN_PROBES:
            self.register(probe)

    def register(self, probe: BiasProbe) -> None:
        self._probes[probe.id] = probe

    def list(self) -> list[BiasProbe]:
        return list(self._probes.values())

    def ids(self) -> list[str]:
        return list(self._probes.keys())

    def by_attribute(self, attribute: str) -> list[BiasProbe]:
        return [probe for probe in self._probes.values() if probe.attribute == attribute]

    def by_jurisdiction(self, jurisdiction: str) -> list[BiasProbe]:
        """Probes valid in one jurisdiction, including the jurisdiction-neutral ones.

        Running a US audit should not include German names, but it should include the
        probes whose signal is stated in the prompt and therefore travels.
        """
        return [
            probe
            for probe in self._probes.values()
            if probe.jurisdiction in (jurisdiction, "cross")
        ]

    def filter(self, attribute: str | None = None, jurisdiction: str | None = None) -> list[BiasProbe]:
        probes = self.list()
        if attribute:
            probes = [probe for probe in probes if probe.attribute == attribute]
        if jurisdiction:
            probes = [probe for probe in probes if probe.jurisdiction in (jurisdiction, "cross")]
        return probes

    def get(self, probe_id: str) -> BiasProbe:
        if probe_id not in self._probes:
            raise KeyError(f"Unknown probe: {probe_id}")
        return self._probes[probe_id]


probe_registry = ProbeRegistry()
