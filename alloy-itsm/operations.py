"""
Copyright start
MIT License
Copyright (c) 2025 Fortinet Inc
Copyright end
"""

from connectors.core.connector import ConnectorError, get_logger
import requests
import arrow
import urllib.parse
import json
import base64
import mimetypes
from os.path import join
from .auth import AlloyAuth
from .constants import LOGGER_NAME, ENDPOINTS

try:
    from integrations.crudhub import make_request, download_file_from_cyops
    from integrations.crudhub import make_request, make_file_upload_request
except:
    pass

logger = get_logger(LOGGER_NAME)


class AlloyClient:
    def __init__(self, config):
        """
        Initialize Alloy Navigator Express client
        Args:
            config (dict): Connector configuration
        """
        self.config = config
        self.server_url = config.get('server_url', '').rstrip('/')
        self.verify_ssl = config.get('verify_ssl', True)

        # Initialize authentication handler
        self.auth = AlloyAuth(config)

        if not self.server_url:
            raise ConnectorError("Server URL is required")

    def make_request(self, method, endpoint, params=None, data=None, operation_name=None):
        """
        Make HTTP request to Alloy Navigator Express API with proper authentication
        Args:
            method (str): HTTP method (GET, POST, PUT, DELETE)
            endpoint (str): API endpoint (e.g., '/incidents')
            params (dict): Query parameters
            data (dict): Request body data
            operation_name (str): Name of the operation for logging
        Returns:
            dict: API response
        Raises:
            ConnectorError: If request fails
        """
        try:
            # Build full URL
            url = f"{self.server_url}{endpoint}"

            # Get authentication headers
            headers = self.auth.get_auth_header()
            headers.update({
                "Content-Type": "application/json"
            })

            logger.debug(f"Making {method} request to {url}")

            # Make the request
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data,
                verify=self.verify_ssl,
            )
            # Handle different HTTP status codes
            if response.status_code in [200, 201]:
                try:
                    return response.json() if response.text else {}
                except ValueError:
                    # If response is not JSON, return text
                    return {"message": response.text}
            elif response.status_code == 204:
                return {"status": "success", "message": "Operation completed successfully"}
            elif response.status_code == 202:
                return {"status": "accepted", "message": "Request accepted, processing in background"}
            elif response.status_code == 400:
                error_msg = self._extract_error_message(response)
                raise ConnectorError(f"Bad Request: {error_msg}")
            elif response.status_code == 401:
                # Token might be expired, clear cache and retry once
                logger.warning("Authentication failed, clearing token cache")
                AlloyAuth.cleanup_expired_tokens()
                raise ConnectorError("Authentication failed - check credentials")
            elif response.status_code == 403:
                raise ConnectorError("Access forbidden - insufficient permissions")
            elif response.status_code == 404:
                raise ConnectorError("Resource not found")
            elif response.status_code == 429:
                raise ConnectorError("Rate limit exceeded - please try again later")
            elif response.status_code >= 500:
                raise ConnectorError(f"Server error: {response.status_code}")
            else:
                error_msg = self._extract_error_message(response)
                logger.error(f"Request failed | Status: {response.status_code} | Response: {response.text}")
                raise ConnectorError(f"API call failed: {response.status_code} - {error_msg}")

        except requests.exceptions.ConnectionError:
            raise ConnectorError("Connection error - unable to reach API endpoint")
        except requests.exceptions.SSLError:
            raise ConnectorError("SSL verification failed - check SSL configuration")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request Exception: {e}")
            raise ConnectorError(f"Request failed: {str(e)}")

    def _extract_error_message(self, response):
        """Extract error message from response safely"""
        try:
            error_data = response.json()
            if not error_data:
                return response.text or 'Unknown error'

            # Check common error fields
            message = error_data.get('message') or error_data.get('error_description') or 'Unknown error'
            errors = error_data.get('errors')

            if errors:
                return f"{message} - {errors}"
            return message

        except ValueError:
            # Response is not JSON
            return response.text or 'Unknown error'


def check_health(config):
    """
    Health check by testing authentication and making a simple API call
    Args:
        config (dict): Connector configuration
    Returns:
        dict: Health check result
    Raises:
        ConnectorError: If health check fails
    """
    try:
        client = AlloyClient(config)
        auth_type = config.get("auth_type", "Application Account")

        # Test authentication by getting a token
        token = client.auth.get_access_token()

        if not token:
            raise ConnectorError("Failed to obtain access token")

        # For Application Accounts, just verify token generation
        if auth_type == "Application Account":
            return {
                "status": "success",
                "details": "Successfully authenticated with Alloy Navigator Express API using Application Account",
                "server_url": client.server_url,
                "token_obtained": True,
                "auth_type": auth_type
            }

        # For Technician accounts, test with profile endpoint
        elif auth_type == "Technician Account":
            url = f"{client.server_url}{ENDPOINTS['profile']}"
            headers = client.auth.get_auth_header()
            headers.update({
                "Content-Type": "application/json"
            })

            response = requests.get(
                url,
                headers=headers,
                verify=client.verify_ssl,
                timeout=30
            )

            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get("success"):
                        response_object = result.get("responseObject", {})
                        items = response_object.get("Items", [])
                        user_info = _parse_user_items(items)

                        return {
                            "status": "success",
                            "details": "Successfully connected to Alloy Navigator Express API and retrieved user profile",
                            "server_url": client.server_url,
                            "token_obtained": True,
                            "auth_type": auth_type,
                            "api_version": "v2",
                            "authenticated_user": user_info.get("full_name", "Unknown"),
                            "user_id": user_info.get("id", "Unknown"),
                            "is_technician": user_info.get("is_technician", "Unknown")
                        }
                    else:
                        error_text = result.get("errorText", "Unknown error")
                        raise ConnectorError(f"API health check failed: {error_text}")
                except ValueError:
                    raise ConnectorError("Invalid JSON response during health check")
            else:
                raise ConnectorError(f"Health check failed: HTTP {response.status_code}")

    except ConnectorError as e:
        logger.error(f"Health check failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during health check: {e}", exc_info=True)
        raise ConnectorError(f"Health check failed: {str(e)}")


def get_current_user_profile(config, params):
    """
    Retrieve information about the currently logged in user/technician
    Args:
        config (dict): Connector configuration
        params (dict): Operation parameters (not used)
    Returns:
        dict: Current user profile data
    """
    client = AlloyClient(config)

    # Use v2 API endpoint for profile
    url = f"{client.server_url}{ENDPOINTS['profile']}"
    headers = client.auth.get_auth_header()
    headers["Accept"] = "application/json"

    response = requests.get(url, headers=headers, verify=client.verify_ssl, timeout=30)

    if response.status_code == 200:
        result = response.json()
        if not result.get("success"):
            error_text = result.get("errorText", "Unknown error")
            raise ConnectorError(f"API error: {error_text}")

        # Add simplified user info
        items = result.get("responseObject", {}).get("Items", [])
        result["user_info"] = _parse_user_items(items)
        return result

    elif response.status_code == 401:
        AlloyAuth.cleanup_expired_tokens()
        raise ConnectorError("Authentication failed")
    else:
        raise ConnectorError(f"Failed to get user profile: HTTP {response.status_code}")


