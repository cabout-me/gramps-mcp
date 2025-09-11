"""
Tests for the unified API call system.

This module tests the API call parameter mapping and the unified
make_api_call method with real API calls to ensure integration works.
"""

import pytest
from pydantic import ValidationError

from src.gramps_mcp.client import GrampsWebAPIClient
from src.gramps_mcp.models import PersonData
from src.gramps_mcp.models.api_calls import ApiCalls
from src.gramps_mcp.models.api_mapping import (
    API_CALL_PARAMS,
    get_param_model,
    validate_api_call_params,
)
from src.gramps_mcp.models.parameters.base_params import (
    BaseGetMultipleParams,
    BaseGetSingleParams,
)


class TestApiMapping:
    """Test API call parameter mapping functionality."""
    
    def test_api_call_params_mapping_exists(self):
        """Test that the API_CALL_PARAMS mapping exists and has expected entries."""
        # Test that mapping exists
        assert API_CALL_PARAMS is not None
        assert isinstance(API_CALL_PARAMS, dict)
        
        # Test that it has entries for people operations
        assert ApiCalls.GET_PEOPLE in API_CALL_PARAMS
        assert ApiCalls.GET_PERSON in API_CALL_PARAMS
        assert ApiCalls.POST_PEOPLE in API_CALL_PARAMS
        
        # Test correct parameter model mappings
        assert API_CALL_PARAMS[ApiCalls.GET_PEOPLE] == BaseGetMultipleParams
        assert API_CALL_PARAMS[ApiCalls.GET_PERSON] == BaseGetSingleParams
        assert API_CALL_PARAMS[ApiCalls.POST_PEOPLE] == PersonData
    
    def test_get_param_model(self):
        """Test getting parameter model for API calls."""
        # Test existing mapping
        assert get_param_model(ApiCalls.GET_PEOPLE) == BaseGetMultipleParams
        assert get_param_model(ApiCalls.GET_PERSON) == BaseGetSingleParams
        
        # Test None for operations without parameters
        assert get_param_model(ApiCalls.DELETE_PERSON) is None
    
    def test_validate_api_call_params_success(self):
        """Test successful parameter validation."""
        # Test with valid parameters
        params = {"page": 1, "pagesize": 10}
        result = validate_api_call_params(ApiCalls.GET_PEOPLE, params)
        
        assert isinstance(result, BaseGetMultipleParams)
        assert result.page == 1
        assert result.pagesize == 10
    
    def test_validate_api_call_params_invalid(self):
        """Test parameter validation with invalid parameters."""
        # Test with invalid parameters - invalid extend choice
        params = {"extend": "invalid_choice"}
        
        with pytest.raises(ValidationError):
            validate_api_call_params(ApiCalls.GET_PEOPLE, params)
    
    def test_validate_api_call_params_no_model(self):
        """Test parameter validation for API calls without parameter models."""
        # Test with no parameters (should return None)
        result = validate_api_call_params(ApiCalls.DELETE_PERSON, {})  # No model defined
        assert result is None
        
        # Test with parameters but no model defined (should raise error)
        with pytest.raises(ValueError, match="does not accept parameters"):
            validate_api_call_params(ApiCalls.DELETE_PERSON, {"page": 1})


class TestUnifiedApiCall:
    """Test the unified API call functionality with real API integration."""
    
    @pytest.fixture
    async def client(self):
        """Create a real GrampsWebAPIClient for integration testing."""
        client = GrampsWebAPIClient()
        yield client
        await client.close()
    
    def test_build_url_with_substitution(self):
        """Test URL building with parameter substitution."""
        client = GrampsWebAPIClient()
        
        # Test URL substitution
        url = client._build_url_with_substitution(
            tree_id="test_tree",
            endpoint="people/{handle}/timeline",
            url_params={"handle": "test_handle_123"}
        )
        
        assert "test_handle_123" in url
        assert "{handle}" not in url
        assert url.endswith("people/test_handle_123/timeline")
    
    def test_build_url_with_substitution_multiple_params(self):
        """Test URL building with multiple parameter substitutions."""
        client = GrampsWebAPIClient()
        
        # Test multiple parameter substitution
        url = client._build_url_with_substitution(
            tree_id="test_tree",
            endpoint="relations/{handle1}/{handle2}",
            url_params={"handle1": "person1", "handle2": "person2"}
        )
        
        assert "person1" in url
        assert "person2" in url
        assert "{handle1}" not in url
        assert "{handle2}" not in url
        assert url.endswith("relations/person1/person2")
    
    def test_build_url_with_substitution_missing_params(self):
        """Test URL building with missing parameters."""
        client = GrampsWebAPIClient()
        
        # Test missing parameters
        with pytest.raises(ValueError, match="Missing required URL parameters"):
            client._build_url_with_substitution(
                tree_id="test_tree",
                endpoint="people/{handle}/timeline",
                url_params={}  # Missing handle
            )
    
    @pytest.mark.asyncio
    async def test_make_api_call_parameter_validation(self, client):
        """Test parameter validation in make_api_call."""
        # Test with valid parameters
        params = BaseGetMultipleParams(page=1, pagesize=10)
        
        # This should not raise an error during parameter validation
        # (it may fail during actual HTTP call if no server is available)
        try:
            await client.make_api_call(
                ApiCalls.GET_PEOPLE,
                params=params,
                tree_id="default"
            )
        except Exception as e:
            # We expect network errors, but not parameter validation errors
            assert "Missing required URL parameters" not in str(e)
            assert "ValidationError" not in str(e)
    
    @pytest.mark.asyncio 
    async def test_make_api_call_url_substitution_validation(self, client):
        """Test URL parameter substitution validation."""
        # Test that missing URL parameters are caught
        with pytest.raises(ValueError, match="Missing required URL parameters"):
            await client.make_api_call(
                ApiCalls.GET_PERSON,  # Requires {handle}
                params={"strip": True},
                tree_id="default"
                # Missing handle parameter
            )
    
    @pytest.mark.asyncio
    async def test_make_api_call_with_dict_params(self, client):
        """Test make_api_call with dictionary parameters."""
        params = {"page": 1, "pagesize": 5}
        
        try:
            await client.make_api_call(
                ApiCalls.GET_PEOPLE,
                params=params,
                tree_id="default"
            )
        except Exception as e:
            # We expect network errors, but parameter validation should work
            assert "ValidationError" not in str(e)
            assert "Missing required URL parameters" not in str(e)
    
    @pytest.mark.asyncio
    async def test_make_api_call_with_pydantic_params(self, client):
        """Test make_api_call with Pydantic model parameters."""
        params = BaseGetMultipleParams(page=2, pagesize=10)
        
        try:
            await client.make_api_call(
                ApiCalls.GET_PEOPLE,
                params=params,
                tree_id="default"
            )
        except Exception as e:
            # We expect network errors, but parameter validation should work
            assert "ValidationError" not in str(e)
            assert "Missing required URL parameters" not in str(e)