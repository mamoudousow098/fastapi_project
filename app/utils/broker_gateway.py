"""
Broker Gateway for external connector calls
Equivalent to Java BrokerGateway class
"""
import logging
from typing import Optional

from app.models.parameter import Parameter
from app.services.parameter import ParameterService
from app.utils.http_utils import HTTPUtils, HTTPResponse

logger = logging.getLogger(__name__)


class BrokerGateway:
    """
    Gateway for making calls to external connectors
    Equivalent to Java BrokerGateway class
    """

    # Class-level cache for credentials
    _connector_login: Optional[str] = None
    _connector_password: Optional[str] = None

    def __init__(self, parameter_service: ParameterService):
        self.parameter_service = parameter_service
        self.http_utils = HTTPUtils(parameter_service)

    async def post_to_connector(
            self,
            url: Parameter,
            body: str,
            tag: str
    ) -> Optional[HTTPResponse]:
        """
        Make a POST request to the connector

        Args:
            url: Parameter containing the URL and proxy flag
            body: Request body (JSON string)
            tag: Tag for logging

        Returns:
            HTTPResponse or None if error
        """
        try:
            # Get credentials and build auth header
            login = await self.get_connector_login()
            password = await self.get_connector_password()
            basic_auth = f"Basic {HTTPUtils.encode_auth(login, password)}"

            # Make POST request with timeout
            return await self.http_utils.post_request_with_timeout(
                url=url.prm_string_value,
                body=body,
                auth=basic_auth,
                use_proxy=url.prm_value,
                tag=tag
            )
        except Exception as e:
            logger.error(f"An error occurred while calling connector :: {str(e)}", exc_info=True)
            return None

    async def get_to_connector(
            self,
            url: Parameter,
            context: str,
            tag: str
    ) -> Optional[HTTPResponse]:
        """
        Make a GET request to the connector

        Args:
            url: Parameter containing the base URL and proxy flag
            context: URL context/path to append
            tag: Tag for logging

        Returns:
            HTTPResponse or None if error
        """
        try:
            # Get credentials and build auth header
            login = await self.get_connector_login()
            password = await self.get_connector_password()
            basic_auth = f"Basic {HTTPUtils.encode_auth(login, password)}"

            # Build full URL
            full_url = url.prm_string_value + context

            # Make GET request
            return await self.http_utils.get_request(
                url=full_url,
                auth=basic_auth,
                use_proxy=url.prm_value,
                tag=tag
            )
        except Exception as e:
            logger.error(f"An error occurred while calling connector :: {str(e)}", exc_info=True)
            return None

    async def put_to_connector(
            self,
            url: Parameter,
            body: str,
            tag: str
    ) -> Optional[HTTPResponse]:
        """
        Make a PUT request to the connector

        Args:
            url: Parameter containing the URL and proxy flag
            body: Request body (JSON string)
            tag: Tag for logging

        Returns:
            HTTPResponse or None if error
        """
        try:
            # Get credentials and build auth header
            login = await self.get_connector_login()
            password = await self.get_connector_password()
            basic_auth = f"Basic {HTTPUtils.encode_auth(login, password)}"

            # Make PUT request
            return await self.http_utils.put_request(
                url=url.prm_string_value,
                body=body,
                auth=basic_auth,
                use_proxy=url.prm_value,
                tag=tag
            )
        except Exception as e:
            logger.error(f"An error occurred while calling connector :: {str(e)}", exc_info=True)
            return None

    async def post_to_product(
            self,
            url: str,
            body: str,
            tag: str
    ) -> Optional[HTTPResponse]:
        """
        Make a POST request to a product service

        Args:
            url: Target URL
            body: Request body (JSON string)
            tag: Tag for logging

        Returns:
            HTTPResponse or None if error
        """
        try:
            if url:
                # Use proxy if not localhost
                use_proxy = 0 if "localhost" in url else 1

                return await self.http_utils.post_request(
                    url=url,
                    body=body,
                    auth=None,
                    use_proxy=use_proxy,
                    tag=tag
                )
        except Exception as e:
            logger.error(f"An error occurred while calling product :: {str(e)}", exc_info=True)
            return None

    async def get_connector_login(self) -> str:
        """
        Get connector login from parameters (cached)

        Returns:
            Connector login string
        """
        if self._connector_login is None:
            param = self.parameter_service.get_parameter_by_code("CREDENTIAL_LOGIN")
            if param:
                self._connector_login = param.prm_string_value
                logger.debug("Cached connector login")
            else:
                logger.error("CREDENTIAL_LOGIN parameter not found")
                raise ValueError("CREDENTIAL_LOGIN parameter not found")

        return self._connector_login

    async def get_connector_password(self) -> str:
        """
        Get connector password from parameters (cached)

        Returns:
            Connector password string
        """
        if self._connector_password is None:
            param = self.parameter_service.get_parameter_by_code("CREDENTIAL_PASS")
            if param:
                self._connector_password = param.prm_string_value
                logger.debug("Cached connector password")
            else:
                logger.error("CREDENTIAL_PASS parameter not found")
                raise ValueError("CREDENTIAL_PASS parameter not found")

        return self._connector_password

    @classmethod
    def clear_cache(cls):
        """Clear cached credentials"""
        cls._connector_login = None
        cls._connector_password = None
        logger.info("BrokerGateway cache cleared")