def get_objects(config, params):
    """
    Retrieve information about Alloy Navigator objects with filtering, sorting, and pagination
    Args:
        config (dict): Connector configuration
        params (dict): Operation parameters including:
            - object_class (required): Object class name (e.g., Incidents, Computers)
            - par_fields: Comma-separated list of fields to return
            - par_sort_asc: Fields to sort ascending
            - par_sort_desc: Fields to sort descending
            - par_limit: Number of records to return
            - par_offset: Number of records to skip
            - par_search_text: Search string for partial text search
            - filters: Additional filtering criteria as JSON object
    Returns:
        dict: API response with Fields and Data arrays
    """
    client = AlloyClient(config)

    # Validate required parameter
    object_class = params.get("object_class")
    if not object_class:
        raise ConnectorError("Missing required parameter: object_class")

    # Build query parameters
    query_params = {}

    # Add optional parameters if provided
    optional_params = [
        "par_fields", "par_sort_asc", "par_sort_desc",
        "par_limit", "par_offset", "par_search_text"
    ]

    for param in optional_params:
        value = params.get(param)
        if value is not None and str(value).strip():
            query_params[param] = value

    # Add filter criteria from JSON object
    filters = params.get("filters")
    if filters:
        try:
            if isinstance(filters, str):
                filter_dict = [item.strip() for item in filters.split(",")]
            else:
                filter_dict = filters

            # Add each filter as query parameter
            for key, value in filter_dict.items():
                query_params[key] = value
        except json.JSONDecodeError as e:
            raise ConnectorError(f"Invalid filters JSON format: {str(e)}")

    # Make API request
    endpoint = ENDPOINTS['objects'].format(object_class=object_class)
    result = client.make_request(
        method="GET",
        endpoint=endpoint,
        params=query_params,
        operation_name="get_objects"
    )

    # Validate response structure
    if not result.get("success"):
        error_text = result.get("errorText", "Unknown error")
        raise ConnectorError(f"API error: {error_text}")

    return result


def get_objects_advanced(config, params):
    """
    Retrieve Alloy Navigator objects using POST method with advanced filtering
    Args:
        config (dict): Connector configuration
        params (dict): Operation parameters including:
            - object_class (required): Object class name (e.g., Incidents, Computers)
            - fields: JSON array of field names to return
            - filters: JSON array of filter objects with name, value, operation
            - sort: JSON array of sort objects with property and direction
            - limit: Number of records to return
            - offset: Number of records to skip
            - searchText: Search string for partial text search
    Returns:
        dict: API response with Fields and Data arrays
    Raises:
        ConnectorError: If object class not found or invalid parameters
    Note:
        POST method supports advanced filter operators: =, <>, >, >=, <, <=
        No URL length limitations compared to GET method
    """
    client = AlloyClient(config)

    # Validate required parameter
    object_class = params.get("object_class")
    if not object_class:
        raise ConnectorError("Missing required parameter: object_class")

    object_class = str(object_class).strip()
    if not object_class:
        raise ConnectorError("Object class cannot be empty")

    # Build POST body
    post_body = {}

    # Handle fields parameter
    fields = params.get("fields")
    if fields:
        try:
            if isinstance(fields, str):
                fields_list = [item.strip() for item in fields.split(",")]
            else:
                fields_list = fields

            if isinstance(fields_list, list):
                post_body["fields"] = fields_list
            else:
                raise ConnectorError("Fields must be a JSON array")
        except json.JSONDecodeError as e:
            raise ConnectorError(f"Invalid fields JSON format: {str(e)}")

    # Handle filters parameter
    filters = params.get("filters")
    if filters:
        try:
            if isinstance(filters, str):
                filters_list = [item.strip() for item in filters.split(",")]
            else:
                filters_list = filters

            if isinstance(filters_list, list):
                # Validate filter structure
                for f in filters_list:
                    if not isinstance(f, dict):
                        raise ConnectorError("Each filter must be an object with name, value, and operation")
                    if "name" not in f or "value" not in f or "operation" not in f:
                        raise ConnectorError("Each filter must have 'name', 'value', and 'operation' properties")
                    # Validate operation
                    valid_ops = ["=", "<>", ">", ">=", "<", "<="]
                    if f["operation"] not in valid_ops:
                        raise ConnectorError(
                            f"Invalid operation '{f['operation']}'. Must be one of: {', '.join(valid_ops)}")

                post_body["filters"] = filters_list
            else:
                raise ConnectorError("Filters must be a JSON array")
        except json.JSONDecodeError as e:
            raise ConnectorError(f"Invalid filters JSON format: {str(e)}")

    # Handle sort parameter
    sort = params.get("sort")
    if sort:
        try:
            if isinstance(sort, str):
                sort_list = [item.strip() for item in sort.split(",")]
            else:
                sort_list = sort

            if isinstance(sort_list, list):
                # Validate sort structure
                for s in sort_list:
                    if not isinstance(s, dict):
                        raise ConnectorError("Each sort must be an object with property and direction")
                    if "property" not in s or "direction" not in s:
                        raise ConnectorError("Each sort must have 'property' and 'direction' properties")
                    # Validate direction
                    if s["direction"].lower() not in ["asc", "desc"]:
                        raise ConnectorError(f"Invalid sort direction '{s['direction']}'. Must be 'asc' or 'desc'")

                post_body["sort"] = sort_list
            else:
                raise ConnectorError("Sort must be a JSON array")
        except json.JSONDecodeError as e:
            raise ConnectorError(f"Invalid sort JSON format: {str(e)}")

    # Handle simple parameters
    if params.get("limit") is not None:
        post_body["limit"] = params.get("limit")

    if params.get("offset") is not None:
        post_body["offset"] = params.get("offset")

    if params.get("searchText"):
        post_body["searchText"] = params.get("searchText")

    # Build endpoint
    endpoint = ENDPOINTS['objects_advanced'].format(object_class=object_class)

    # Make API request with POST method
    result = client.make_request(
        method="POST",
        endpoint=endpoint,
        data=post_body,
        operation_name="get_objects_advanced"
    )

    # Validate response structure
    if not result.get("success"):
        error_text = result.get("errorText", "Unknown error")
        raise ConnectorError(f"API error: {error_text}")

    return result


def get_object_by_id(config, params):
    """
    Retrieve all fields of a particular object using its OID or database ID
    Args:
        config (dict): Connector configuration
        params (dict): Operation parameters including:
            - oid (required): Object identifier (OID like T000002 or GUID like {EB6D7E24-...})
    Returns:
        dict: API response with Items array containing all object fields
    Raises:
        ConnectorError: If object not found or user lacks permissions
    Note:
        - Cannot be used for Software Catalog and Stock Room objects
        - For those, use get_objects() method instead
    """
    client = AlloyClient(config)

    # Validate required parameter
    oid = params.get("oid")
    if not oid:
        raise ConnectorError("Missing required parameter: oid")

    # Trim whitespace
    oid = str(oid).strip()
    if not oid:
        raise ConnectorError("Object identifier (oid) cannot be empty")

    # Build endpoint with object identifier
    endpoint = ENDPOINTS['object_by_id'].format(oid=oid)

    # Make API request
    result = client.make_request(
        method="GET",
        endpoint=endpoint,
        operation_name="get_object_by_id"
    )

    # Validate response structure
    if not result.get("success"):
        error_text = result.get("errorText", "Unknown error")
        error_code = result.get("errorCode", 0)

        # Handle specific error messages
        if "not found" in error_text.lower():
            raise ConnectorError(f"Object '{oid}' not found in the system")
        elif "permissions" in error_text.lower() or "access" in error_text.lower():
            raise ConnectorError(f"Insufficient permissions to access object '{oid}'")
        else:
            raise ConnectorError(f"API error (code {error_code}): {error_text}")

    return result


