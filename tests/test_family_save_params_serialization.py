"""
Regression tests for FamilySaveParams API serialization.

Covers issue #24: ``create_family`` ignored ``child_handles`` because the
Gramps Web REST API expects children as ``child_ref_list`` (a list of
``{"ref": handle}`` dicts), not as a list of bare handle strings.

The fix adds a ``to_api_payload`` method that translates ``child_handles``
into ``child_ref_list`` only when serialising for the API call.
``model_dump`` keeps the field as ``List[str]`` so re-validation works.
"""

import pytest

from src.gramps_mcp.models.parameters.family_params import FamilySaveParams


class TestFamilySaveParamsChildHandlesSerialization:
    """Verify FamilySaveParams child-handle translation for issue #24."""

    def test_model_dump_keeps_child_handles_as_strings(self):
        """``model_dump`` must keep ``child_handles`` as a list of strings so
        the model can be re-instantiated without errors."""
        params = FamilySaveParams(child_handles=["c1", "c2", "c3"])

        dumped = params.model_dump()

        assert dumped["child_handles"] == ["c1", "c2", "c3"]
        assert "child_ref_list" not in dumped

    def test_model_dump_round_trips_through_validation(self):
        """Re-validating the dumped dict must succeed because the dump
        keeps ``child_handles`` as ``List[str]``."""
        params = FamilySaveParams(
            handle="fam1",
            father_handle="p1",
            mother_handle="p2",
            child_handles=["c1", "c2"],
        )
        dumped = params.model_dump()

        re_validated = FamilySaveParams(**dumped)

        assert re_validated.child_handles == ["c1", "c2"]
        assert re_validated.father_handle == "p1"
        assert re_validated.mother_handle == "p2"

    def test_to_api_payload_translates_child_handles_to_ref_list(self):
        """``to_api_payload`` translates ``child_handles`` (List[str]) into
        ``child_ref_list`` (List[dict]) that the Gramps Web API expects."""
        params = FamilySaveParams(child_handles=["c1", "c2"])

        payload = params.to_api_payload()

        assert payload["child_ref_list"] == [
            {"ref": "c1"},
            {"ref": "c2"},
        ]
        assert "child_handles" not in payload

    def test_to_api_payload_exclude_none_drops_unrelated_none_fields(self):
        """``to_api_payload`` honours ``exclude_none`` for fields other than
        ``child_handles``."""
        params = FamilySaveParams(
            father_handle="p1",
            child_handles=["c1"],
            note_list=None,
        )

        payload = params.to_api_payload(exclude_none=True)

        assert "handle" not in payload
        assert "mother_handle" not in payload
        assert "note_list" not in payload
        assert payload["child_ref_list"] == [{"ref": "c1"}]
        assert payload["father_handle"] == "p1"

    def test_to_api_payload_no_child_handles_leaves_payload_alone(self):
        """If no ``child_handles`` are provided, ``to_api_payload`` must not
        introduce a ``child_ref_list`` (which would tell the API to clear
        existing children). The ``child_handles`` field should also be
        omitted from the payload — the API ignores unknown fields but a
        clean payload is easier to reason about."""
        params = FamilySaveParams(handle="fam1", father_handle="p1")

        payload = params.to_api_payload()

        assert "child_ref_list" not in payload
        assert "child_handles" not in payload
        assert payload["handle"] == "fam1"
        assert payload["father_handle"] == "p1"

    def test_to_api_payload_empty_child_handles_omits_ref_list(self):
        """An empty ``child_handles`` list must not produce ``child_ref_list: []``,
        which would tell the API to clear existing children on a PUT."""
        params = FamilySaveParams(child_handles=[])

        payload = params.to_api_payload()

        assert "child_ref_list" not in payload
        assert "child_handles" not in payload

    def test_to_api_payload_present_on_class(self):
        """``client.py`` uses ``hasattr(validated_params, "to_api_payload")``
        to choose the API serializer."""
        assert hasattr(FamilySaveParams, "to_api_payload")
        assert callable(FamilySaveParams.to_api_payload)

    def test_to_api_payload_preserves_other_fields(self):
        """Adding ``to_api_payload`` must not break the rest of the payload."""
        params = FamilySaveParams(
            handle="fam1",
            father_handle="p1",
            mother_handle="p2",
            child_handles=["c1"],
            event_ref_list=[{"ref": "e1"}],
            note_list=["n1"],
            urls=[{"uri": "https://example.com"}],
            media_list=[{"ref": "m1"}],
        )

        payload = params.to_api_payload()

        assert payload == {
            "handle": "fam1",
            "father_handle": "p1",
            "mother_handle": "p2",
            "child_ref_list": [{"ref": "c1"}],
            "event_ref_list": [{"ref": "e1"}],
            "note_list": ["n1"],
            "urls": [{"uri": "https://example.com"}],
            "media_list": [{"ref": "m1"}],
        }