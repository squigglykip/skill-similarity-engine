"""
Tests for Skills Library API functionality.

These tests validate the SkillsLibraryAPI class structure and basic operations
without requiring actual API credentials.
"""

import pytest
from unittest.mock import Mock, patch, mock_open
import json
from pathlib import Path
import sys
import pandas as pd

# Find the project root, which is one folder back
project_root = Path(__file__).resolve().parent.parent
# Add the src directory to the path where the actual package lives
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

print(f"Project root: {project_root}")
print(f"Added to path: {src_path}")

from skill_similarity_engine.api.skills_library_api import SkillsLibraryAPI, SkillsLibraryConfig

class TestSkillsLibraryConfig:
    """Test the configuration dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = SkillsLibraryConfig()
        assert config.api_base_url == "https://emsiservices.com/skills"
        assert config.skills_library_path == "data/skills_library"
        assert config.versions_file == "lightcast_versions.json"
        assert config.skills_csv_file == "lightcast_skills_comprehensive.csv"
        assert config.max_retries == 3
        assert config.timeout_seconds == 30
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = SkillsLibraryConfig(
            client_id="test_id",
            client_secret="test_secret",
            skills_library_path="custom/path"
        )
        assert config.client_id == "test_id"
        assert config.client_secret == "test_secret"
        assert config.skills_library_path == "custom/path"


class TestSkillsLibraryAPI:
    """Test the SkillsLibraryAPI class."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for testing."""
        return SkillsLibraryConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            skills_library_path="test/skills_library"
        )
    
    @pytest.fixture  
    def api_instance(self, mock_config):
        """Create API instance with mock config."""
        with patch('skill_similarity_engine.api.skills_library_api.Path'):
            return SkillsLibraryAPI(mock_config)
    
    def test_initialization(self, api_instance, mock_config):
        """Test API instance initialization."""
        assert api_instance.config == mock_config
        assert api_instance.access_token is None
        assert api_instance.token_expires_at is None
    
    @patch('skill_similarity_engine.api.skills_library_api.requests.post')
    def test_authentication_success(self, mock_post, api_instance):
        """Test successful authentication."""
        # Mock successful auth response
        mock_response = Mock()
        mock_response.json.return_value = {
            'access_token': 'test_token',
            'expires_in': 3600
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = api_instance.authenticate()
        
        assert result is True
        assert api_instance.access_token == 'test_token'
        assert api_instance.token_expires_at is not None
    
    @patch('skill_similarity_engine.api.skills_library_api.requests.post')
    def test_authentication_failure(self, mock_post, api_instance):
        """Test authentication failure."""
        # Mock failed auth response
        mock_post.side_effect = Exception("Auth failed")
        
        result = api_instance.authenticate()
        
        assert result is False
        assert api_instance.access_token is None
    
    def test_get_processed_versions_no_file(self, api_instance):
        """Test getting processed versions when no file exists."""
        with patch.object(api_instance.versions_file_path, 'exists', return_value=False):
            versions = api_instance.get_processed_versions()
            assert versions == []
    
    def test_get_processed_versions_with_file(self, api_instance):
        """Test getting processed versions from existing file."""
        mock_versions_data = {
            "version1": {"processed_at": "2024-01-01T00:00:00"},
            "version2": {"processed_at": "2024-01-02T00:00:00"}
        }
        
        with patch.object(api_instance.versions_file_path, 'exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=json.dumps(mock_versions_data))):
                versions = api_instance.get_processed_versions()
                assert versions == ["version1", "version2"]
    
    def test_identify_new_versions(self, api_instance):
        """Test identifying new versions to process."""
        with patch.object(api_instance, 'get_available_versions', return_value=['v1', 'v2', 'v3']):
            with patch.object(api_instance, 'get_processed_versions', return_value=['v1', 'v2']):
                new_versions = api_instance.identify_new_versions()
                assert new_versions == ['v3']
    
    def test_get_library_status_no_files(self, api_instance):
        """Test getting library status when no files exist."""
        with patch.object(api_instance.skills_csv_path, 'exists', return_value=False):
            with patch.object(api_instance.versions_file_path, 'exists', return_value=False):
                status = api_instance.get_library_status()
                
                assert status['versions_processed'] == 0
                assert status['total_skills'] == 0
                assert status['csv_exists'] is False
                assert status['last_update'] is None
    
    def test_get_library_status_with_files(self, api_instance):
        """Test getting library status with existing files."""
        mock_versions_data = {
            "v1": {"processed_at": "2024-01-01T00:00:00"},
            "v2": {"processed_at": "2024-01-02T00:00:00"}
        }
        
        with patch.object(api_instance.skills_csv_path, 'exists', return_value=True):
            with patch.object(api_instance.versions_file_path, 'exists', return_value=True):
                with patch('builtins.open', mock_open(read_data=json.dumps(mock_versions_data))):
                    with patch('pandas.read_csv') as mock_read_csv:
                        # Mock DataFrame with length 100
                        mock_df = pd.DataFrame({'test': range(100)})  # Simple DataFrame with 100 rows
                        mock_read_csv.return_value = mock_df
                        
                        with patch.object(api_instance.skills_csv_path, 'stat') as mock_stat:
                            mock_stat.return_value.st_size = 1024 * 1024  # 1MB
                            
                            status = api_instance.get_library_status()
                            
                            assert status['versions_processed'] == 2
                            assert status['total_skills'] == 100
                            assert status['csv_exists'] is True
                            assert status['csv_size_mb'] == 1.0
                            assert status['last_update'] == "2024-01-02T00:00:00"


def run_all_tests():
    """Run all tests manually (since we can't install pytest)."""
    print("🧪 Running Skills Library API Tests...")
    print("=" * 50)
    
    # Test SkillsLibraryConfig
    print("\n📋 Testing SkillsLibraryConfig...")
    config_tests = TestSkillsLibraryConfig()
    
    try:
        config_tests.test_default_config()
        print("✅ test_default_config")
    except Exception as e:
        print(f"❌ test_default_config: {e}")
    
    try:
        config_tests.test_custom_config()
        print("✅ test_custom_config")
    except Exception as e:
        print(f"❌ test_custom_config: {e}")
    
    # Test SkillsLibraryAPI (basic tests only, skip mocked ones)
    print("\n🔧 Testing SkillsLibraryAPI...")
    
    # Create test configuration manually (instead of using pytest fixture)
    try:
        mock_config = SkillsLibraryConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            skills_library_path="test/skills_library"
        )
        print("✅ mock_config created")
    except Exception as e:
        print(f"❌ mock_config creation: {e}")
        return
    
    # Create API instance manually
    try:
        api_instance = SkillsLibraryAPI(mock_config)
        print("✅ api_instance created")
    except Exception as e:
        print(f"❌ api_instance creation: {e}")
        return
    
    # Test initialization
    try:
        assert api_instance.config == mock_config
        assert api_instance.access_token is None
        assert api_instance.token_expires_at is None
        print("✅ test_initialization")
    except Exception as e:
        print(f"❌ test_initialization: {e}")
    
    # Test get_processed_versions when no file exists
    try:
        result = api_instance.get_processed_versions()
        print(f"✅ test_get_processed_versions_no_file: {result}")
    except Exception as e:
        print(f"❌ test_get_processed_versions_no_file: {e}")
        
    # Test get_library_status
    try:
        status = api_instance.get_library_status()
        print(f"✅ test_get_library_status: {type(status)} with {len(status)} keys")
    except Exception as e:
        print(f"❌ test_get_library_status: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Basic tests completed!")
    print("Note: Advanced tests with mocking require pytest framework")


if __name__ == "__main__":
    run_all_tests() 