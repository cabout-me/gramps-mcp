"""Round-trip tests for NoteSaveParams and FamilySaveParams.

These models transform user-facing fields into the shapes the Gramps Web API
expects (StyledText for note text, ChildRef objects for family children) inside
model_dump(). The FastMCP dispatch layer validates tool arguments into the
model, calls model_dump(), and the handler then re-validates the resulting
dict against the same model. That validate -> model_dump -> re-validate cycle
must be lossless and idempotent, otherwise notes fail to save and family
children silently disappear. These tests lock that behaviour in.
"""

from src.gramps_mcp.models.parameters.family_params import FamilySaveParams
from src.gramps_mcp.models.parameters.note_params import NoteSaveParams


class TestNoteSaveParamsRoundTrip:
    def test_text_dumps_to_styledtext(self):
        dumped = NoteSaveParams(text="hello", type="Research").model_dump(
            exclude_none=True
        )
        assert dumped["text"] == {"_class": "StyledText", "string": "hello"}

    def test_styledtext_dict_revalidates(self):
        """Re-validating a dumped model must not raise (the create_note bug)."""
        first = NoteSaveParams(text="hello", type="Research").model_dump(
            exclude_none=True
        )
        second = NoteSaveParams(**first).model_dump(exclude_none=True)
        # idempotent: text is still a single-wrapped StyledText, string intact
        assert second["text"] == {"_class": "StyledText", "string": "hello"}

    def test_field_validator_extracts_string(self):
        model = NoteSaveParams(
            text={"_class": "StyledText", "string": "hi"}, type="Research"
        )
        assert model.text == "hi"


class TestFamilySaveParamsRoundTrip:
    def test_child_handles_become_child_ref_list(self):
        dumped = FamilySaveParams(child_handles=["H1", "H2"]).model_dump(
            exclude_none=True
        )
        assert "child_handles" not in dumped
        assert [c["ref"] for c in dumped["child_ref_list"]] == ["H1", "H2"]
        assert all(
            c["_class"] == "ChildRef" and c["frel"] == "Birth" and c["mrel"] == "Birth"
            for c in dumped["child_ref_list"]
        )

    def test_children_survive_revalidation(self):
        """The create_family bug: children dropped on re-validation."""
        first = FamilySaveParams(
            father_handle="F", child_handles=["H1", "H2"]
        ).model_dump(exclude_none=True)
        second = FamilySaveParams(**first).model_dump(exclude_none=True)
        assert second["father_handle"] == "F"
        assert [c["ref"] for c in second["child_ref_list"]] == ["H1", "H2"]

    def test_child_handles_dedupe_against_explicit_refs(self):
        dumped = FamilySaveParams(
            child_handles=["H1", "H3"],
            child_ref_list=[
                {"_class": "ChildRef", "ref": "H1", "frel": "Birth", "mrel": "Birth"}
            ],
        ).model_dump(exclude_none=True)
        assert [c["ref"] for c in dumped["child_ref_list"]] == ["H1", "H3"]

    def test_no_children_adds_nothing(self):
        dumped = FamilySaveParams(father_handle="F").model_dump(exclude_none=True)
        assert "child_ref_list" not in dumped
        assert "child_handles" not in dumped
