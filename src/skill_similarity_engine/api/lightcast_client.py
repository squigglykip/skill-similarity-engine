"""
Lightcast Skills API Client

A comprehensive Python client for interacting with the Lightcast Skills API v2.14.0
Supports all documented endpoints with proper authentication and error handling.

NO HARDCODED VALUES - All configuration externalized following PTH philosophy.
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from pathlib import Path

import requests
from requests.exceptions import RequestException, HTTPError

from ..config.architectural_config_manager import get_config_manager


@dataclass
class AuthToken:
    """Container for OAuth token information"""
    access_token: str
    expires_at: datetime
    token_type: str = "Bearer"
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired (with 5 minute buffer)"""
        return datetime.now() >= (self.expires_at - timedelta(minutes=5))
    
    @property
    def auth_header(self) -> Dict[str, str]:
        """Get authorization header"""
        return {"Authorization": f"{self.token_type} {self.access_token}"}


class LightcastAPIError(Exception):
    """Base exception for Lightcast API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class RateLimitError(LightcastAPIError):
    """Raised when API rate limit is exceeded"""
    pass


class AuthenticationError(LightcastAPIError):
    """Raised when authentication fails"""
    pass


class LightcastSkillsClient:
    """
    Comprehensive client for the Lightcast Skills API
    
    Handles authentication, rate limiting, and provides methods for all documented endpoints.
    """
    
    def __init__(self, client_id: str, client_secret: str, scope: Optional[str] = None):
        """
        Initialize the Lightcast Skills API client
        
        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            scope: OAuth scope (uses config default if None)
        """
        # Use architectural configuration manager (NO hardcoded values)
        self.config_manager = get_config_manager()
        
        # API endpoints from configuration
        self.BASE_URL = self.config_manager.get_nested_value('api', 'lightcast', 'base_url', default="https://emsiservices.com/skills")
        self.AUTH_URL = self.config_manager.get_nested_value('api', 'lightcast', 'auth_url', default="https://auth.emsicloud.com/connect/token")
        
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope if scope is not None else self.config_manager.get_nested_value('api', 'lightcast', 'default_scope', default="emsi_open")
        self._token: Optional[AuthToken] = None
        self._session = requests.session()
        
        # Rate limiting from configuration
        rate_limit_rps = self.config_manager.get_nested_value('api', 'lightcast', 'rate_limit_requests_per_second', default=5)
        self._min_request_interval = self.config_manager.get_nested_value('api', 'lightcast', 'min_request_interval_seconds', default=0.2)
        self._last_request_time = 0
    
    @classmethod
    def from_credentials_file(cls, filepath: Optional[Union[str, Path]] = None, **kwargs) -> "LightcastSkillsClient":
        """
        Create client from credentials file (configuration-driven file discovery)
        
        Args:
            filepath: Path to JSON credentials file (uses config search paths if None)
            **kwargs: Additional arguments to pass to constructor
            
        Returns:
            LightcastSkillsClient instance
        """
        # Use configuration-driven file discovery if no path provided
        if filepath is None:
            config_manager = get_config_manager()
            default_filename = config_manager.get_nested_value('api', 'lightcast', 'default_credentials_file', default="credentials.json")
            search_paths = config_manager.get_nested_value('api', 'lightcast', 'credentials_search_paths', default=["."])
            
            # Search for credentials file in configured paths
            filepath = None
            for search_path in search_paths:
                candidate = Path(search_path) / default_filename if search_path != "." else Path(default_filename)
                if candidate.exists():
                    filepath = candidate
                    break
            
            if filepath is None:
                raise FileNotFoundError(f"Credentials file '{default_filename}' not found in search paths: {search_paths}")
        
        with open(filepath, 'r') as f:
            credentials = json.load(f)
        
        return cls(
            client_id=credentials["CLIENT_ID"],
            client_secret=credentials["CLIENT_SECRET"],
            **kwargs
        )
    
    def _wait_for_rate_limit(self):
        """Ensure we don't exceed rate limits"""
        now = time.time()
        time_since_last = now - self._last_request_time
        
        if time_since_last < self._min_request_interval:
            time.sleep(self._min_request_interval - time_since_last)
        
        self._last_request_time = time.time()
    
    def _authenticate(self) -> AuthToken:
        """
        Authenticate with the Lightcast API and get access token
        
        Returns:
            AuthToken object
            
        Raises:
            AuthenticationError: If authentication fails
        """
        # Format as URL-encoded string as per API documentation
        payload = f"client_id={self.client_id}&client_secret={self.client_secret}&grant_type=client_credentials&scope={self.scope}"
        
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        try:
            response = self._session.post(self.AUTH_URL, data=payload, headers=headers)
            
            # Check for authentication errors before raising for status
            if response.status_code == 400:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error_description", error_data.get("error", "Bad Request"))
                    raise AuthenticationError(f"Authentication failed: {error_msg}")
                except json.JSONDecodeError:
                    raise AuthenticationError(f"Authentication failed: {response.text}")
            
            response.raise_for_status()
            
            data = response.json()
            expires_at = datetime.now() + timedelta(seconds=data["expires_in"])
            
            return AuthToken(
                access_token=data["access_token"],
                expires_at=expires_at,
                token_type=data.get("token_type", "Bearer")
            )
            
        except requests.RequestException as e:
            if not isinstance(e, AuthenticationError):
                raise AuthenticationError(f"Authentication failed: {str(e)}")
        except Exception as e:
            raise AuthenticationError(f"Authentication failed: {str(e)}")
    
    def _get_valid_token(self) -> AuthToken:
        """Get a valid access token, refreshing if necessary"""
        if not self._token or self._token.is_expired:
            self._token = self._authenticate()
        return self._token
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make authenticated request to API
        
        Args:
            method: HTTP method
            endpoint: API endpoint (without base URL)
            **kwargs: Additional arguments for requests
            
        Returns:
            JSON response data
            
        Raises:
            LightcastAPIError: For API errors
            RateLimitError: For rate limit exceeded
        """
        self._wait_for_rate_limit()
        
        token = self._get_valid_token()
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        
        headers = kwargs.pop("headers", {})
        headers.update(token.auth_header)
        
        try:
            response = self._session.request(method, url, headers=headers, **kwargs)
            
            if response.status_code == 429:
                raise RateLimitError("Rate limit exceeded", status_code=429)
            
            response.raise_for_status()
            return response.json()
            
        except requests.HTTPError as e:
            error_data = None
            try:
                error_data = response.json()
            except:
                pass
            
            raise LightcastAPIError(
                f"API request failed: {str(e)}", 
                status_code=response.status_code,
                response_data=error_data
            )
    
    # Status and Metadata Endpoints
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get service health status
        
        Returns:
            Status information including healthy flag
        """
        return self._make_request("GET", "/status")
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get service metadata including latest version and attribution
        
        Returns:
            Metadata including latest version and attribution text
        """
        return self._make_request("GET", "/meta")
    
    # Version Endpoints
    
    def list_versions(self) -> List[str]:
        """
        List all available skill taxonomy versions
        
        Returns:
            List of version strings
        """
        response = self._make_request("GET", "/versions")
        return response["data"]
    
    def get_version_metadata(self, version: str = "latest") -> Dict[str, Any]:
        """
        Get metadata for a specific version
        
        Args:
            version: Version string (default: "latest")
            
        Returns:
            Version metadata including fields, types, and skill counts
        """
        return self._make_request("GET", f"/versions/{version}")
    
    def get_version_changes(self, version: str = "latest") -> Dict[str, Any]:
        """
        Get changes for a specific version
        
        Args:
            version: Version string (default: "latest")
            
        Returns:
            Changes including additions, removals, renames, etc.
        """
        return self._make_request("GET", f"/versions/{version}/changes")
    
    # Skills Endpoints
    
    def list_skills(self, 
                   version: str = "latest",
                   query: Optional[str] = None,
                   type_ids: Optional[List[str]] = None,
                   fields: Optional[List[str]] = None,
                   limit: Optional[int] = None) -> Dict[str, Any]:
        """
        List skills with optional filtering
        
        Args:
            version: Version string (default: "latest")
            query: Search query for skill names
            type_ids: List of type IDs to filter by (ST1, ST2, ST3, ST0)
            fields: List of fields to include in response
            limit: Maximum number of results to return
            
        Returns:
            Skills data with attributions
        """
        params = {}
        
        if query:
            params["q"] = query
        if type_ids:
            params["typeIds"] = ",".join(type_ids)
        if fields:
            params["fields"] = ",".join(fields)
        if limit:
            params["limit"] = limit
        
        return self._make_request("GET", f"/versions/{version}/skills", params=params)
    
    def search_skills(self, query: str, version: str = "latest", **kwargs) -> Dict[str, Any]:
        """
        Search for skills by name
        
        Args:
            query: Search query
            version: Version string (default: "latest")
            **kwargs: Additional arguments for list_skills
            
        Returns:
            Matching skills
        """
        return self.list_skills(version=version, query=query, **kwargs)
    
    def get_skills_by_type(self, 
                          skill_type: str, 
                          version: str = "latest", 
                          **kwargs) -> Dict[str, Any]:
        """
        Get skills filtered by type
        
        Args:
            skill_type: Skill type ID (ST1, ST2, ST3, ST0)
            version: Version string (default: "latest")
            **kwargs: Additional arguments for list_skills
            
        Returns:
            Skills of specified type
        """
        return self.list_skills(version=version, type_ids=[skill_type], **kwargs)
    
    def get_specialized_skills(self, version: str = "latest", **kwargs) -> Dict[str, Any]:
        """Get specialized skills (ST1)"""
        return self.get_skills_by_type("ST1", version, **kwargs)
    
    def get_common_skills(self, version: str = "latest", **kwargs) -> Dict[str, Any]:
        """Get common skills (ST2)"""
        return self.get_skills_by_type("ST2", version, **kwargs)
    
    def get_certifications(self, version: str = "latest", **kwargs) -> Dict[str, Any]:
        """Get certification skills (ST3)"""
        return self.get_skills_by_type("ST3", version, **kwargs)
    
    # Utility Methods
    
    def get_all_skills_paginated(self, 
                                version: str = "latest",
                                page_size: int = 1000,
                                **kwargs) -> List[Dict[str, Any]]:
        """
        Get all skills - API may not support pagination, so get maximum available
        
        Args:
            version: Version string (default: "latest")
            page_size: Number of skills per request (may be limited by API)
            **kwargs: Additional arguments for list_skills
            
        Returns:
            List of all skills
        """
        # Try to get all skills in one request first
        # The API may have its own internal limits
        response = self.list_skills(
            version=version,
            limit=50000,  # Try a very large limit to get all skills
            **kwargs
        )
        
        skills = response.get("data", [])
        
        # If we got skills, return them
        if skills:
            return skills
        
        # Fallback: try without limit parameter
        response = self.list_skills(
            version=version,
            **kwargs
        )
        
        return response.get("data", [])
    
    def get_skill_statistics(self, version: str = "latest") -> Dict[str, Any]:
        """
        Get comprehensive statistics about skills in a version
        
        Args:
            version: Version string (default: "latest")
            
        Returns:
            Statistics including counts by type
        """
        metadata = self.get_version_metadata(version)
        version_data = metadata["data"]
        
        stats = {
            "version": version_data["version"],
            "total_skills": version_data["skillCount"],
            "removed_skills": version_data["removedSkillCount"],
            "types": {}
        }
        
        # Get counts by type
        for skill_type in version_data["types"]:
            type_id = skill_type["id"]
            if type_id != "ST0":  # Skip removed skills
                type_skills = self.list_skills(version=version, type_ids=[type_id], limit=1)
                # Note: This is a simplified count - for exact counts you'd need to paginate
                stats["types"][skill_type["name"]] = {
                    "id": type_id,
                    "description": skill_type["description"]
                }
        
        return stats


# Convenience function for quick access
def create_client(credentials_file: str = "credentials.json") -> LightcastSkillsClient:
    """
    Create a Lightcast Skills API client from credentials file
    
    Args:
        credentials_file: Path to credentials JSON file
        
    Returns:
        LightcastSkillsClient instance
    """
    return LightcastSkillsClient.from_credentials_file(credentials_file) 
