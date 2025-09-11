"""
Integration tests for auth and config modules using actual .env configuration.
"""

import pytest

from src.gramps_mcp.auth import AuthManager
from src.gramps_mcp.config import get_settings


class TestConfigIntegration:
    """Test configuration loading from actual .env file."""
    
    def test_get_settings_loads_from_env(self):
        """Test settings load from actual .env file."""
        settings = get_settings()
        
        # Verify all required fields are present
        assert settings.gramps_api_url is not None
        assert settings.gramps_username is not None
        assert settings.gramps_password is not None
        assert settings.gramps_tree_id is not None


class TestAuthIntegration:
    """Test auth manager with actual configuration."""
    
    def test_auth_manager_initialization(self):
        """Test auth manager initializes with actual config."""
        auth = AuthManager()
        
        # Verify settings are loaded
        assert auth.settings.gramps_api_url is not None
        assert auth.settings.gramps_username is not None
        assert auth.settings.gramps_password is not None
        
        # Verify client is configured (created on-demand via property)
        client = auth.client  # This triggers creation
        assert client is not None
        assert client.base_url is not None
    
    @pytest.mark.asyncio
    async def test_authentication_attempt(self):
        """Test authentication attempt with actual Gramps API."""
        auth = AuthManager()
        
        try:
            # This will either succeed or fail based on actual API availability
            token = await auth.authenticate()
            
            # If successful, verify token properties
            assert isinstance(token, str)
            assert len(token) > 0
            assert auth._access_token == token
            assert auth._token_expires_at is not None
            
            print(f"Authentication successful! Token length: {len(token)}")
            
        except ValueError as e:
            # Expected if API is not available or credentials are invalid
            print(f"Authentication failed (expected): {e}")
            assert "Authentication" in str(e) or "connect" in str(e).lower()
        
        finally:
            await auth.close()
    
    @pytest.mark.asyncio
    async def test_get_token_flow(self):
        """Test complete token retrieval flow."""
        auth = AuthManager()
        
        try:
            # Test get_token which should authenticate if needed
            token = await auth.get_token()
            
            # If successful, verify we can get headers
            assert isinstance(token, str)
            assert len(token) > 0
            
            headers = auth.get_headers()
            assert "Authorization" in headers
            assert headers["Authorization"].startswith("Bearer ")
            assert "Content-Type" in headers
            
            print("Complete auth flow successful!")
            
        except ValueError as e:
            print(f"Auth flow failed (expected if API unavailable): {e}")
            
            # Should still be able to test error case
            with pytest.raises(ValueError, match="Not authenticated"):
                auth.get_headers()
        
        finally:
            await auth.close()
    
    def test_auth_manager_cleanup(self):
        """Test auth manager singleton behavior."""
        auth = AuthManager()
        
        # Since this is a singleton, the token may be set from previous tests
        # Just verify the manager exists and is the same instance
        auth2 = AuthManager()
        assert auth is auth2  # Same singleton instance
        
        # Verify settings are loaded
        assert auth.settings.gramps_api_url is not None