def get_object_activities(config, params):
    """
    Retrieve activities/history for a specific Alloy Navigator object
    Args:
        config (dict): Connector configuration
        params (dict): Operation parameters including:
            - oid (required): Object identifier (e.g., T000027)
            - par_fields: Comma-separated list of activity fields to return
            - par_sort_asc: Fields to sort ascending
            - par_sort_desc: Fields to sort descending
            - par_limit: Number of records to return
            - par_offset: Number of records to skip
            - filters: Additional filtering criteria as JSON object
    Returns:
        dict: API response with Fields and Data arrays containing activity records
    Raises:
        ConnectorError: If object not found or user lacks permissions
    Note:
        - Cannot be used for Software Catalog and Stock Room objects
        - Activities include status changes, comments, updates, and other object history
    """
    client = AlloyClient(config)

    # Validate required parameter
    oid = params.get("oid")
    if not oid:
        raise ConnectorError("Missing required parameter: oid")

    # Trim whitespace
    oid = str(oid).strip()
    if not oid:
        raise ConnectorError("Object identifier (oid) cannot be empty")

    # Build query parameters
    query_params = {}

    # Add optional parameters if provided
    optional_params = [
        "par_fields", "par_sort_asc", "par_sort_desc",
        "par_limit", "par_offset"
    ]

    for param in optional_params:
        value = params.get(param)
        if value is not None and str(value).strip():
            query_params[param] = value

    # Add filter criteria from JSON object
    filters = params.get("filters")
    if filters:
        try:
            if isinstance(filters, str):
                filter_dict = [item.strip() for item in filters.split(",")]
            else:
                filter_dict = filters

            # Add each filter as query parameter
            for key, value in filter_dict.items():
                query_params[key] = value
        except json.JSONDecodeError as e:
            raise ConnectorError(f"Invalid filters JSON format: {str(e)}")

    # Build endpoint with object identifier
    endpoint = ENDPOINTS['activities'].format(oid=oid)

    # Make API request
    result = client.make_request(
        method="GET",
        endpoint=endpoint,
        params=query_params,
        operation_name="get_object_activities"
    )

    # Validate response structure
    if not result.get("success"):
        error_text = result.get("errorText", "Unknown error")
        error_code = result.get("errorCode", 0)

        # Handle specific error messages
        if "not found" in error_text.lower():
            raise ConnectorError(f"Object '{oid}' not found in the system")
        elif "permissions" in error_text.lower() or "access" in error_text.lower():
            raise ConnectorError(f"Insufficient permissions to access activities for object '{oid}'")
        else:
            raise ConnectorError(f"API error (code {error_code}): {error_text}")

    return result


def get_object_activities_advanced(config, params):
    """
    Retrieve object activities using POST method with advanced filtering
    Args:
        config (dict): Connector configuration
        params (dict): Operation parameters including:
            - oid (required): Object identifier (e.g., T000027)
            - fields: JSON array of activity field names to return
            - filters: JSON array of filter objects with name, value, operation
            - sort: JSON array of sort objects with property and direction
            - limit: Number of records to return
            - offset: Number of records to skip
    Returns:
        dict: API response with Fields and Data arrays containing activity records
    Raises:
        ConnectorError: If object not found or invalid parameters
    Note:
        POST method supports advanced filter operators: =, <>, >, >=, <, <=
        No URL length limitations compared to GET method
    """
    client = AlloyClient(config)

    # Validate required parameter
    oid = params.get("oid")
    if not oid:
        raise ConnectorError("Missing required parameter: oid")

    oid = str(oid).strip()
    if not oid:
        raise ConnectorError("Object identifier (oid) cannot be empty")

    # Build POST body
    post_body = {}

    # Handle fields parameter
    fields = params.get("fields")
    if fields:
        try:
            if isinstance(fields, str):
                fields_list = [item.strip() for item in fields.split(",")]
            else:
                fields_list = fields

            if isinstance(fields_list, list):
                post_body["fields"] = fields_list
            else:
                raise ConnectorError("Fields must be a JSON array")
        except json.JSONDecodeError as e:
            raise ConnectorError(f"Invalid fields JSON format: {str(e)}")

    # Handle filters parameter
    filters = params.get("filters")
    if filters:
        try:
            if isinstance(filters, str):
                filters_list = [item.strip() for item in filters.split(",")]
            else:
                filters_list = filters

            if isinstance(filters_list, list):
                # Validate filter structure
                for f in filters_list:
                    if not isinstance(f, dict):
                        raise ConnectorError("Each filter must be an object with name, value, and operation")
                    if "name" not in f or "value" not in f or "operation" not in f:
                        raise ConnectorError("Each filter must have 'name', 'value', and 'operation' properties")
                    # Validate operation
                    valid_ops = ["=", "<>", ">", ">=", "<", "<="]
                    if f["operation"] not in valid_ops:
                        raise ConnectorError(
                            f"Invalid operation '{f['operation']}'. Must be one of: {', '.join(valid_ops)}")

                post_body["filters"] = filters_list
            else:
                raise ConnectorError("Filters must be a JSON array")
        except json.JSONDecodeError as e:
            raise ConnectorError(f"Invalid filters JSON format: {str(e)}")

    # Handle sort parameter
    sort = params.get("sort")
    if sort:
        try:
            if isinstance(sort, str):
                sort_list = [item.strip() for item in sort.split(",")]
            else:
                sort_list = sort

            if isinstance(sort_list, list):
                # Validate sort structure
                for s in sort_list:
                    if not isinstance(s, dict):
                        raise ConnectorError("Each sort must be an object with property and direction")
                    if "property" not in s or "direction" not in s:
                        raise ConnectorError("Each sort must have 'property' and 'direction' properties")
                    # Validate direction
                    if s["direction"].lower() not in ["asc", "desc"]:
                        raise ConnectorError(f"Invalid sort direction '{s['direction']}'. Must be 'asc' or 'desc'")

                post_body["sort"] = sort_list
            else:
                raise ConnectorError("Sort must be a JSON array")
        except json.JSONDecodeError as e:
            raise ConnectorError(f"Invalid sort JSON format: {str(e)}")

    # Handle simple parameters
    if params.get("limit") is not None:
        post_body["limit"] = params.get("limit")

    if params.get("offset") is not None:
        post_body["offset"] = params.get("offset")

    # Build endpoint with object identifier
    endpoint = ENDPOINTS['activities_advanced'].format(oid=oid)

    # Make API request with POST method
    result = client.make_request(
        method="POST",
        endpoint=endpoint,
        data=post_body,
        operation_name="get_object_activities_advanced"
    )

    # Validate response structure
    if not result.get("success"):
        error_text = result.get("errorText", "Unknown error")
        error_code = result.get("errorCode", 0)

        # Handle specific error messages
        if "not found" in error_text.lower():
            raise ConnectorError(f"Object '{oid}' not found in the system")
        elif "permissions" in error_text.lower() or "access" in error_text.lower():
            raise ConnectorError(f"Insufficient permissions to access activities for object '{oid}'")
        else:
            raise ConnectorError(f"API error (code {error_code}): {error_text}")

    return result


