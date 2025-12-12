"""
Copyright start
MIT License
Copyright (c) 2025 Fortinet Inc
Copyright end
"""

from connectors.core.connector import Connector
from connectors.core.connector import get_logger, ConnectorError
from .operations import operations, check_health
from .constants import LOGGER_NAME

logger = get_logger(LOGGER_NAME)


class Alloy(Connector):
    def execute(self, config, operation, params, **kwargs):
        """
        Execute the specified operation with given configuration and parameters
        Args:
            config (dict): Connector configuration including server URL, username, password
            operation (str): Name of the operation to execute
            params (dict): Parameters for the operation
            **kwargs: Additional keyword arguments
        Returns:
            dict: Operation result
        Raises:
            ConnectorError: If operation fails or is unsupported
        """
        try:
            # Add connector metadata to config for logging and tracking
            config['connector_info'] = {
                "connector_name": self._info_json.get('name'),
                "connector_version": self._info_json.get('version')
            }

            # Log operation execution for debugging
            logger.info(f"Executing operation: {operation}")

            # Get the operation function from operations dictionary
            op_function = operations.get(operation)
            if not op_function:
                available_operations = list(operations.keys())
                logger.error(
                    f"Unsupported operation '{operation}'. Available operations: {available_operations}"
                )
                raise ConnectorError(
                    f"Unsupported operation: {operation}. "
                    f"Available operations: {', '.join(available_operations)}"
                )

            # Execute the operation
            result = op_function(config, params)
            logger.info(f"Operation '{operation}' executed successfully")
            return result

        except ConnectorError:
            # Re-raise ConnectorError as-is to preserve specific error messages
            raise
        except Exception as err:
            # Log unexpected errors with full details
            logger.error(
                f"Unexpected exception in execute() for operation '{operation}': {str(err)}",
                exc_info=True
            )
            raise ConnectorError(f"Operation '{operation}' failed: {str(err)}")

    def check_health(self, config):
        """
        Perform health check to verify connector configuration and API connectivity
        Args:
            config (dict): Connector configuration including server URL, username, password
        Returns:
            dict: Health check result with status and details
        Raises:
            ConnectorError: If health check fails
        """
        try:
            # Add connector metadata to config
            config['connector_info'] = {
                "connector_name": self._info_json.get('name'),
                "connector_version": self._info_json.get('version')
            }

            logger.info("Starting health check for Alloy Navigator Express connector")

            # Perform the health check
            result = check_health(config)
            logger.info("Health check completed successfully")
            return result

        except ConnectorError:
            # Re-raise ConnectorError as-is to preserve specific error messages
            logger.error("Health check failed with ConnectorError")
            raise
        except Exception as err:
            # Log unexpected errors with full details
            logger.error(
                f"Unexpected exception in check_health(): {str(err)}",
                exc_info=True
            )
            raise ConnectorError(
                f"Health check failed due to unexpected error: {str(err)}"
            )

    def __str__(self):
        """String representation of the connector"""
        return f"Alloy Navigator Express Connector v{self._info_json.get('version', 'unknown')}"

    def __repr__(self):
        """Detailed string representation for debugging"""
        return (
            f"Alloy(name='{self._info_json.get('name')}', "
            f"version='{self._info_json.get('version')}', "
            f"operations={list(operations.keys())})"
        )