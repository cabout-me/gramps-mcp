"""
Integration tests for MCP server using proper MCP client library.

These tests verify that the MCP server correctly implements the protocol
and can handle real API calls to Gramps Web API endpoints.
"""

import subprocess
import sys

import httpx
import pytest
from dotenv import load_dotenv
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import InitializeResult, TextContent

# Load environment variables
load_dotenv()

# Set timeout for all async operations
TIMEOUT = 5.0

# Base URL for the live server
BASE_URL = "http://localhost:8000"

# Pytest timeout configuration
pytestmark = pytest.mark.timeout(TIMEOUT)


class TestServerBuild:
    """Test that the server builds and imports correctly."""
    
    @pytest.mark.asyncio
    async def test_server_starts_without_error(self):
        """Test that the server can start without import errors."""
        # Run the server module to check for import errors
        result = subprocess.run(
            [sys.executable, "-c", "from src.gramps_mcp.server import app; print('Server imports OK')"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            pytest.fail(f"Server failed to start: {result.stderr}")
        
        assert "Server imports OK" in result.stdout


class TestMCPServerSetup:
    """Test MCP server initialization and setup."""
    
    @pytest.mark.asyncio
    async def test_server_is_running(self):
        """Test that the MCP server is running and accessible."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "Gramps MCP Server"
    
    @pytest.mark.asyncio
    async def test_tool_registration(self):
        """Test that only 3 simplified tools plus create/analysis tools are registered."""
        endpoint = f"{BASE_URL}/mcp"
        
        async with streamablehttp_client(endpoint) as client_streams:
            read_stream, write_stream, _ = client_streams  # Unpack 3 elements
            async with ClientSession(read_stream, write_stream) as session:
                # Initialize session
                result = await session.initialize()
                assert isinstance(result, InitializeResult)
                assert result.serverInfo.name == "gramps"
                
                # List tools
                tools_result = await session.list_tools()
                tools = tools_result.tools
                assert len(tools) == 16  # 3 simplified + 9 create + 4 analysis tools
                
                # Verify all expected tools are registered
                expected_tools = {
                    # Simplified Search & Retrieval Tools (3)
                    "find_type", "find_anything", "get_type",
                    
                    # Data Creation & Management Tools (9) - keep unchanged
                    "create_person", "create_family", "create_event", "create_place",
                    "create_source", "create_citation", "create_note", "create_media",
                    "create_repository",
                    
                    # Tree Management Tools (1)
                    "tree_stats",
                    
                    # Analysis Tools (3)
                    "get_descendants", "get_ancestors", "recent_changes"
                }
                
                registered_tool_names = {tool.name for tool in tools}
                assert registered_tool_names == expected_tools
    
    @pytest.mark.asyncio
    async def test_tool_descriptions(self):
        """Test that all tools have proper descriptions."""
        endpoint = f"{BASE_URL}/mcp"
        
        async with streamablehttp_client(endpoint) as client_streams:
            read_stream, write_stream, _ = client_streams
            async with ClientSession(read_stream, write_stream) as session:
                # Initialize session
                await session.initialize()
                
                # List tools and check descriptions
                tools_result = await session.list_tools()
                tools = tools_result.tools
                
                for tool in tools:
                    assert tool.description is not None
                    assert len(tool.description.strip()) > 0
                    assert tool.name is not None


class TestHTTPRoutes:
    """Test standard HTTP routes."""
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self):
        """Test root endpoint returns server information."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/")
            assert response.status_code == 200
            data = response.json()
            assert data["service"] == "Gramps MCP Server"
            assert data["tools_count"] == 16  # 3 simplified + 9 create + 4 analysis

    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Test health check endpoint."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "Gramps MCP Server"


class TestMCPProtocolCompliance:
    """Test MCP protocol compliance and communication."""
    
    @pytest.mark.asyncio
    async def test_mcp_tools_list_request(self):
        """Test MCP tools/list request."""
        endpoint = f"{BASE_URL}/mcp"
        
        async with streamablehttp_client(endpoint) as client_streams:
            read_stream, write_stream, _ = client_streams
            async with ClientSession(read_stream, write_stream) as session:
                # Initialize session
                result = await session.initialize()
                assert isinstance(result, InitializeResult)
                
                # List tools
                tools_result = await session.list_tools()
                assert len(tools_result.tools) == 16  # 3 simplified + 9 create + 4 analysis
    
    @pytest.mark.asyncio
    async def test_mcp_tool_call_find_type_real_api(self):
        """Test find_type tool call with real API integration."""
        endpoint = f"{BASE_URL}/mcp"
        
        async with streamablehttp_client(endpoint) as client_streams:
            read_stream, write_stream, _ = client_streams
            async with ClientSession(read_stream, write_stream) as session:
                # Initialize session
                await session.initialize()
                
                # Call find_type tool for person search
                result = await session.call_tool("find_type", {
                    "arguments": {
                        "type": "person",
                        "gql": "primary_name.first_name ~ \"John\"",
                        "max_results": 20
                    }
                })
                
                # Verify response structure
                assert len(result.content) >= 1
                assert isinstance(result.content[0], TextContent)
                
                response_text = result.content[0].text
                print(f"MCP find_type response: {response_text}")
                
                # Check if the search found results or indicates no matches found
                assert "Found" in response_text or "no people found" in response_text.lower() or "not found" in response_text.lower()
    
    
    @pytest.mark.asyncio
    async def test_mcp_invalid_tool_call(self):
        """Test MCP server handles invalid tool calls properly."""
        endpoint = f"{BASE_URL}/mcp"
        
        async with streamablehttp_client(endpoint) as client_streams:
            read_stream, write_stream, _ = client_streams
            async with ClientSession(read_stream, write_stream) as session:
                # Initialize session
                await session.initialize()
                
                # Try to call a non-existent tool - FastMCP might handle this gracefully
                try:
                    result = await session.call_tool("non_existent_tool", {})
                    # If no exception is raised, check that response indicates error
                    assert len(result.content) >= 1
                    assert isinstance(result.content[0], TextContent)
                    response_text = result.content[0].text.lower()
                    assert "error" in response_text or "not found" in response_text
                except Exception as e:
                    # If an exception is raised, that's also acceptable
                    error_str = str(e).lower()
                    assert "non_existent_tool" in error_str or "not found" in error_str


class TestToolIntegrationRealAPI:
    """Test tool integration with real Gramps Web API."""
    
    @pytest.mark.asyncio
    async def test_find_type_with_specific_query(self):
        """Test find_type tool with specific query."""
        endpoint = f"{BASE_URL}/mcp"
        
        async with streamablehttp_client(endpoint) as client_streams:
            read_stream, write_stream, _ = client_streams
            async with ClientSession(read_stream, write_stream) as session:
                # Initialize session
                await session.initialize()
                
                # Call find_type with specific query
                result = await session.call_tool("find_type", {
                    "arguments": {
                        "type": "person",
                        "gql": "primary_name.surname_list.any.surname ~ \"Smith\"",
                        "max_results": 20
                    }
                })
                
                # Verify response format
                assert len(result.content) >= 1
                assert isinstance(result.content[0], TextContent)
                response_text = result.content[0].text
                
                # Should be valid JSON or formatted text
                assert len(response_text.strip()) > 0
    
    @pytest.mark.asyncio
    async def test_search_all_objects(self):
        """Test search_all tool for comprehensive search."""
        endpoint = f"{BASE_URL}/mcp"
        
        async with streamablehttp_client(endpoint) as client_streams:
            read_stream, write_stream, _ = client_streams
            async with ClientSession(read_stream, write_stream) as session:
                # Initialize session
                await session.initialize()
                
                # Call find_anything tool
                result = await session.call_tool("find_anything", {
                    "arguments": {
                        "query": "test",
                        "pagesize": 3
                    }
                })
                
                # Verify response format
                assert len(result.content) >= 1
                assert isinstance(result.content[0], TextContent)


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.mark.asyncio
    async def test_invalid_tree_id(self):
        """Test handling of invalid tree ID."""
        endpoint = f"{BASE_URL}/mcp"
        
        async with streamablehttp_client(endpoint) as client_streams:
            read_stream, write_stream, _ = client_streams
            async with ClientSession(read_stream, write_stream) as session:
                # Initialize session
                await session.initialize()
                
                # Call find_person which now uses configured tree
                result = await session.call_tool("find_person", {
                    "arguments": {
                        "gql": "primary_name.first_name ~ \"test\"",
                        "pagesize": 1
                    }
                })
                
                # Should handle gracefully without crashing
                assert len(result.content) >= 1
                assert isinstance(result.content[0], TextContent)
    
    @pytest.mark.asyncio
    async def test_get_type_details_invalid_handle(self):
        """Test get_type with invalid handle."""
        endpoint = f"{BASE_URL}/mcp"
        
        async with streamablehttp_client(endpoint) as client_streams:
            read_stream, write_stream, _ = client_streams
            async with ClientSession(read_stream, write_stream) as session:
                # Initialize session
                await session.initialize()
                
                # Call with invalid person handle
                result = await session.call_tool("get_type", {
                    "arguments": {
                        "type": "person",
                        "handle": "invalid_handle_123"
                    }
                })
                
                # Should handle gracefully
                assert len(result.content) >= 1
                assert isinstance(result.content[0], TextContent)
                response_text = result.content[0].text
                
                # Should indicate error or empty result
                assert len(response_text.strip()) > 0


class TestParameterModels:
    """Test that server uses proper parameter models from parameters module."""
    
    def test_server_imports_parameter_models(self):
        """Test that server can import from src.gramps_mcp.models.parameters."""
        # Test that we can import the parameter models that should be used
        from src.gramps_mcp.models.parameters.family_params import FamilySaveParams
        from src.gramps_mcp.models.parameters.people_params import PersonData
        from src.gramps_mcp.models.parameters.search_params import SearchParams
        
        # Verify these are proper Pydantic models
        assert hasattr(SearchParams, 'model_fields')
        assert hasattr(PersonData, 'model_fields')
        assert hasattr(FamilySaveParams, 'model_fields')
        
        # Verify they have expected fields
        assert 'query' in SearchParams.model_fields
        assert 'pagesize' in SearchParams.model_fields
        assert 'primary_name' in PersonData.model_fields
        assert 'handle' in FamilySaveParams.model_fields


class TestMCPResources:
    """Test MCP resource functionality."""
    
    @pytest.mark.asyncio
    async def test_list_resources(self):
        """Test that resources are properly registered."""
        endpoint = f"{BASE_URL}/mcp"
        
        async with streamablehttp_client(endpoint) as client_streams:
            read_stream, write_stream, _ = client_streams
            async with ClientSession(read_stream, write_stream) as session:
                # Initialize session
                await session.initialize()
                
                # List resources
                resources_result = await session.list_resources()
                resources = resources_result.resources
                
                # Should have at least the GQL documentation resource
                resource_uris = {str(resource.uri) for resource in resources}
                assert "gql://documentation" in resource_uris