def get_classification_values(config, params):
    """
    Retrieve classification/dictionary values for Alloy Navigator objects

    Args:
        config (dict): Connector configuration
        params (dict): Operation parameters including:
            - par_objectClass (required): Object class name (e.g., Incidents, Computers)
            - par_refField (required): Reference field name (e.g., Status, Types, Priority)
            - par_fields: Comma-separated list of fields to return
            - par_sort_asc: Fields to sort ascending
            - par_sort_desc: Fields to sort descending
            - par_limit: Number of records to return
            - par_offset: Number of records to skip
            - filters: Additional filtering criteria as JSON object
    Returns:
        dict: API response with Fields and Data arrays containing classification values
    Raises:
        ConnectorError: If object class or reference field not found
    Note:
        Useful for getting dropdown values, status options, type lists, etc.
        Common reference fields: Status, Types, Priority, Category, Urgency, Impact
    """
    client = AlloyClient(config)

    # Validate required parameters
    object_class = params.get("par_objectClass")
    ref_field = params.get("par_refField")

    if not object_class:
        raise ConnectorError("Missing required parameter: par_objectClass")
    if not ref_field:
        raise ConnectorError("Missing required parameter: par_refField")

    # Trim whitespace
    object_class = str(object_class).strip()
    ref_field = str(ref_field).strip()

    if not object_class:
        raise ConnectorError("Object class (par_objectClass) cannot be empty")
    if not ref_field:
        raise ConnectorError("Reference field (par_refField) cannot be empty")

    # Build query parameters - start with required params
    query_params = {
        "par_objectClass": object_class,
        "par_refField": ref_field
    }

    # Add optional parameters if provided
    optional_params = [
        "par_fields", "par_sort_asc", "par_sort_desc",
        "par_limit", "par_offset"
    ]

    for param in optional_params:
        value = params.get(param)
        if value is not None and str(value).strip():
            query_params[param] = value

    # Add filter criteria from JSON object
    filters = params.get("filters")
    if filters:
        try:
            if isinstance(filters, str):
                filter_dict = [item.strip() for item in filters.split(",")]
            else:
                filter_dict = filters

            # Add each filter as query parameter
            for key, value in filter_dict.items():
                query_params[key] = value
        except json.JSONDecodeError as e:
            raise ConnectorError(f"Invalid filters JSON format: {str(e)}")

    # Build endpoint for Dictionary API
    endpoint = ENDPOINTS['dictionary']

    # Make API request
    result = client.make_request(
        method="GET",
        endpoint=endpoint,
        params=query_params,
        operation_name="get_classification_values"
    )

    # Validate response structure
    if not result.get("success"):
        error_text = result.get("errorText", "Unknown error")
        error_code = result.get("errorCode", 0)

        # Handle specific error messages
        if "unknown class" in error_text.lower():
            raise ConnectorError(f"Object class '{object_class}' not found in the system")
        elif "unknown" in error_text.lower() and "field" in error_text.lower():
            raise ConnectorError(f"Reference field '{ref_field}' not found for object class '{object_class}'")
        elif "permissions" in error_text.lower() or "access" in error_text.lower():
            raise ConnectorError(f"Insufficient permissions to access classification values")
        else:
            raise ConnectorError(f"API error (code {error_code}): {error_text}")

    return result


def get_classification_values_advanced(config, params):
    """
    Retrieve classification/dictionary values using POST method with advanced filtering
    Args:
        config (dict): Connector configuration
        params (dict): Operation parameters including:
            - objectClass (required): Object class name (e.g., Incidents, Computers)
            - refField (required): Reference field name (e.g., Status, Statuses, Priority)
            - fields: JSON array of field names to return
            - filters: JSON array of filter objects with name, value, operation
            - sort: JSON array of sort objects with property and direction
            - limit: Number of records to return
            - offset: Number of records to skip
    Returns:
        dict: API response with Fields and Data arrays containing classification values
    Raises:
        ConnectorError: If object class or reference field not found or invalid parameters
    Note:
        POST method supports advanced filter operators: =, <>, >, >=, <, <=
        Reference field examples: Status, Statuses, Priority, Types, Category
    """
    client = AlloyClient(config)

    # Validate required parameters
    object_class = params.get("objectClass")
    ref_field = params.get("refField")

    if not object_class:
        raise ConnectorError("Missing required parameter: objectClass")
    if not ref_field:
        raise ConnectorError("Missing required parameter: refField")

    # Trim whitespace
    object_class = str(object_class).strip()
    ref_field = str(ref_field).strip()

    if not object_class:
        raise ConnectorError("Object class (objectClass) cannot be empty")
    if not ref_field:
        raise ConnectorError("Reference field (refField) cannot be empty")

    # Build POST body - include required params in body as per documentation
    post_body = {
        "objectClass": object_class,
        "refField": ref_field
    }

    # Handle fields parameter
    fields = params.get("fields")
    if fields:
        try:
            if isinstance(fields, str):
                fields_list = [item.strip() for item in fields.split(",")]
            else:
                fields_list = fields

            if isinstance(fields_list, list):
                post_body["fields"] = fields_list
            else:
                raise ConnectorError("Fields must be a JSON array")
        except json.JSONDecodeError as e:
            raise ConnectorError(f"Invalid fields JSON format: {str(e)}")

    # Handle filters parameter
    filters = params.get("filters")
    if filters:
        try:
            if isinstance(filters, str):
                filters_list = [item.strip() for item in fields.split(",")]
            else:
                filters_list = filters

            if isinstance(filters_list, list):
                # Validate filter structure
                for f in filters_list:
                    if not isinstance(f, dict):
                        raise ConnectorError("Each filter must be an object with name, value, and operation")
                    if "name" not in f or "value" not in f or "operation" not in f:
                        raise ConnectorError("Each filter must have 'name', 'value', and 'operation' properties")
                    # Validate operation
                    valid_ops = ["=", "<>", ">", ">=", "<", "<="]
                    if f["operation"] not in valid_ops:
                        raise ConnectorError(
                            f"Invalid operation '{f['operation']}'. Must be one of: {', '.join(valid_ops)}")

                post_body["filters"] = filters_list
            else:
                raise ConnectorError("Filters must be a JSON array")
        except json.JSONDecodeError as e:
            raise ConnectorError(f"Invalid filters JSON format: {str(e)}")

    # Handle sort parameter
    sort = params.get("sort")
    if sort:
        try:
            if isinstance(sort, str):
                sort_list = [item.strip() for item in sort.split(",")]
            else:
                sort_list = sort

            if isinstance(sort_list, list):
                # Validate sort structure
                for s in sort_list:
                    if not isinstance(s, dict):
                        raise ConnectorError("Each sort must be an object with property and direction")
                    if "property" not in s or "direction" not in s:
                        raise ConnectorError("Each sort must have 'property' and 'direction' properties")
                    # Validate direction
                    if s["direction"].lower() not in ["asc", "desc"]:
                        raise ConnectorError(f"Invalid sort direction '{s['direction']}'. Must be 'asc' or 'desc'")

                post_body["sort"] = sort_list
            else:
                raise ConnectorError("Sort must be a JSON array")
        except json.JSONDecodeError as e:
            raise ConnectorError(f"Invalid sort JSON format: {str(e)}")

    # Handle simple parameters - use default 0 if not provided
    if params.get("limit") is not None:
        post_body["limit"] = params.get("limit")

    if params.get("offset") is not None:
        post_body["offset"] = params.get("offset")

    # Build endpoint for Dictionary API - no path parameters
    endpoint = ENDPOINTS['dictionary_advanced']

    # Make API request with POST method
    result = client.make_request(
        method="POST",
        endpoint=endpoint,
        data=post_body,
        operation_name="get_classification_values_advanced"
    )

    # Validate response structure
    if not result.get("success"):
        error_text = result.get("errorText", "Unknown error")
        error_code = result.get("errorCode", 0)

        # Handle specific error messages - adjust based on actual API responses
        if "unknown class" in error_text.lower() or "Requested object is of unknown class" in error_text:
            raise ConnectorError(f"Object class '{object_class}' not found in the system")
        elif "unknown" in error_text.lower() and "field" in error_text.lower():
            raise ConnectorError(
                f"Reference field '{ref_field}' not found for object class '{object_class}'. Common field names: Status, Priority, Type, Category")
        elif "permissions" in error_text.lower() or "access" in error_text.lower() or "Authorization has been denied" in error_text:
            raise ConnectorError(f"Insufficient permissions to access classification values")
        else:
            raise ConnectorError(f"API error (code {error_code}): {error_text}")

    return result


