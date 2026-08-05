from app.core.enums import InputType, StepName
from app.workflows.definitions import get_workflow, validate_workflow


def test_source_video_has_transcription_step() -> None:
    workflow = get_workflow(InputType.SOURCE_VIDEO)
    validate_workflow(workflow)
    names = [step.name for step in workflow]
    assert StepName.TRANSCRIBE_MEDIA in names
    assert names.index(StepName.TRANSCRIBE_MEDIA) < names.index(StepName.PREPARE_SCRIPT)


def test_script_skips_transcription() -> None:
    workflow = get_workflow(InputType.SCRIPT)
    validate_workflow(workflow)
    names = [step.name for step in workflow]
    assert StepName.TRANSCRIBE_MEDIA not in names


def test_render_waits_for_parallel_branches() -> None:
    workflow = get_workflow(InputType.TITLE_PROMPT)
    render = next(step for step in workflow if step.name == StepName.RENDER_VIDEO)
    assert set(render.depends_on) == {
        StepName.PLAN_SCENES,
        StepName.GENERATE_VOICE,
        StepName.COLLECT_ASSETS,
        StepName.GENERATE_SUBTITLES,
    }
