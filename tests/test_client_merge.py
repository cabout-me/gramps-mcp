"""
Unit tests for the client.py merge logic in PUT operations.

This test demonstrates the DESIRED behavior for Issue #9 - when updating a person 
with new event references, the existing event_ref_list should be merged with the 
new events, not replaced.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.gramps_mcp.client import GrampsWebAPIClient
from src.gramps_mcp.models.api_calls import ApiCalls


class TestClientMergeLogic:
    """Test the merge logic for PUT operations in the client."""

    @pytest.mark.asyncio
    async def test_put_operation_should_preserve_existing_events_when_adding_new(self):
        """Test that PUT operations should preserve existing events when adding new ones.
        
        This is the actual Issue #9 scenario: user has a person with existing events,
        and wants to add a new event. They provide only the new event in event_ref_list,
        expecting the existing events to be preserved.
        """
        
        # Create a client instance
        client = GrampsWebAPIClient()
        
        # Mock the auth manager to avoid actual authentication
        client.auth_manager = MagicMock()
        client.auth_manager.get_token = AsyncMock()
        client.auth_manager.get_headers = MagicMock(return_value={"Authorization": "Bearer test"})
        client.auth_manager.client = MagicMock()
        client.auth_manager.close = AsyncMock()
        
        # Existing person data with one event (Birth) and other fields
        existing_person_data = {
            "handle": "test_person_handle",
            "gramps_id": "I0001",
            "primary_name": {
                "first_name": "John",
                "surname_list": [{"surname": "Smith"}]
            },
            "gender": 1,
            "change": 1234567890,
            "private": False,
            "event_ref_list": [
                {
                    "ref": "birth_event_handle",
                    "role": "Primary"
                }
            ],
            "note_list": ["existing_note_handle"],
            "media_list": [{"ref": "existing_media_handle"}]
        }
        
        # User provides NEW event plus updates to other fields
        # This tests both list merging AND regular field updates
        update_data = {
            "handle": "test_person_handle",
            "primary_name": {
                "first_name": "Jonathan",  # Changed from "John"
                "surname_list": [{"surname": "Smith-Jones"}]  # Changed surname
            },
            "gender": 1,
            "private": True,  # Changed from False
            "event_ref_list": [
                {
                    "ref": "death_event_handle",
                    "role": "Primary"
                }
            ],
            "note_list": ["new_note_handle"]  # New note, should merge with existing
        }
        
        # Mock the _make_request method to capture what's being sent
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            # First call returns existing data (GET)
            # Second call is the PUT with merged data
            mock_request.side_effect = [
                existing_person_data,  # GET response
                {"success": True}       # PUT response
            ]
            
            # Make the API call
            result = await client.make_api_call(
                api_call=ApiCalls.PUT_PERSON,
                params=update_data,
                tree_id="test_tree",
                handle="test_person_handle"
            )
            
            # Verify the GET request was made
            assert mock_request.call_count == 2
            
            # Get the PUT request call (second call)
            put_call = mock_request.call_args_list[1]
            
            # Extract the json_data argument from the PUT request
            put_json_data = put_call.kwargs.get('json_data') or put_call[1].get('json_data')
            
            # DESIRED BEHAVIOR: The existing event should be preserved
            assert put_json_data is not None, "PUT request should have json_data"
            assert "event_ref_list" in put_json_data, "PUT data should have event_ref_list"
            
            # Test 1: List fields should be MERGED (existing + new)
            event_refs = put_json_data["event_ref_list"]
            assert len(event_refs) == 2, f"Should have 2 events (existing + new), got {len(event_refs)}: {event_refs}"
            event_handles = {e["ref"] for e in event_refs}
            assert "birth_event_handle" in event_handles, "Should preserve existing birth event"
            assert "death_event_handle" in event_handles, "Should add new death event"
            
            note_refs = put_json_data["note_list"]
            assert len(note_refs) == 2, f"Should have 2 notes (existing + new), got {len(note_refs)}: {note_refs}"
            assert "existing_note_handle" in note_refs, "Should preserve existing note"
            assert "new_note_handle" in note_refs, "Should add new note"
            
            media_refs = put_json_data["media_list"]
            assert len(media_refs) == 1, f"Should preserve existing media, got {len(media_refs)}: {media_refs}"
            assert media_refs[0]["ref"] == "existing_media_handle", "Should preserve existing media"
            
            # Test 2: Non-list fields should be UPDATED (new values replace old)
            assert put_json_data.get("primary_name")["first_name"] == "Jonathan", "Should update first_name"
            assert put_json_data.get("primary_name")["surname_list"][0]["surname"] == "Smith-Jones", "Should update surname"
            assert put_json_data.get("private") == True, "Should update private field"
            
            # Test 3: Fields not in update should be PRESERVED
            assert put_json_data.get("gramps_id") == "I0001", "Should preserve gramps_id from existing data"
            assert put_json_data.get("change") == 1234567890, "Should preserve change field"
            assert put_json_data.get("gender") == 1, "Should preserve gender"
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_event_ref_list_deduplication(self):
        """Test that duplicate event references are not added during merge."""
        # Setup mock API client
        client = GrampsWebAPIClient()
        client.auth_manager.close = AsyncMock()
        
        # Mock existing person with one event
        existing_person = {
            "handle": "person123",
            "primary_name": {"first_name": "John", "surname_list": [{"surname": "Smith"}]},
            "gender": 1,
            "gramps_id": "I001",
            "change": 1234567890,
            "event_ref_list": [
                {"ref": "event_birth", "role": "Primary"}
            ]
        }
        
        # Mock update data that includes the same event plus a new one
        update_data = {
            "handle": "person123",
            "primary_name": {"first_name": "John", "surname_list": [{"surname": "Smith"}]},
            "gender": 1,
            "event_ref_list": [
                {"ref": "event_birth", "role": "Primary"},  # Duplicate
                {"ref": "event_death", "role": "Primary"}   # New
            ]
        }
        
        with patch.object(client, '_make_request') as mock_request:
            # First call (GET) returns existing person
            # Second call (PUT) will receive the merged data
            mock_request.side_effect = [existing_person, {"success": True}]
            
            # Make the API call
            result = await client.make_api_call(
                api_call=ApiCalls.PUT_PERSON,
                params=update_data,
                tree_id="test_tree",
                handle="person123"
            )
            
            # Verify the PUT request was made with deduplicated event_ref_list
            assert len(mock_request.call_args_list) == 2
            put_call = mock_request.call_args_list[1]
            put_data = put_call.kwargs.get('json_data') or put_call[1].get('json_data')
            
            # Should only have 2 events (birth once, death once), not 3
            assert len(put_data["event_ref_list"]) == 2
            event_refs = {event["ref"] for event in put_data["event_ref_list"]}
            assert event_refs == {"event_birth", "event_death"}
            
            print(f"DEBUG: Final event_ref_list has {len(put_data['event_ref_list'])} events")
            for event in put_data["event_ref_list"]:
                print(f"  - {event['ref']}: {event['role']}")
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_generic_list_deduplication(self):
        """Test that deduplication works for all types of reference lists."""
        # Setup mock API client
        client = GrampsWebAPIClient()
        client.auth_manager.close = AsyncMock()
        
        # Mock existing person with various reference types
        existing_person = {
            "handle": "person123",
            "primary_name": {"first_name": "John", "surname_list": [{"surname": "Smith"}]},
            "gender": 1,
            "event_ref_list": [{"ref": "event1", "role": "Primary"}],
            "media_list": [{"ref": "media1"}],
            "note_list": ["note1"],  # Simple string handles
            "change": 1234567890,
            "gramps_id": "I001"
        }
        
        # Mock update data with duplicates and new items
        update_data = {
            "handle": "person123", 
            "primary_name": {"first_name": "John", "surname_list": [{"surname": "Smith"}]},
            "gender": 1,
            "event_ref_list": [
                {"ref": "event1", "role": "Primary"},  # Duplicate
                {"ref": "event2", "role": "Primary"}   # New
            ],
            "media_list": [
                {"ref": "media1"},  # Duplicate
                {"ref": "media2"}   # New
            ],
            "note_list": ["note1", "note2"]      # Duplicate + new
        }
        
        with patch.object(client, '_make_request') as mock_request:
            mock_request.side_effect = [existing_person, {"success": True}]
            
            result = await client.make_api_call(
                api_call=ApiCalls.PUT_PERSON,
                params=update_data,
                tree_id="test_tree",
                handle="person123"
            )
            
            # Verify deduplication for all list types
            put_call = mock_request.call_args_list[1]
            put_data = put_call.kwargs.get('json_data') or put_call[1].get('json_data')
            
            # Event references (objects with ref field)
            assert len(put_data["event_ref_list"]) == 2
            event_refs = {e["ref"] for e in put_data["event_ref_list"]}
            assert event_refs == {"event1", "event2"}
            
            # Media references (objects with ref field) 
            assert len(put_data["media_list"]) == 2
            media_refs = {m["ref"] for m in put_data["media_list"]}
            assert media_refs == {"media1", "media2"}
            
            # Note handles (simple strings) - deduplication test
            assert len(put_data["note_list"]) == 2
            assert set(put_data["note_list"]) == {"note1", "note2"}
        
        await client.close()