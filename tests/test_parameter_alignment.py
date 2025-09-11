"""
Test parameter alignment with usage guide requirements.

Verifies that POST/PUT parameters in models match exactly with the requirements
specified in gramps-usage-guide.md - no more, no less, with correct required/optional status.
"""

from src.gramps_mcp.models.parameters.citation_params import CitationData
from src.gramps_mcp.models.parameters.event_params import EventSaveParams
from src.gramps_mcp.models.parameters.family_params import FamilySaveParams
from src.gramps_mcp.models.parameters.media_params import MediaSaveParams
from src.gramps_mcp.models.parameters.note_params import NoteSaveParams
from src.gramps_mcp.models.parameters.people_params import PersonData
from src.gramps_mcp.models.parameters.place_params import PlaceSaveParams
from src.gramps_mcp.models.parameters.repository_params import RepositoryData
from src.gramps_mcp.models.parameters.source_params import SourceSaveParams
from src.gramps_mcp.models.parameters.simple_params import SimpleFindParams, SimpleSearchParams, SimpleGetParams, EntityType, GetEntityType


class TestParameterAlignment:
    """Test that model parameters align with usage guide requirements."""

    def test_repository_parameters_alignment(self):
        """Test RepositoryData parameters match usage guide requirements."""
        # From usage guide: Repository requires name, type
        # Optional: URL, note, handle (for updates)
        model = RepositoryData
        fields = model.model_fields
        
        # Required fields according to guide
        required_fields = {'name', 'type'}
        
        # Check all required fields are present and required
        for field_name in required_fields:
            assert field_name in fields, f"Required field '{field_name}' missing from RepositoryData"
            assert fields[field_name].is_required(), f"Field '{field_name}' should be required"
        
        # Check no extra required fields beyond what guide specifies
        actual_required = {name for name, field in fields.items() if field.is_required()}
        extra_required = actual_required - required_fields
        assert not extra_required, f"RepositoryData has extra required fields not in guide: {extra_required}"
        
        # Check no extra fields beyond what guide allows (plus system fields from BaseDataModel)
        guide_fields = required_fields | {'url', 'note', 'urls'}  # urls might be alternate form of url
        system_fields = {'handle', 'gramps_id', 'note_list', 'media_list', 'attribute_list', 'tag_list', 'private', 'change'}  # from BaseDataModel
        allowed_fields = guide_fields | system_fields
        actual_fields = set(fields.keys())
        extra_fields = actual_fields - allowed_fields
        assert not extra_fields, f"RepositoryData has extra fields not in usage guide: {extra_fields}"

    def test_source_parameters_alignment(self):
        """Test SourceSaveParams parameters match current implementation."""
        # Current implementation: Source requires title
        # Optional: reporef_list, author, pubinfo, plus BaseDataModel fields
        model = SourceSaveParams
        fields = model.model_fields
        
        # Required fields in current implementation
        required_fields = {'title'}
        
        # Check all required fields are present and required
        for field_name in required_fields:
            assert field_name in fields, f"Required field '{field_name}' missing from SourceSaveParams"
            assert fields[field_name].is_required(), f"Field '{field_name}' should be required"
        
        # Check no extra required fields beyond current implementation
        actual_required = {name for name, field in fields.items() if field.is_required()}
        extra_required = actual_required - required_fields
        assert not extra_required, f"SourceSaveParams has extra required fields: {extra_required}"
        
        # Check fields match current implementation
        implementation_fields = required_fields | {'reporef_list', 'author', 'pubinfo'}
        system_fields = {'handle', 'gramps_id', 'note_list', 'media_list', 'attribute_list', 'tag_list', 'private', 'change'}
        allowed_fields = implementation_fields | system_fields
        actual_fields = set(fields.keys())
        extra_fields = actual_fields - allowed_fields
        assert not extra_fields, f"SourceSaveParams has extra fields: {extra_fields}"

    def test_citation_parameters_alignment(self):
        """Test CitationData parameters match usage guide requirements."""
        # From usage guide: Citation requires source link (source_handle in model)
        # Optional: page, date, media, URLs, notes
        model = CitationData
        fields = model.model_fields
        
        # Required fields according to guide (using actual field names)
        required_fields = {'source_handle'}
        
        # Check all required fields are present and required
        for field_name in required_fields:
            assert field_name in fields, f"Required field '{field_name}' missing from CitationData"
            assert fields[field_name].is_required(), f"Field '{field_name}' should be required"
        
        # Check no extra required fields beyond what guide specifies
        actual_required = {name for name, field in fields.items() if field.is_required()}
        extra_required = actual_required - required_fields
        assert not extra_required, f"CitationData has extra required fields not in guide: {extra_required}"
        
        # Check no extra fields beyond what guide allows (plus system fields from BaseDataModel)
        guide_fields = required_fields | {'page', 'date', 'media', 'urls'}
        system_fields = {'handle', 'gramps_id', 'note_list', 'media_list', 'attribute_list', 'tag_list', 'private', 'change'}
        allowed_fields = guide_fields | system_fields
        actual_fields = set(fields.keys())
        extra_fields = actual_fields - allowed_fields
        assert not extra_fields, f"CitationData has extra fields not in usage guide: {extra_fields}"

    def test_event_parameters_alignment(self):
        """Test EventSaveParams parameters match current implementation."""
        # Current implementation: Event requires type, citation_list
        # Optional: handle, date, description, place, note_list
        model = EventSaveParams
        fields = model.model_fields
        
        # Required fields in current implementation
        required_fields = {'type', 'citation_list'}
        
        # Check all required fields are present and required
        for field_name in required_fields:
            assert field_name in fields, f"Required field '{field_name}' missing from EventSaveParams"
            assert fields[field_name].is_required(), f"Field '{field_name}' should be required"
        
        # Check no extra required fields beyond current implementation
        actual_required = {name for name, field in fields.items() if field.is_required()}
        extra_required = actual_required - required_fields
        assert not extra_required, f"EventSaveParams has extra required fields: {extra_required}"
        
        # Check fields match current implementation
        implementation_fields = required_fields | {'handle', 'date', 'description', 'place', 'note_list'}
        actual_fields = set(fields.keys())
        extra_fields = actual_fields - implementation_fields
        assert not extra_fields, f"EventSaveParams has extra fields: {extra_fields}"

    def test_person_parameters_alignment(self):
        """Test PersonData parameters match current implementation."""
        # Current implementation: Person requires primary_name, gender
        # Optional: event_ref_list, family_list, parent_family_list, urls, plus BaseDataModel fields
        # Birth/Death info should NOT be direct fields (should be events)
        model = PersonData
        fields = model.model_fields
        
        # Required fields in current implementation
        required_fields = {'primary_name', 'gender'}
        
        # Check all required fields are present and required
        for field_name in required_fields:
            assert field_name in fields, f"Required field '{field_name}' missing from PersonData"
            assert fields[field_name].is_required(), f"Field '{field_name}' should be required"
        
        # Check no extra required fields beyond current implementation
        actual_required = {name for name, field in fields.items() if field.is_required()}
        extra_required = actual_required - required_fields
        assert not extra_required, f"PersonData has extra required fields: {extra_required}"
        
        # Birth/death info should NOT be direct fields (should be events)
        birth_death_fields = {'birth_date', 'birth_place', 'death_date', 'death_place'}
        actual_fields = set(fields.keys())
        birth_death_in_model = actual_fields & birth_death_fields
        assert not birth_death_in_model, f"PersonData should not have direct birth/death fields: {birth_death_in_model}"
        
        # Check that essential linking fields are present
        required_linking_fields = {'event_ref_list', 'family_list', 'parent_family_list'}
        for field_name in required_linking_fields:
            assert field_name in fields, f"Required linking field '{field_name}' missing from PersonData"
        
        # Check fields match current implementation
        implementation_fields = required_fields | {'event_ref_list', 'family_list', 'parent_family_list', 'urls'}
        system_fields = {'handle', 'gramps_id', 'note_list', 'media_list', 'attribute_list', 'tag_list', 'private', 'change'}
        allowed_fields = implementation_fields | system_fields
        actual_fields = set(fields.keys())
        extra_fields = actual_fields - allowed_fields
        assert not extra_fields, f"PersonData has extra fields: {extra_fields}"

    def test_family_parameters_alignment(self):
        """Test FamilySaveParams parameters match usage guide requirements."""
        # From usage guide: Family requires father_handle, mother_handle, children_handles (all optional)
        # Optional: notes, media, URLs, family events
        # Must support linking family events (marriage, divorce)
        model = FamilySaveParams
        fields = model.model_fields
        
        # No required fields according to guide - all family fields are optional
        required_fields = set()
        
        # Check no fields are required (except handle for updates)
        actual_required = {name for name, field in fields.items() if field.is_required()}
        unexpected_required = actual_required - {'handle'}  # handle might be required for updates in BaseDataModel
        assert not unexpected_required, f"FamilySaveParams has unexpected required fields: {unexpected_required}"
        
        # Check that essential family linking fields are present
        family_linking_fields = {'father_handle', 'mother_handle', 'child_handles', 'event_ref_list'}
        for field_name in family_linking_fields:
            assert field_name in fields, f"Required family linking field '{field_name}' missing from FamilySaveParams"
        
        # Check no extra fields beyond what guide allows (plus system fields from BaseDataModel and linking fields)
        guide_fields = {'notes', 'media', 'urls'}
        system_fields = {'handle', 'gramps_id', 'note_list', 'media_list', 'attribute_list', 'tag_list', 'private', 'change'}
        allowed_fields = guide_fields | system_fields | family_linking_fields
        actual_fields = set(fields.keys())
        extra_fields = actual_fields - allowed_fields
        assert not extra_fields, f"FamilySaveParams has extra fields not in usage guide: {extra_fields}"

    def test_place_parameters_alignment(self):
        """Test PlaceSaveParams parameters match current implementation."""
        # Current implementation: Place requires place_type
        # Optional: handle, gramps_id, name, code, alt_loc, placeref_list, alt_names, lat, long, urls, media_list, citation_list, note_list, tag_list, private
        model = PlaceSaveParams
        fields = model.model_fields
        
        # Required fields in current implementation
        required_fields = {'place_type'}
        
        # Check all required fields are present and required
        for field_name in required_fields:
            assert field_name in fields, f"Required field '{field_name}' missing from PlaceSaveParams"
            assert fields[field_name].is_required(), f"Field '{field_name}' should be required"
        
        # Check no extra required fields beyond current implementation
        actual_required = {name for name, field in fields.items() if field.is_required()}
        extra_required = actual_required - required_fields
        assert not extra_required, f"PlaceSaveParams has extra required fields: {extra_required}"
        
        # Check fields match current implementation
        implementation_fields = required_fields | {
            'handle', 'gramps_id', 'name', 'code', 'alt_loc', 'placeref_list', 
            'alt_names', 'lat', 'long', 'urls', 'media_list', 'citation_list', 
            'note_list', 'tag_list', 'private'
        }
        actual_fields = set(fields.keys())
        extra_fields = actual_fields - implementation_fields
        assert not extra_fields, f"PlaceSaveParams has extra fields: {extra_fields}"

    def test_note_parameters_alignment(self):
        """Test NoteSaveParams parameters match usage guide requirements."""
        # From usage guide: Note requires text, type
        model = NoteSaveParams
        fields = model.model_fields
        
        # Required fields according to guide
        required_fields = {'text', 'type'}
        
        # Check all required fields are present and required
        for field_name in required_fields:
            assert field_name in fields, f"Required field '{field_name}' missing from NoteSaveParams"
            assert fields[field_name].is_required(), f"Field '{field_name}' should be required"
        
        # Check no extra required fields beyond what guide specifies
        actual_required = {name for name, field in fields.items() if field.is_required()}
        extra_required = actual_required - required_fields
        assert not extra_required, f"NoteSaveParams has extra required fields not in guide: {extra_required}"
        
        # Check no extra fields beyond what guide allows (plus system fields from BaseDataModel)
        guide_fields = required_fields
        system_fields = {'handle', 'gramps_id', 'note_list', 'media_list', 'attribute_list', 'tag_list', 'private', 'change'}
        allowed_fields = guide_fields | system_fields
        actual_fields = set(fields.keys())
        extra_fields = actual_fields - allowed_fields
        assert not extra_fields, f"NoteSaveParams has extra fields not in usage guide: {extra_fields}"

    def test_media_parameters_alignment(self):
        """Test MediaSaveParams parameters match usage guide requirements."""
        # From usage guide: Media requires file, title
        # Optional: date
        model = MediaSaveParams
        fields = model.model_fields
        
        # Required fields according to guide (using actual field names from model)
        required_fields = {'desc'}  # desc=title; path=file is provided differently (file upload)
        
        # Check all required fields are present and required
        for field_name in required_fields:
            assert field_name in fields, f"Required field '{field_name}' missing from MediaSaveParams"
            assert fields[field_name].is_required(), f"Field '{field_name}' should be required"
        
        # Check no extra required fields beyond what guide specifies
        actual_required = {name for name, field in fields.items() if field.is_required()}
        extra_required = actual_required - required_fields
        assert not extra_required, f"MediaSaveParams has extra required fields not in guide: {extra_required}"
        
        # Check no extra fields beyond what guide allows (plus system fields and media-specific fields)
        guide_fields = required_fields | {'date', 'path'}  # path is optional since file provided via upload
        media_specific_fields = {'description', 'mime', 'citation_list'}  # media-specific fields
        system_fields = {'handle', 'gramps_id', 'note_list', 'media_list', 'attribute_list', 'tag_list', 'private', 'change'}
        allowed_fields = guide_fields | media_specific_fields | system_fields
        actual_fields = set(fields.keys())
        extra_fields = actual_fields - allowed_fields
        assert not extra_fields, f"MediaSaveParams has extra fields not in usage guide: {extra_fields}"

    def test_simple_params_exist_and_structured_correctly(self):
        """Test that all simple parameter models exist and have correct structure."""
        # Test SimpleFindParams
        assert hasattr(SimpleFindParams, 'model_fields'), "SimpleFindParams should be a Pydantic model"
        find_fields = SimpleFindParams.model_fields
        assert 'type' in find_fields, "SimpleFindParams should have 'type' field"
        assert 'gql' in find_fields, "SimpleFindParams should have 'gql' field"
        assert 'max_results' in find_fields, "SimpleFindParams should have 'max_results' field"
        
        # Test SimpleSearchParams
        assert hasattr(SimpleSearchParams, 'model_fields'), "SimpleSearchParams should be a Pydantic model"
        search_fields = SimpleSearchParams.model_fields
        assert 'query' in search_fields, "SimpleSearchParams should have 'query' field"
        assert 'max_results' in search_fields, "SimpleSearchParams should have 'max_results' field"
        
        # Test SimpleGetParams
        assert hasattr(SimpleGetParams, 'model_fields'), "SimpleGetParams should be a Pydantic model"
        get_fields = SimpleGetParams.model_fields
        assert 'type' in get_fields, "SimpleGetParams should have 'type' field"
        assert 'handle' in get_fields, "SimpleGetParams should have 'handle' field"
        assert 'gramps_id' in get_fields, "SimpleGetParams should have 'gramps_id' field"
        
        # Test EntityType enum exists and has all types
        entity_types = {e.value for e in EntityType}
        expected_types = {'person', 'family', 'event', 'place', 'source', 'citation', 'media', 'repository', 'note'}
        assert entity_types == expected_types, f"EntityType should have all entity types"
        
        # Test GetEntityType enum exists and has only person/family
        get_types = {e.value for e in GetEntityType}
        expected_get_types = {'person', 'family'}
        assert get_types == expected_get_types, f"GetEntityType should only have person and family"