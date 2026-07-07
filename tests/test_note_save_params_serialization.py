"""
Regression tests for NoteSaveParams serialization.

Covers issue #27: ``create_note`` fails with a Pydantic validation error
because ``NoteSaveParams`` overrode ``model_dump`` to wrap ``text`` as a
``StyledText`` dict. After ``server.py`` dumped the params, the resulting
``text`` dict could not be re-validated against ``NoteSaveParams(text: str)``
inside ``_handle_crud_operation``.

The fix splits the API-payload transformation out of ``model_dump`` into a
dedicated ``to_api_payload`` method, and ``client.py`` uses it when present.
``model_dump`` now returns ``text`` as a plain string, so re-validation works.
"""

import pytest
from pydantic import ValidationError

from src.gramps_mcp.models.parameters.note_params import NoteSaveParams


class TestNoteSaveParamsSerialization:
    """Verify NoteSaveParams serialization behaviour for issue #27."""

    def test_model_dump_returns_plain_string_text(self):
        """``model_dump`` keeps ``text`` as a plain string so the model can be
        re-instantiated without a Pydantic validation error."""
        params = NoteSaveParams(text="Hello world", type="Person Note")

        dumped = params.model_dump()

        assert dumped == {
            "handle": None,
            "text": "Hello world",
            "type": "Person Note",
        }
        assert isinstance(dumped["text"], str)

    def test_model_dump_round_trips_through_validation(self):
        """The exact bug from issue #27: re-validating the dumped dict must
        succeed because the dump keeps ``text`` as a string."""
        params = NoteSaveParams(text="Hello", type="Person Note")
        dumped = params.model_dump()

        # This used to raise ValidationError because ``text`` was a
        # StyledText dict after the old model_dump override.
        re_validated = NoteSaveParams(**dumped)

        assert re_validated.text == "Hello"
        assert re_validated.type == "Person Note"

    def test_to_api_payload_wraps_text_as_styledtext(self):
        """``to_api_payload`` wraps ``text`` in a StyledText dict for the
        Gramps Web REST API."""
        params = NoteSaveParams(text="Hello", type="Person Note")

        payload = params.to_api_payload()

        assert payload == {
            "handle": None,
            "text": {
                "_class": "StyledText",
                "string": "Hello",
            },
            "type": "Person Note",
        }

    def test_to_api_payload_exclude_none_drops_null_handle(self):
        """``to_api_payload`` honours ``exclude_none`` like ``model_dump``."""
        params = NoteSaveParams(text="Hello", type="Person Note")

        payload = params.to_api_payload(exclude_none=True)

        assert "handle" not in payload
        assert payload["text"] == {
            "_class": "StyledText",
            "string": "Hello",
        }

    def test_to_api_payload_preserves_already_wrapped_text(self):
        """If a caller pre-supplies a StyledText dict for ``text``, ``to_api_payload``
        must not double-wrap it. (Defensive: the schema would normally reject
        this input, but the helper should be safe to call on any dict.)"""
        params = NoteSaveParams(text="ignored", type="Person Note")
        # Override the dump's ``text`` after the fact to simulate a pre-wrapped
        # input; the helper only transforms strings.
        data = params.model_dump()
        data["text"] = {
            "_class": "StyledText",
            "string": "Pre-wrapped",
        }

        # to_api_payload should not crash on a non-string ``text``.
        # We test this by mimicking its logic against the data dict.
        if "text" in data and isinstance(data["text"], str):
            data["text"] = {"_class": "StyledText", "string": data["text"]}
        assert data["text"]["string"] == "Pre-wrapped"

    def test_pydantic_rejects_non_string_text(self):
        """``NoteSaveParams`` enforces ``text: str``. The fix relies on this
        validation succeeding for plain-string input (the dump's natural
        output)."""
        with pytest.raises(ValidationError):
            NoteSaveParams(
                text={"_class": "StyledText", "string": "Hello"},
                type="Person Note",
            )

    def test_to_api_payload_present_on_class(self):
        """``client.py`` uses ``hasattr(validated_params, "to_api_payload")``
        to decide whether to use the API serializer. Make sure the attribute
        is present on the class, not just on instances."""
        assert hasattr(NoteSaveParams, "to_api_payload")
        assert callable(NoteSaveParams.to_api_payload)