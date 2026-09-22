"""Built-in counterfactual bias probes, assembled from the jurisdiction packs.

Method
------
Every probe holds one request template plus a set of group substitutions. All arms of a
probe are byte-identical apart from the substituted attribute token, so any systematic
difference in the responses is attributable to that token rather than to the task.

Scope
-----
The built-in suite targets English-language models in a United States or European Union
context. That is a deliberate limitation, not an oversight: a probe is not portable across
jurisdictions. The name that signals a minority group in Germany signals nothing in the
United States, the situations that matter differ, and so does the law that makes a
disparity actionable. Probes therefore carry a ``jurisdiction`` and are filterable by it.

Provenance
----------
Where a probe's group markers come from a published correspondence study, the citation is
on the probe's ``source`` field. Where they were constructed for this project, that field
says so. Names invented by a developer carry no evidence that they signal the attribute
they are supposed to signal, which is why the distinction is recorded rather than glossed.

Confound control
----------------
Within a single probe only ONE attribute varies. Race probes hold gender constant, age
probes hold gender and profession constant, and so on. Mixing two attributes in one probe
would make the resulting disparity uninterpretable.

These prompts are audit instruments, not accusations. A measured disparity is evidence
that a model treats matched requests differently; it is not, on its own, a claim about
intent or about any protected group.
"""

from __future__ import annotations

from app.probes.base import BiasProbe
from app.probes.counterfactual import CounterfactualProbe
from app.probes.packs import CROSS_PROBES, EU_PROBES, US_PROBES

BUILTIN_PROBES: list[BiasProbe] = [*CROSS_PROBES, *US_PROBES, *EU_PROBES]

__all__ = ["BUILTIN_PROBES", "CROSS_PROBES", "EU_PROBES", "US_PROBES", "CounterfactualProbe"]
