from __future__ import annotations

from dataclasses import dataclass

from app.core.enums import InputType, StepName


@dataclass(frozen=True, slots=True)
class StepDefinition:
    name: StepName
    queue: str
    depends_on: tuple[StepName, ...] = ()


COMMON_AFTER_SCRIPT: tuple[StepDefinition, ...] = (
    StepDefinition(StepName.PLAN_SCENES, "ai", (StepName.PREPARE_SCRIPT,)),
    StepDefinition(StepName.GENERATE_VOICE, "audio", (StepName.PREPARE_SCRIPT,)),
    StepDefinition(StepName.COLLECT_ASSETS, "assets", (StepName.PREPARE_SCRIPT, StepName.PLAN_SCENES)),
    StepDefinition(
        StepName.GENERATE_SUBTITLES,
        "audio",
        (StepName.PREPARE_SCRIPT, StepName.GENERATE_VOICE),
    ),
    StepDefinition(
        StepName.RENDER_VIDEO,
        "render",
        (
            StepName.PLAN_SCENES,
            StepName.GENERATE_VOICE,
            StepName.COLLECT_ASSETS,
            StepName.GENERATE_SUBTITLES,
        ),
    ),
    StepDefinition(StepName.QUALITY_CHECK, "render", (StepName.RENDER_VIDEO,)),
    StepDefinition(StepName.FINALIZE_MANIFEST, "default", (StepName.QUALITY_CHECK,)),
)


def get_workflow(input_type: InputType) -> tuple[StepDefinition, ...]:
    ingest = StepDefinition(StepName.INGEST_INPUT, "default")

    if input_type in {InputType.SOURCE_VIDEO, InputType.VOICE}:
        prefix = (
            ingest,
            StepDefinition(StepName.TRANSCRIBE_MEDIA, "audio", (StepName.INGEST_INPUT,)),
            StepDefinition(StepName.PREPARE_SCRIPT, "ai", (StepName.TRANSCRIBE_MEDIA,)),
        )
    else:
        prefix = (
            ingest,
            StepDefinition(StepName.PREPARE_SCRIPT, "ai", (StepName.INGEST_INPUT,)),
        )

    return prefix + COMMON_AFTER_SCRIPT


def validate_workflow(definitions: tuple[StepDefinition, ...]) -> None:
    names = [item.name for item in definitions]
    if len(names) != len(set(names)):
        raise ValueError("A workflow cannot contain duplicate step names")

    known: set[StepName] = set()
    for item in definitions:
        unknown = set(item.depends_on) - set(names)
        if unknown:
            raise ValueError(f"Unknown dependencies for {item.name}: {unknown}")
        if any(dependency not in known for dependency in item.depends_on):
            raise ValueError(f"Workflow is not topologically ordered at {item.name}")
        known.add(item.name)