def create_object(config, params):
    """
    Create a new Alloy Navigator object record via workflow Create Action
    Args:
        config (dict): Connector configuration
        params (dict): Operation parameters including:
            - action_id (required): The Create Action ID
            - fields (required): JSON object with field names and values
    Returns:
        dict: API response with ObjectID and ObjectOID of created object
    Raises:
        ConnectorError: If action not found, unauthorized, or validation fails
    Note:
        - Does not support Service Requests (use Submit Request action instead)
        - For reference fields: use object identifier (e.g., "PN000017") or name
        - For classification fields: use display value (e.g., "Immediate")
        - For boolean fields: use true/false or 1/0
        - Field names should use display labels
    """
    client = AlloyClient(config)

    # Validate required parameters
    action_id = params.get("action_id")

    if not action_id:
        raise ConnectorError("Missing required parameter: action_id")

    # Initialize fields_dict
    fields_dict = {}

    # Get additional fields from JSON if provided
    fields = params.get("fields")
    if fields:
        # Parse fields if provided as JSON string
        if isinstance(fields, str):
            try:
                fields_dict = [item.strip() for item in fields.split(",")]
            except json.JSONDecodeError as e:
                raise ConnectorError(f"Invalid fields JSON format: {str(e)}")
        else:
            fields_dict = fields

    # Validate fields is a dictionary
    if not isinstance(fields_dict, dict):
        raise ConnectorError("fields must be a JSON object with field name-value pairs")

    # Add individual fields to fields_dict
    if params.get("summary"):
        fields_dict["Summary"] = params.get("summary")

    if params.get("description"):
        fields_dict["Description"] = params.get("description")

    if params.get("category"):
        fields_dict["Category"] = params.get("category")

    if params.get("requester"):
        fields_dict["Requester"] = params.get("requester")

    if params.get("urgency"):
        fields_dict["Urgency"] = params.get("urgency")

    if params.get("impact"):
        fields_dict["Impact"] = params.get("impact")

    # Check if at least one field is provided
    if not fields_dict:
        raise ConnectorError("At least one field must be specified (individual fields or additional fields JSON)")

    # Validate action_id is numeric
    try:
        action_id = int(action_id)
    except (ValueError, TypeError):
        raise ConnectorError("action_id must be a valid integer")

    # Build POST body
    post_body = {
        "ActionId": action_id,
        "Fields": fields_dict
    }

    # Build endpoint
    endpoint = ENDPOINTS['create_object']

    # Make API request with POST method
    result = client.make_request(
        method="POST",
        endpoint=endpoint,
        data=post_body,
        operation_name="create_object"
    )

    # Validate response structure
    if not result.get("success"):
        error_text = result.get("errorText", "Unknown error")
        error_code = result.get("errorCode", 0)

        # Handle specific error messages
        if "Authorization has been denied" in error_text:
            raise ConnectorError("Authorization failed - token may have expired")
        elif "action's condition is not satisfied" in error_text or "not authorized" in error_text.lower():
            raise ConnectorError(f"User is not authorized to execute Create Action ID {action_id}")
        elif "action is not available" in error_text.lower() or "not found" in error_text.lower():
            raise ConnectorError(
                f"Create Action ID {action_id} not found. Check Settings App: Workflow > Actions > Create Actions")
        elif "Field" in error_text and "unknown" in error_text.lower():
            raise ConnectorError(f"API error: {error_text}. Check field names match display labels")
        else:
            raise ConnectorError(f"API error (code {error_code}): {error_text}")

    # Check if object creation succeeded
    response_obj = result.get("responseObject", {})
    if not response_obj.get("Succeed", False):
        raise ConnectorError("Object creation failed - Succeed flag is false")

    return result


def check_step_action_availability(config, params):
    """
    Check if a workflow Step Action is available for a specific Alloy Navigator object
    Args:
        config (dict): Connector configuration
        params (dict): Operation parameters including:
            - oid (required): Object identifier (e.g., T000027, V000006)
            - action_id (required): The Step Action ID to check
    Returns:
        dict: API response with Result (true/false) indicating action availability
    Raises:
        ConnectorError: If object not found or invalid parameters
    Note:
        - Action availability depends on object type, status, security roles, and other criteria
        - Cannot be used for Software Catalog and Stock Room objects
        - Returns Result: true if action is available, false if not available
    """
    client = AlloyClient(config)

    # Validate required parameters
    oid = params.get("oid")
    action_id = params.get("action_id")

    if not oid:
        raise ConnectorError("Missing required parameter: oid")

    if not action_id:
        raise ConnectorError("Missing required parameter: action_id")

    # Trim whitespace from OID
    oid = str(oid).strip()
    if not oid:
        raise ConnectorError("Object identifier (oid) cannot be empty")

    # Validate action_id is numeric
    try:
        action_id = int(action_id)
    except (ValueError, TypeError):
        raise ConnectorError("action_id must be a valid integer")

    # Build endpoint with object identifier, action ID, and check suffix
    endpoint = ENDPOINTS['step_action_check'].format(oid=oid, action_id=action_id)

    # Make API request with GET method
    result = client.make_request(
        method="GET",
        endpoint=endpoint,
        operation_name="check_step_action_availability"
    )

    # Validate response structure
    if not result.get("success"):
        error_text = result.get("errorText", "Unknown error")
        error_code = result.get("errorCode", 0)

        # Handle specific error messages
        if "Authorization has been denied" in error_text:
            raise ConnectorError("Authorization failed - token may have expired")
        elif "not found" in error_text.lower():
            if "Object" in error_text:
                raise ConnectorError(f"Object '{oid}' not found in the system")
            elif "action" in error_text.lower():
                raise ConnectorError(f"Step Action ID {action_id} not found")
            else:
                raise ConnectorError(f"API error: {error_text}")
        elif "not have enough permissions" in error_text.lower():
            raise ConnectorError(f"User is not authorized to access object '{oid}'")
        else:
            raise ConnectorError(f"API error (code {error_code}): {error_text}")

    # Add availability interpretation to response for easier consumption
    response_obj = result.get("responseObject", {})
    is_available = response_obj.get("Result", False)

    result["action_available"] = is_available
    result["availability_message"] = (
        f"Step Action {action_id} is available for object {oid}" if is_available
        else f"Step Action {action_id} is not available for object {oid}"
    )

    return result


