from fastapi import APIRouter, HTTPException, status

from app.evaluators.registry import evaluator_registry
from app.probes.base import ProbeContext
from app.probes.registry import probe_registry
from app.schemas.probe import EvaluatorRead, ProbeRead, ProbeRunRequest, ProbeRunResponse
from app.services.target_adapters import TargetAdapterError, target_adapter_registry

router = APIRouter(tags=["probes"])


@router.get("/probes", response_model=list[ProbeRead])
async def list_probes(attribute: str | None = None, jurisdiction: str | None = None) -> list[ProbeRead]:
    """List probes, optionally narrowed by attribute and jurisdiction.

    A jurisdiction filter also returns the jurisdiction-neutral (`cross`) probes, since
    those carry no region-specific name signal.
    """
    probes = probe_registry.filter(attribute=attribute, jurisdiction=jurisdiction)
    return [
        ProbeRead(
            id=probe.id,
            name=probe.name,
            description=probe.description,
            attribute=probe.attribute,
            groups=list(getattr(probe, "groups", {}).keys()),
            jurisdiction=getattr(probe, "jurisdiction", "cross"),
            source=getattr(probe, "source", ""),
            legal_basis=getattr(probe, "legal_basis", ""),
        )
        for probe in probes
    ]


@router.get("/evaluators", response_model=list[EvaluatorRead])
async def list_evaluators() -> list[EvaluatorRead]:
    return [
        EvaluatorRead(id=item.id, name=item.name, description=item.description, metric=item.metric)
        for item in evaluator_registry.list()
    ]


@router.post("/probes/{probe_id}/run", response_model=ProbeRunResponse)
async def run_probe(probe_id: str, payload: ProbeRunRequest) -> ProbeRunResponse:
    """Run one probe on its own, without creating an audit. Useful while developing probes."""
    try:
        probe = probe_registry.get(probe_id)
        evaluator = evaluator_registry.get(payload.evaluator_id)
        adapter = target_adapter_registry.get(payload.provider)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TargetAdapterError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    case = await probe.generate(ProbeContext(target_id=payload.target_id, configuration=payload.configuration))
    configuration = {**payload.configuration, "model_name": payload.model_name}

    responses: dict[str, str] = {}
    errors: dict[str, str] = {}
    for variant in case.variants:
        try:
            responses[variant.group] = await adapter.complete(variant.prompt, configuration)
        except TargetAdapterError as exc:
            responses[variant.group] = ""
            errors[variant.group] = str(exc)
        except Exception as exc:  # one bad arm must not abort the probe
            # Providers raise their own exception types for a malformed model name, a bad
            # base URL or a transport failure. Letting those escape turns an operator
            # mistake into an opaque 500; recording them per arm keeps the other arms
            # usable and puts the reason in the response.
            responses[variant.group] = ""
            errors[variant.group] = f"{type(exc).__name__}: {exc}"

    observation = await probe.execute(case, responses, errors)
    evaluation = await evaluator.evaluate(observation)
    return ProbeRunResponse(
        probe_id=probe.id,
        attribute=probe.attribute,
        prompts=observation.prompts,
        responses=observation.responses,
        evaluation=evaluation,
    )
