"""
Regression tests for EventSaveParams API serialization (issue #38).

``create_event`` and ``update_event`` (POST/PUT ``/events``) silently
ignored the user-supplied ``citation_list`` and ``note_list`` handles because
the Gramps Web REST API expects those fields as ``[{"ref": handle}]``
references but ``EventSaveParams`` defines them as plain ``List[str]``.

These tests pin down the ``EventSaveParams.to_api_payload`` contract that
makes those references reach the API:

- ``citation_list`` (required) is translated to ``[{"ref": handle}]``.
- ``note_list`` (optional) is translated the same way when present.
- ``note_list`` of ``None`` or ``[]`` is omitted from the API payload so a
  ``PUT`` does not clobber existing notes.
- ``model_dump`` keeps the user-friendly ``List[str]`` shape so the model
  can be re-validated or inspected.
"""

from src.gramps_mcp.models.parameters.event_params import EventSaveParams


class TestEventSaveParamsCitationListSerialization:
    """``citation_list`` is required and must be translated to refs."""

    def test_required_citation_list_becomes_ref_list(self):
        params = EventSaveParams(
            type="Birth",
            citation_list=["c1", "c2", "c3"],
        )

        payload = params.to_api_payload(exclude_none=True)

        assert payload["citation_list"] == [
            {"ref": "c1"},
            {"ref": "c2"},
            {"ref": "c3"},
        ]

    def test_citation_list_with_single_handle(self):
        params = EventSaveParams(type="Death", citation_list=["only_handle"])

        payload = params.to_api_payload(exclude_none=True)

        assert payload["citation_list"] == [{"ref": "only_handle"}]


class TestEventSaveParamsNoteListSerialization:
    """``note_list`` is optional and only emitted when provided."""

    def test_optional_note_list_becomes_ref_list(self):
        params = EventSaveParams(
            type="Marriage",
            citation_list=["c1"],
            note_list=["n1", "n2"],
        )

        payload = params.to_api_payload(exclude_none=True)

        assert payload["note_list"] == [{"ref": "n1"}, {"ref": "n2"}]

    def test_none_note_list_is_omitted(self):
        params = EventSaveParams(type="Birth", citation_list=["c1"], note_list=None)

        payload = params.to_api_payload(exclude_none=True)

        assert "note_list" not in payload

    def test_empty_note_list_is_omitted(self):
        """An empty ``note_list`` must not clobber existing notes on PUT."""

        params = EventSaveParams(
            type="Birth", citation_list=["c1"], note_list=[]
        )

        payload = params.to_api_payload(exclude_none=True)

        assert "note_list" not in payload


class TestEventSaveParamsRoundTrip:
    """``model_dump`` keeps the user-friendly ``List[str]`` shape."""

    def test_model_dump_keeps_plain_string_handles(self):
        params = EventSaveParams(
            type="Birth",
            citation_list=["c1", "c2"],
            note_list=["n1"],
        )

        dumped = params.model_dump(exclude_none=True)

        assert dumped["citation_list"] == ["c1", "c2"]
        assert dumped["note_list"] == ["n1"]

    def test_to_api_payload_excludes_unset_optional_fields(self):
        params = EventSaveParams(
            type="Birth",
            citation_list=["c1"],
            description=None,
            date=None,
            place=None,
            note_list=None,
        )

        payload = params.to_api_payload(exclude_none=True)

        assert payload["type"] == "Birth"
        assert payload["citation_list"] == [{"ref": "c1"}]
        assert "description" not in payload
        assert "date" not in payload
        assert "place" not in payload
        assert "note_list" not in payload

    def test_to_api_payload_preserves_complex_date_object(self):
        params = EventSaveParams(
            type="Birth",
            citation_list=["c1"],
            date={
                "dateval": [1, 1, 1900, False],
                "quality": 0,
                "modifier": 0,
            },
        )

        payload = params.to_api_payload(exclude_none=True)

        assert payload["date"] == {
            "dateval": [1, 1, 1900, False],
            "quality": 0,
            "modifier": 0,
        }
        # The two reference list fields still use the ref shape.
        assert payload["citation_list"] == [{"ref": "c1"}]

    def test_to_api_payload_default_exclude_none_matches_previous_filtering(self):
        """``note_list`` is always omitted when ``None`` or empty.

        This is independent of ``exclude_none`` because an empty list (with
        no exclusion option applied) would still be sent as ``note_list: []``
        and silently drop existing notes on the server side. The contract
        matches what the maintainer's ``to_api_payload`` does for
        ``FamilySaveParams.child_handles``.
        """
        params = EventSaveParams(
            type="Birth", citation_list=["c1"], note_list=None
        )

        payload = params.to_api_payload()

        assert "note_list" not in payload
        # citation_list is required, so it's always in the output
        assert payload["citation_list"] == [{"ref": "c1"}]  