def run_step_action(config, params):
    """
    Run a workflow Step Action on an Alloy Navigator object
    Args:
        config (dict): Connector configuration
        params (dict): Operation parameters including:
            - oid (required): Object identifier (e.g., T000027, V000006)
            - action_id (required): The Step Action ID
            - fields (required): JSON object with field names and values to update
    Returns:
        dict: API response with ObjectID and ObjectOID of updated object
    Raises:
        ConnectorError: If object/action not found, unauthorized, or validation fails
    Note:
        - Cannot be used for Software Catalog and Stock Room objects
        - For reference fields: use object identifier (e.g., "PN000017") or name
        - For classification fields: use display value (e.g., "Immediate")
        - For boolean fields: use true/false or 1/0
        - Field names should use display labels
    """
    client = AlloyClient(config)

    # Validate required parameters
    oid = params.get("oid")
    action_id = params.get("action_id")
    fields = params.get("fields")

    if not oid:
        raise ConnectorError("Missing required parameter: oid")

    if not action_id:
        raise ConnectorError("Missing required parameter: action_id")

    # if not fields:
    #     raise ConnectorError("Missing required parameter: fields")

    # Trim whitespace from OID
    oid = str(oid).strip()
    if not oid:
        raise ConnectorError("Object identifier (oid) cannot be empty")

    # Validate action_id is numeric
    try:
        action_id = int(action_id)
    except (ValueError, TypeError):
        raise ConnectorError("action_id must be a valid integer")

    # Initialize fields_dict
    fields_dict = {}

    # Get additional fields from JSON if provided
    fields = params.get("fields")
    if fields:
        # Parse fields if provided as JSON string
        if isinstance(fields, str):
            try:
                fields_dict = [item.strip() for item in fields.split(",")]
            except json.JSONDecodeError as e:
                raise ConnectorError(f"Invalid fields JSON format: {str(e)}")
        else:
            fields_dict = fields

        # Validate fields is a dictionary
        if not isinstance(fields_dict, dict):
            raise ConnectorError("fields must be a JSON object with field name-value pairs")

    # Add individual fields to fields_dict
    if params.get("summary"):
        fields_dict["Summary"] = params.get("summary")

    if params.get("description"):
        fields_dict["Description"] = params.get("description")

    if params.get("category"):
        fields_dict["Category"] = params.get("category")

    if params.get("requester"):
        fields_dict["Requester"] = params.get("requester")

    if params.get("urgency"):
        fields_dict["Urgency"] = params.get("urgency")

    if params.get("impact"):
        fields_dict["Impact"] = params.get("impact")

    # Check if at least one field is provided
    if not fields_dict:
        raise ConnectorError("At least one field must be specified (individual fields or additional fields JSON)")

    # Build endpoint with object identifier and action ID
    endpoint = ENDPOINTS['step_action'].format(oid=oid, action_id=action_id)

    # POST body contains only the fields (not wrapped in another object)
    post_body = fields_dict

    # Make API request with POST method
    result = client.make_request(
        method="POST",
        endpoint=endpoint,
        data=post_body,
        operation_name="run_step_action"
    )

    # Validate response structure
    if not result.get("success"):
        error_text = result.get("errorText", "Unknown error")
        error_code = result.get("errorCode", 0)

        # Handle specific error messages
        if "Authorization has been denied" in error_text:
            raise ConnectorError("Authorization failed - token may have expired")
        elif "not have enough permissions" in error_text.lower():
            raise ConnectorError(f"User is not authorized to access object '{oid}'")
        elif "action's condition is not satisfied" in error_text or "not authorized to use" in error_text.lower():
            raise ConnectorError(f"User is not authorized to execute Step Action ID {action_id} on object '{oid}'")
        elif "not found" in error_text.lower():
            if "Object" in error_text:
                raise ConnectorError(f"Object '{oid}' not found in the system")
            elif "action" in error_text.lower():
                raise ConnectorError(
                    f"Step Action ID {action_id} not found. Check Settings App: Workflow > Actions > Step Actions")
            else:
                raise ConnectorError(f"API error: {error_text}")
        elif "Field" in error_text and "unknown" in error_text.lower():
            raise ConnectorError(f"API error: {error_text}. Check field names match display labels")
        else:
            raise ConnectorError(f"API error (code {error_code}): {error_text}")

    # Check if action execution succeeded
    response_obj = result.get("responseObject", {})
    if not response_obj.get("Succeed", False):
        raise ConnectorError("Step Action execution failed - Succeed flag is false")

    return result


def list_object_attachments(config, params):
    """
    Retrieve a list of attachments for a specific Alloy Navigator object
    Args:
        config (dict): Connector configuration
        params (dict): Operation parameters including:
            - oid (required): Object identifier (e.g., T000027, GUID)
            - par_fields: Comma-separated list of attachment fields
            - par_sort_asc: Fields to sort ascending
            - par_sort_desc: Fields to sort descending
            - par_limit: Number of records to return
            - par_offset: Number of records to skip
            - filters: Additional filtering criteria as JSON object
    Returns:
        dict: API response with Fields and Data arrays containing attachment records
    Raises:
        ConnectorError: If object not found or user lacks permissions
    Note:
        - Requires Modify access permission on the object
        - Returns attachment metadata including ID, Name, Type, Created_Date
    """
    client = AlloyClient(config)

    # Validate required parameter
    oid = params.get("oid")
    if not oid:
        raise ConnectorError("Missing required parameter: oid")

    # Trim whitespace
    oid = str(oid).strip()
    if not oid:
        raise ConnectorError("Object identifier (oid) cannot be empty")

    # Build query parameters
    query_params = {}

    # Add optional parameters if provided
    optional_params = [
        "par_fields", "par_sort_asc", "par_sort_desc",
        "par_limit", "par_offset"
    ]

    for param in optional_params:
        value = params.get(param)
        if value is not None and str(value).strip():
            query_params[param] = value

    # Add filter criteria from JSON object
    filters = params.get("filters")
    if filters:
        try:
            if isinstance(filters, str):
                filter_dict = [item.strip() for item in filters.split(",")]
            else:
                filter_dict = filters

            # Add each filter as query parameter
            for key, value in filter_dict.items():
                query_params[key] = value
        except json.JSONDecodeError as e:
            raise ConnectorError(f"Invalid filters JSON format: {str(e)}")

    # Build endpoint
    endpoint = ENDPOINTS['list_attachments'].format(oid=oid)

    # Make API request
    result = client.make_request(
        method="GET",
        endpoint=endpoint,
        params=query_params,
        operation_name="list_object_attachments"
    )

    # Validate response structure
    if not result.get("success"):
        error_text = result.get("errorText", "Unknown error")
        error_code = result.get("errorCode", 0)

        # Handle specific error messages
        if "not found" in error_text.lower():
            raise ConnectorError(f"Object '{oid}' not found in the system")
        elif "permissions" in error_text.lower() or "access" in error_text.lower():
            raise ConnectorError(f"Insufficient permissions to access attachments for object '{oid}'")
        else:
            raise ConnectorError(f"API error (code {error_code}): {error_text}")

    return result


def get_attachment_content(config, params):
    """
    Get the contents of a specific object attachment (base64 encoded)
    Args:
        config (dict): Connector configuration
        params (dict): Operation parameters including:
            - oid (required): Object identifier (e.g., T000027, GUID)
            - attachment_id (required): Attachment ID (GUID)
    Returns:
        dict: API response with base64 encoded Data, FileName, Description, Size
    Raises:
        ConnectorError: If object/attachment not found or user lacks permissions
    Note:
        - Requires Modify access permission on the object
        - Returns attachment contents as base64 encoded string
    """
    client = AlloyClient(config)

    # Validate required parameters
    oid = params.get("oid")
    attachment_id = params.get("attachment_id")

    if not oid:
        raise ConnectorError("Missing required parameter: oid")
    if not attachment_id:
        raise ConnectorError("Missing required parameter: attachment_id")

    # Trim whitespace
    oid = str(oid).strip()
    attachment_id = str(attachment_id).strip()

    if not oid:
        raise ConnectorError("Object identifier (oid) cannot be empty")
    if not attachment_id:
        raise ConnectorError("Attachment ID (attachment_id) cannot be empty")

    # Build endpoint
    endpoint = ENDPOINTS['get_attachment_content'].format(oid=oid, attachment_id=attachment_id)

    # Make API request
    result = client.make_request(
        method="GET",
        endpoint=endpoint,
        operation_name="get_attachment_content"
    )

    # Validate response structure
    if not result.get("success"):
        error_text = result.get("errorText", "Unknown error")
        error_code = result.get("errorCode", 0)

        # Handle specific error messages
        if "not found" in error_text.lower():
            raise ConnectorError(f"Object '{oid}' or attachment '{attachment_id}' not found")
        elif "permissions" in error_text.lower() or "access" in error_text.lower():
            raise ConnectorError(f"Insufficient permissions to access attachment for object '{oid}'")
        else:
            raise ConnectorError(f"API error (code {error_code}): {error_text}")

    return result


