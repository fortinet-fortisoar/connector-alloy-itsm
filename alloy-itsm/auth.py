"""
Copyright start
MIT License
Copyright (c) 2025 Fortinet Inc
Copyright end
"""

import requests
import time
import threading
from threading import Lock
from connectors.core.connector import ConnectorError, get_logger
from .constants import LOGGER_NAME

logger = get_logger(LOGGER_NAME)

# Token cache with thread safety
_token_cache = {}
_cache_lock = Lock()


class AlloyAuth:
    """
    Handles authentication for Alloy Navigator Express API
    Supports both Application Account and Technician Account authentication
    Manages token generation, caching, and expiry (8-hour tokens)
    """

    def __init__(self, config):
        """
        Initialize authentication handler

        Args:
            config (dict): Connector configuration
        """
        self.server_url = config.get("server_url", "").rstrip("/")
        self.auth_type = config.get("auth_type", "Application Account")
        self.verify_ssl = config.get("verify_ssl")

        # Validate required configuration based on auth type
        if not self.server_url:
            raise ConnectorError("Missing required configuration: server_url")

        # Validate URL format
        if not self.server_url.startswith(('http://', 'https://')):
            raise ConnectorError("server_url must start with http:// or https://")

        # Initialize credentials based on authentication type
        if self.auth_type == "Application Account":
            self.client_id = config.get("client_id")
            self.client_secret = config.get("client_secret")

            if not self.client_id or not self.client_secret:
                raise ConnectorError("Missing required configuration for Application Account: client_id, client_secret")

            if not isinstance(self.client_id, str) or not self.client_id.strip():
                raise ConnectorError("client_id must be a non-empty string")

            if not isinstance(self.client_secret, str) or not self.client_secret.strip():
                raise ConnectorError("client_secret must be a non-empty string")

        elif self.auth_type == "Technician Account":
            self.username = config.get("username")
            self.password = config.get("password")

            if not self.username or not self.password:
                raise ConnectorError("Missing required configuration for Technician Account: username, password")

            if not isinstance(self.username, str) or not self.username.strip():
                raise ConnectorError("username must be a non-empty string")

            if not isinstance(self.password, str) or not self.password.strip():
                raise ConnectorError("password must be a non-empty string")

        else:
            raise ConnectorError(
                f"Invalid auth_type: {self.auth_type}. Must be 'Application Account' or 'Technician Account'")

    def _get_cached_token(self):
        """
        Return cached token if still valid
        Returns:
            str or None: Valid access token or None if expired/missing
        """
        with _cache_lock:
            # Use server_url + auth_type as cache key to separate tokens
            cache_key = f"{self.server_url}_{self.auth_type}"
            token_data = _token_cache.get(cache_key)
            if token_data:
                expires_at = token_data.get("expires_at", 0)
                if time.time() < expires_at:
                    logger.debug(f"Using cached Alloy Navigator Express token ({self.auth_type})")
                    return token_data.get("access_token")
        return None

    def _cache_token(self, token_response):
        """
        Store token with expiry in cache
        Args:
            token_response (dict): Token response from API
        Returns:
            str: Access token
        """
        access_token = token_response.get("access_token")
        expires_in = token_response.get("expires_in", 28800)  # 8 hours default

        with _cache_lock:
            # Use server_url + auth_type as cache key
            cache_key = f"{self.server_url}_{self.auth_type}"
            _token_cache[cache_key] = {
                "access_token": access_token,
                "expires_at": time.time() + int(expires_in) - 300  # refresh 5 min before expiry
            }

        logger.debug(f"Token cached for {self.server_url} ({self.auth_type}), expires in {expires_in} seconds")
        return access_token

    def _generate_token(self):
        """
        Request new token from Alloy Navigator Express API
        Returns:
            str: Access token
        Raises:
            ConnectorError: If token generation fails
        """
        url = f"{self.server_url}/token"

        # Build payload based on authentication type
        if self.auth_type == "Application Account":
            payload = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
            logger.debug("Requesting new Alloy Navigator Express token (Application Account)")
        else:  # Technician Account
            payload = {
                "grant_type": "password",
                "username": self.username,
                "password": self.password
            }
            logger.debug("Requesting new Alloy Navigator Express token (Technician Account)")

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        try:
            response = requests.post(
                url,
                data=payload,
                headers=headers,
                verify=self.verify_ssl,
                timeout=30
            )

            # Handle specific error responses
            if response.status_code == 400:
                try:
                    error_data = response.json()
                    error_type = error_data.get("error", "unknown_error")

                    if error_type == "unsupported_grant_type":
                        expected_grant = "client_credentials" if self.auth_type == "Application Account" else "password"
                        raise ConnectorError(f"Invalid grant_type, must be '{expected_grant}'")
                    elif error_type == "invalid_grant":
                        raise ConnectorError("Incorrect username or password")
                    elif error_type == "invalid_client":
                        raise ConnectorError("Incorrect application ID or secret")
                    else:
                        raise ConnectorError(f"Authentication error: {error_type}")
                except ValueError:
                    raise ConnectorError(f"Authentication failed: {response.text}")

            elif response.status_code == 401:
                raise ConnectorError("Authentication failed: Invalid credentials")
            elif response.status_code == 403:
                raise ConnectorError("Access forbidden: Check user permissions")
            elif response.status_code == 404:
                raise ConnectorError("API endpoint not found: Check server_url")
            elif response.status_code != 200:
                logger.error(f"Token request failed: {response.status_code} - {response.text}")
                raise ConnectorError(f"Failed to get access token: HTTP {response.status_code}")

            # Parse and validate JSON response
            try:
                token_response = response.json()
            except ValueError as e:
                logger.error(f"Invalid JSON response from token endpoint: {response.text}")
                raise ConnectorError(f"Invalid response format from Alloy Navigator Express: {str(e)}")

            # Validate required fields in response
            if not token_response.get("access_token"):
                logger.error(f"No access token in response: {token_response}")
                raise ConnectorError("Invalid token response: missing access_token")

            if token_response.get("token_type", "").lower() != "bearer":
                logger.warning(f"Unexpected token type: {token_response.get('token_type')}")

            return self._cache_token(token_response)

        except requests.exceptions.SSLError:
            raise ConnectorError("SSL certificate verification failed while connecting to Alloy Navigator Express")
        except requests.exceptions.ConnectionError:
            raise ConnectorError("Unable to connect to Alloy Navigator Express server")
        except requests.exceptions.Timeout:
            raise ConnectorError("Request timeout while connecting to Alloy Navigator Express")
        except ConnectorError:
            raise  # Re-raise connector errors as-is
        except Exception as err:
            logger.error(f"Unexpected error while generating token: {err}", exc_info=True)
            raise ConnectorError(f"Error generating token: {str(err)}")

    def get_access_token(self):
        """
        Get a valid access token (from cache or generate new one)
        Returns:
            str: Valid access token
        Raises:
            ConnectorError: If unable to get valid token
        """
        # Try to get cached token first
        token = self._get_cached_token()
        if token:
            return token

        # Generate new token if no valid cached token
        return self._generate_token()

    def get_auth_header(self):
        """
        Get the authorization header for API requests
        Returns:
            dict: Authorization header with Bearer token
        """
        token = self.get_access_token()
        return {"Authorization": f"Bearer {token}"}

    @classmethod
    def cleanup_expired_tokens(cls):
        """Clean up expired tokens from cache"""
        with _cache_lock:
            current_time = time.time()
            expired_keys = [
                key for key, data in _token_cache.items()
                if current_time >= data.get("expires_at", 0)
            ]
            for key in expired_keys:
                del _token_cache[key]
                logger.debug(f"Cleaned up expired token for {key}")
