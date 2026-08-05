import pytest
from pydantic import ValidationError

from app.core.enums import InputType
from app.schemas.projects import ProjectCreate


def test_script_input_requires_script() -> None:
    with pytest.raises(ValidationError):
        ProjectCreate(name="demo", input_type=InputType.SCRIPT)


def test_source_video_requires_prompt_and_uri() -> None:
    with pytest.raises(ValidationError):
        ProjectCreate(name="demo", input_type=InputType.SOURCE_VIDEO, source_video_uri="video.mp4")


def test_voice_input_is_valid() -> None:
    request = ProjectCreate(name="demo", input_type=InputType.VOICE, voice_uri="voice.mp3")
    assert request.to_input_payload() == {"voice_uri": "voice.mp3"}