def download_attachment(config, params):
    """
    Download a specific object attachment and upload to FortiSOAR attachment module
    Args:
        config (dict): Connector configuration
        params (dict): Operation parameters including:
            - oid (required): Object identifier (e.g., T000027, GUID)
            - attachment_id (required): Attachment ID (GUID)
            - attachment_name (optional): Custom name for FortiSOAR attachment
            - attachment_description (optional): Custom description for FortiSOAR attachment
            - skip_fortisoar_upload (optional): If True, only download without uploading to FortiSOAR
    Returns:
        dict: Combined response with download info and FortiSOAR attachment details
    Raises:
        ConnectorError: If object/attachment not found or user lacks permissions
    Note:
        - Requires Modify access permission on the object
        - Automatically uploads to FortiSOAR attachment module unless skip_fortisoar_upload=True
        - Returns both download response and FortiSOAR attachment record
    """

    client = AlloyClient(config)

    # Validate required parameters
    oid = params.get("oid")
    attachment_id = params.get("attachment_id")

    if not oid:
        raise ConnectorError("Missing required parameter: oid")
    if not attachment_id:
        raise ConnectorError("Missing required parameter: attachment_id")

    # Trim whitespace
    oid = str(oid).strip()
    attachment_id = str(attachment_id).strip()

    if not oid:
        raise ConnectorError("Object identifier (oid) cannot be empty")
    if not attachment_id:
        raise ConnectorError("Attachment ID (attachment_id) cannot be empty")

    # Get optional FortiSOAR parameters
    attachment_name = params.get('attachment_name', '')
    attachment_description = params.get('attachment_description', '')
    skip_fortisoar_upload = params.get('skip_fortisoar_upload', False)

    # Build endpoint
    endpoint = ENDPOINTS['download_attachment'].format(oid=oid, attachment_id=attachment_id)

    # Build full URL
    url = f"{client.server_url}{endpoint}"
    headers = client.auth.get_auth_header()

    try:
        # Make direct request to handle binary response
        logger.info(f"Downloading attachment {attachment_id} from object {oid}")
        response = requests.get(
            url,
            headers=headers,
            verify=client.verify_ssl,
            timeout=60,
            stream=True
        )

        if response.status_code == 200:
            # Extract filename from custom header or Content-Disposition
            file_name = response.headers.get('attachment-file-name', 'downloaded_file')
            content_type = response.headers.get('Content-Type', 'application/octet-stream')
            content_length = response.headers.get('Content-Length', 0)

            # Get binary content
            binary_data = response.content

            # Encode to base64 for the response
            encoded_data = base64.b64encode(binary_data).decode('utf-8')

            # Build download response
            download_response = {
                "success": True,
                "file_name": file_name,
                "content_type": content_type,
                "size": int(content_length) if content_length else len(binary_data),
                "data": encoded_data,
                "message": f"Successfully downloaded attachment: {file_name}"
            }

            logger.info(f"Downloaded {file_name} ({len(binary_data)} bytes)")

            # Upload to FortiSOAR if not skipped
            if not skip_fortisoar_upload:
                try:

                    # Clean filename
                    clean_file_name = urllib.parse.unquote(file_name)
                    clean_file_name = clean_file_name.replace(' ', '_')

                    logger.info(f"Uploading to FortiSOAR: {clean_file_name}")

                    # Upload file to FortiSOAR files module
                    file = make_file_upload_request(clean_file_name, binary_data, content_type)
                    file_id = file['@id']

                    logger.info(f"File uploaded to FortiSOAR: {file_id}")

                    # Create attachment record in FortiSOAR
                    time = arrow.utcnow()
                    attachment_name_final = attachment_name or f'Alloy_Attachment_{time.format("YYYY-MM-DD_HH-mm-ss")}'
                    attachment_description_final = attachment_description or f"Downloaded from Alloy Navigator: {clean_file_name} (Object: {oid})"

                    attachment_result = make_request(
                        '/api/3/attachments',
                        'POST',
                        {
                            'name': attachment_name_final,
                            'file': file_id,
                            'description': attachment_description_final
                        }
                    )

                    logger.info(f"Attachment created in FortiSOAR: {attachment_result.get('@id')}")

                    # Return combined response
                    return {
                        "success": True,
                        "message": f"Successfully downloaded and uploaded to FortiSOAR: {clean_file_name}",
                        "download": download_response,
                        "fortisoar_upload": {
                            "file_name": clean_file_name,
                            "content_type": content_type,
                            "size": len(binary_data),
                            "fortisoar_file_iri": file_id,
                            "fortisoar_attachment_iri": attachment_result.get('@id'),
                            "fortisoar_attachment_id": attachment_result.get('id'),
                            "attachment_record": attachment_result
                        }
                    }

                except ImportError:
                    logger.error("FortiSOAR integration modules not available")
                    download_response["fortisoar_upload_error"] = "FortiSOAR integration modules not available"
                    download_response["fortisoar_upload_success"] = False
                    return download_response
                except Exception as upload_error:
                    logger.error(f"Failed to upload to FortiSOAR: {upload_error}")
                    download_response["fortisoar_upload_error"] = str(upload_error)
                    download_response["fortisoar_upload_success"] = False
                    return download_response
            else:
                logger.info("Skipped FortiSOAR upload as requested")
                return download_response

        elif response.status_code == 404:
            raise ConnectorError(f"Object '{oid}' or attachment '{attachment_id}' not found")
        elif response.status_code == 401:
            raise ConnectorError("Authentication failed - token may have expired")
        elif response.status_code == 403:
            raise ConnectorError(f"Insufficient permissions to download attachment")
        else:
            # Try to parse error response
            try:
                error_data = response.json()
                error_text = error_data.get("errorText", "Unknown error")
                raise ConnectorError(f"Download failed: {error_text}")
            except:
                raise ConnectorError(f"Download failed: HTTP {response.status_code}")

    except requests.exceptions.RequestException as e:
        raise ConnectorError(f"Request failed: {str(e)}")


def add_attachments(config, params):
    """
    Add file attachments or links from FortiSOAR to a specific Alloy Navigator object
    Args:
        config (dict): Connector configuration
        params (dict): Operation parameters including:
            - oid (required): Object identifier (e.g., T000027, GUID)
            - path (required): Type selection - "Attachment ID" or "File IRI"
            - value (required): The actual IRI value based on path selection
    Returns:
        dict: API response confirming attachment addition
    Raises:
        ConnectorError: If object not found, user lacks permissions, or invalid data
    Note:
        - Requires Modify access permission on the object
        - Retrieves file from FortiSOAR and uploads to Alloy Navigator
    """

    client = AlloyClient(config)

    # Validate required parameters
    oid = params.get("oid")
    path = params.get("path")
    value = params.get("value")

    if not oid:
        raise ConnectorError("Missing required parameter: oid")
    if not value:
        raise ConnectorError("Missing required parameter: value (File or Attachment IRI)")

    # Trim whitespace
    oid = str(oid).strip()
    value = str(value).strip()

    if not oid:
        raise ConnectorError("Object identifier (oid) cannot be empty")
    if not value:
        raise ConnectorError("File or Attachment IRI (value) cannot be empty")

    try:
        logger.info(f"Downloading file from FortiSOAR: {value}")

        # Handle both attachment IRI and file IRI
        if value.startswith('/api/3/attachments/'):
            # Get file IRI from attachment record
            attachment_data = make_request(value, 'GET')
            file_iri = attachment_data['file']['@id']
            logger.info(f"Resolved attachment IRI to file IRI: {file_iri}")
        else:
            file_iri = value

        # Download file from FortiSOAR - returns a dictionary
        file_download_response = download_file_from_cyops(file_iri)
        file_name = file_download_response['filename']
        file_path = join('/tmp', file_download_response['cyops_file_path'])

        logger.info(f"Retrieved file: {file_name} from path: {file_path}")

        # Determine mime type
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = 'application/octet-stream'

        # Read file and encode to base64
        with open(file_path, 'rb') as f:
            file_bytes = f.read()
            encoded_data = base64.b64encode(file_bytes).decode('utf-8')

        logger.info(f"Encoded file: {len(file_bytes)} bytes, type: {mime_type}")

        # Build attachment object
        attachment_obj = {
            "FileName": file_name,
            "Description": f"Uploaded from FortiSOAR: {file_name}",
            "Data": encoded_data,
            "IsLink": False
        }

        # Build endpoint
        endpoint = ENDPOINTS['add_attachments'].format(oid=oid)

        # Make API request with PUT method
        result = client.make_request(
            method="PUT",
            endpoint=endpoint,
            data=attachment_obj,
            operation_name="add_attachments"
        )

        # Validate response structure
        if not result.get("success"):
            error_text = result.get("errorText", "Unknown error")
            error_code = result.get("errorCode", 0)

            # Handle specific error messages
            if "not found" in error_text.lower():
                raise ConnectorError(f"Object '{oid}' not found")
            elif "permissions" in error_text.lower() or "access" in error_text.lower():
                raise ConnectorError(f"Insufficient permissions to add attachments to object '{oid}'")
            else:
                raise ConnectorError(f"API error (code {error_code}): {error_text}")

        # Add success message
        result["message"] = f"Successfully uploaded attachment '{file_name}' to object {oid}"
        result["uploaded_file"] = {
            "file_name": file_name,
            "file_size": len(file_bytes),
            "mime_type": mime_type
        }

        return result

    except ImportError as e:
        raise ConnectorError(f"FortiSOAR integration module not available: {str(e)}")
    except KeyError as e:
        raise ConnectorError(f"Invalid file download response - missing key: {str(e)}")
    except FileNotFoundError as e:
        raise ConnectorError(f"Downloaded file not found at expected path: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to upload attachment: {str(e)}")
        raise ConnectorError(f"Failed to upload attachment: {str(e)}")


