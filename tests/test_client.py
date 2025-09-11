"""
Integration tests for Gramps Web API client using real API.

Tests client methods that are used across multiple tools.
These tests require a working Gramps Web API instance with valid credentials.
"""


import pytest
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from src.gramps_mcp.client import GrampsWebAPIClient
from src.gramps_mcp.config import get_settings
from src.gramps_mcp.models.api_calls import ApiCalls
from src.gramps_mcp.models.parameters.base_params import BaseGetMultipleParams


class TestGetPersonCall:
    """Test GET_PERSON API call directly."""
    
    @pytest.mark.asyncio
    async def test_get_person_by_handle(self):
        """Test getting a person by handle using make_api_call."""
        settings = get_settings()
        client = GrampsWebAPIClient()
        
        try:
            # Try different approaches to get full handles
            print(f"Tree ID: {settings.gramps_tree_id}")
            
            # Try 1: Current approach (tree_id in auth only)
            url1 = client._build_url(settings.gramps_tree_id, "people/")
            print(f"URL1 (current): {url1}")
            
            # Try 2: With extend parameter to get more data
            url2 = client._build_url(settings.gramps_tree_id, "people/")
            raw_result2 = await client._make_request("GET", url2, params={"pagesize": 1, "extend": "all"})
            
            if raw_result2 and len(raw_result2) > 0:
                handle = raw_result2[0].get("handle")
                print(f"Handle with extend=all: '{handle}' (length: {len(handle)})")
            
            # Try 3: Test if a known good handle works
            test_handle = "e9bdc3c7e0339256f218fb3450b"
            print(f"Testing known handle: {test_handle}")
            person_url = client._build_url(settings.gramps_tree_id, f"people/{test_handle}/")
            print(f"Person URL: {person_url}")
            
            try:
                person_direct = await client._make_request("GET", person_url)
                print("SUCCESS: Direct person fetch worked!")
            except Exception as e:
                print(f"FAILED: Direct person fetch: {e}")
            
            # Also try via make_api_call
            params = BaseGetMultipleParams(pagesize=1)
            people_result = await client.make_api_call(ApiCalls.GET_PEOPLE, params=params)
            
            if not people_result or len(people_result) == 0:
                pytest.fail("No people found in database for testing")
            
            # Get the first person's handle
            first_person = people_result[0]
            handle = first_person.get("handle")
            expected_gramps_id = first_person.get("gramps_id")
            
            print(f"\nFull person data: {first_person}")
            print(f"Handle length: {len(handle) if handle else 'None'}")
            print(f"Handle: '{handle}'")
            print(f"Expected gramps_id: {expected_gramps_id}")
            
            # Test GET_PERSON call
            person_result = await client.make_api_call(
                ApiCalls.GET_PERSON,
                handle=handle
            )
            
            print(f"GET_PERSON result gramps_id: {person_result.get('gramps_id')}")
            
            assert person_result is not None
            assert person_result.get("gramps_id") == expected_gramps_id
            assert person_result.get("handle") == handle
            
        finally:
            await client.close()


class TestGetObjectGrampsId:
    """Test get_object functionality."""
    
    @pytest.mark.asyncio
    async def test_get_person_by_handle_via_api_call(self):
        """Test getting a person by handle using make_api_call."""
        client = GrampsWebAPIClient()
        
        try:
            # First get a list of people to find one with both handle and gramps_id
            params = BaseGetMultipleParams(pagesize=10)
            people_result = await client.make_api_call(ApiCalls.GET_PEOPLE, params=params)
            
            if not people_result or len(people_result) == 0:
                pytest.fail("No people found in database for testing")
            
            # Find a person with both handle and gramps_id
            test_person = None
            for person in people_result:
                if person.get("handle") and person.get("gramps_id"):
                    test_person = person
                    break
            
            if not test_person:
                pytest.fail("No person with both handle and gramps_id found")
            
            handle = test_person["handle"]
            expected_id = test_person["gramps_id"]
            
            # Test GET_PERSON API call
            person_result = await client.make_api_call(
                ApiCalls.GET_PERSON,
                handle=handle
            )
            
            assert person_result is not None
            assert person_result["gramps_id"] == expected_id
            assert person_result["handle"] == handle
                    
        finally:
            await client.close()


class TestMediaFileUpload:
    """Test media file upload functionality."""
    
    @pytest.mark.asyncio
    async def test_upload_media_file(self):
        """Test uploading a media file to Gramps."""
        client = GrampsWebAPIClient()
        settings = get_settings()
        
        try:
            # Create test file content
            file_content = b"fake image data for testing"
            mime_type = "image/jpeg"
            
            # Upload the file
            result = await client.upload_media_file(
                file_content=file_content,
                mime_type=mime_type,
                tree_id=settings.gramps_tree_id
            )
            
            # The API should return a transaction with the new media object
            assert result is not None
            assert isinstance(result, list)
            assert len(result) > 0
            
            # Check the transaction structure
            transaction = result[0]
            assert "new" in transaction
            
            # Check the media object
            media = transaction["new"]
            assert "handle" in media
            assert "path" in media
            assert "mime" in media
            assert media["mime"] == mime_type
            
            # The path should be set based on checksum
            assert "checksum" in media
            assert media["checksum"] != ""
        finally:
            await client.close()


class TestPutMergeRequirement:
    """Test that PUT operations need to merge with existing data to prevent field loss."""
    
    @pytest.mark.asyncio
    async def test_media_put_should_preserve_existing_file_data(self):
        """Test that PUT operations should preserve existing file data when updating metadata."""
        client = GrampsWebAPIClient()
        settings = get_settings()
        
        try:
            # 1. Upload a media file to create base object with file data
            with open('tests/sample/33SQ-GP8N-NLK.jpg', 'rb') as f:
                file_content = f.read()
            
            upload_result = await client.upload_media_file(
                file_content=file_content,
                mime_type='image/jpeg',
                tree_id=settings.gramps_tree_id
            )
            
            # Extract handle and verify file data exists
            handle = upload_result[0]["new"]["handle"]
            original_mime = upload_result[0]["new"]["mime"]
            original_path = upload_result[0]["new"]["path"]
            
            assert original_mime == "image/jpeg"
            assert original_path != ""
            
            # 2. Do a PUT with only desc field - this should preserve existing file data
            put_result = await client.make_api_call(
                api_call=ApiCalls.PUT_MEDIA_ITEM,
                params={'handle': handle, 'desc': 'Test description'},
                tree_id=settings.gramps_tree_id,
                handle=handle
            )
            
            # 3. Verify that file data was preserved (this will FAIL without merge logic)
            updated_data = put_result[0]["new"]
            assert updated_data["desc"] == "Test description"
            
            # These assertions will FAIL without PUT merge logic
            assert updated_data["mime"] == original_mime, f"Expected mime {original_mime} to be preserved, but got: {updated_data['mime']}"
            assert updated_data["path"] == original_path, f"Expected path {original_path} to be preserved, but got: {updated_data['path']}"
            
        finally:
            await client.close()