def remove_attachment(config, params):
    """
    Remove a specific attachment from an object
    Args:
        config (dict): Connector configuration
        params (dict): Operation parameters including:
            - oid (required): Object identifier (e.g., T000027, GUID)
            - attachment_id (required): Attachment ID (GUID)
    Returns:
        dict: API response confirming attachment removal
    Raises:
        ConnectorError: If object/attachment not found or user lacks permissions
    Note:
        - Requires Modify access permission on the object
        - Permanently removes the attachment
    """
    client = AlloyClient(config)

    # Validate required parameters
    oid = params.get("oid")
    attachment_id = params.get("attachment_id")

    if not oid:
        raise ConnectorError("Missing required parameter: oid")
    if not attachment_id:
        raise ConnectorError("Missing required parameter: attachment_id")

    # Trim whitespace
    oid = str(oid).strip()
    attachment_id = str(attachment_id).strip()

    if not oid:
        raise ConnectorError("Object identifier (oid) cannot be empty")
    if not attachment_id:
        raise ConnectorError("Attachment ID (attachment_id) cannot be empty")

    # Build endpoint
    endpoint = ENDPOINTS['remove_attachment'].format(oid=oid, attachment_id=attachment_id)

    # Make API request with DELETE method
    result = client.make_request(
        method="DELETE",
        endpoint=endpoint,
        operation_name="remove_attachment"
    )

    # Validate response structure
    if not result.get("success"):
        error_text = result.get("errorText", "Unknown error")
        error_code = result.get("errorCode", 0)

        # Handle specific error messages
        if "not found" in error_text.lower():
            raise ConnectorError(f"Object '{oid}' or attachment '{attachment_id}' not found")
        elif "permissions" in error_text.lower() or "access" in error_text.lower():
            raise ConnectorError(f"Insufficient permissions to remove attachment from object '{oid}'")
        else:
            raise ConnectorError(f"API error (code {error_code}): {error_text}")

    # Add success message
    result["message"] = f"Successfully removed attachment {attachment_id} from object {oid}"

    return result


def update_attachment_description(config, params):
    """
    Update the description of a specific attachment
    Args:
        config (dict): Connector configuration
        params (dict): Operation parameters including:
            - oid (required): Object identifier (e.g., T000027, GUID)
            - attachment_id (required): Attachment ID (GUID)
            - description (required): New description text
    Returns:
        dict: API response confirming description update
    Raises:
        ConnectorError: If object/attachment not found or user lacks permissions
    Note:
        - Requires Modify access permission on the object
        - Only modification supported for attachments is description update
    """
    client = AlloyClient(config)

    # Validate required parameters
    oid = params.get("oid")
    attachment_id = params.get("attachment_id")
    description = params.get("description")

    if not oid:
        raise ConnectorError("Missing required parameter: oid")
    if not attachment_id:
        raise ConnectorError("Missing required parameter: attachment_id")
    if description is None:
        raise ConnectorError("Missing required parameter: description")

    # Trim whitespace from identifiers
    oid = str(oid).strip()
    attachment_id = str(attachment_id).strip()

    if not oid:
        raise ConnectorError("Object identifier (oid) cannot be empty")
    if not attachment_id:
        raise ConnectorError("Attachment ID (attachment_id) cannot be empty")

    # Description can be empty string (to clear it)
    description = str(description)

    # Build endpoint
    endpoint = ENDPOINTS['update_attachment_description'].format(oid=oid, attachment_id=attachment_id)

    # POST body with new description
    post_body = {
        "Description": description
    }

    # Make API request with PATCH method
    result = client.make_request(
        method="PATCH",
        endpoint=endpoint,
        data=post_body,
        operation_name="update_attachment_description"
    )

    # Validate response structure
    if not result.get("success"):
        error_text = result.get("errorText", "Unknown error")
        error_code = result.get("errorCode", 0)

        # Handle specific error messages
        if "not found" in error_text.lower():
            raise ConnectorError(f"Object '{oid}' or attachment '{attachment_id}' not found")
        elif "permissions" in error_text.lower() or "access" in error_text.lower():
            raise ConnectorError(f"Insufficient permissions to update attachment for object '{oid}'")
        else:
            raise ConnectorError(f"API error (code {error_code}): {error_text}")

    # Add success message
    result["message"] = f"Successfully updated description for attachment {attachment_id}"

    return result


def _parse_user_items(items):
    """Parse Items array into structured user info"""
    fields = {item["name"]: item["value"] for item in items if "name" in item and "value" in item}

    first_name = fields.get("First_Name", "")
    last_name = fields.get("Last_Name", "")
    full_name = f"{first_name} {last_name}".strip() if first_name or last_name else ""

    return {
        "id": fields.get("ID", ""),
        "first_name": first_name,
        "last_name": last_name,
        "full_name": full_name,
        "organization": fields.get("Organization", ""),
        "is_technician": fields.get("Technician", ""),
        "available_now": fields.get("Available_Now", ""),
        "address": fields.get("Address", ""),
        "gender": fields.get("Gender", "")
    }


# Operations dictionary mapping operation names to functions
operations = {
    "get_current_user_profile": get_current_user_profile,
    "get_objects_advanced": get_objects_advanced,
    "get_objects": get_objects,
    "get_object_by_id": get_object_by_id,
    "get_object_activities": get_object_activities,
    "get_object_activities_advanced": get_object_activities_advanced,
    "get_classification_values": get_classification_values,
    "get_classification_values_advanced": get_classification_values_advanced,
    "create_object": create_object,
    "run_step_action": run_step_action,
    "check_step_action_availability": check_step_action_availability,
    "list_object_attachments": list_object_attachments,
    "get_attachment_content": get_attachment_content,
    "download_attachment": download_attachment,
    "add_attachments": add_attachments,
    "remove_attachment": remove_attachment,
    "update_attachment_description": update_attachment_description
}
