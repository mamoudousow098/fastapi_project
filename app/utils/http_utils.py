"""
HTTP utilities for making external API calls
Equivalent to Java HTTPUtils class
"""
import logging
import base64
import httpx
from typing import Optional, Dict
from dataclasses import dataclass
from datetime import datetime

from app.models.parameter import Parameter
from app.services.parameter import ParameterService

logger = logging.getLogger(__name__)


# ==================== HTTPResponse ====================
@dataclass
class HTTPResponse:
    """
    HTTP response object
    Equivalent to Java HTTPResponse class
    """
    code: Optional[int] = None
    body: Optional[str] = None
    headers: Optional[Dict[str, str]] = None

    def __repr__(self):
        return f"HTTPResponse(code={self.code}, body_length={len(self.body) if self.body else 0})"


# ==================== HTTPUtils ====================
class HTTPUtils:
    """
    HTTP utilities for making external requests
    Equivalent to Java HTTPUtils class
    """

    def __init__(self, parameter_service: ParameterService):
        self.parameter_service = parameter_service
        self._proxy_host: Optional[str] = None
        self._proxy_port: Optional[str] = None
        self._api_key_param: Optional[Parameter] = None
        self._url_nombo_param: Optional[Parameter] = None
        self._url_nombo_expire: float = 0

    def post_request(
            self,
            url: str,
            body: Optional[str],
            auth: Optional[str],
            use_proxy: int,
            tag: str
    ) -> HTTPResponse:
        """
        Make a POST request

        Args:
            url: Target URL
            body: Request body (JSON string)
            auth: Authorization header value
            use_proxy: 1 to use proxy, 0 otherwise
            tag: Tag for logging

        Returns:
            HTTPResponse object
        """
        logger.info(f"[BROKEREME] [{tag}] Calling url {url} with parameters {body}")

        headers = {
            "Content-Type": "application/json"
        }

        if auth:
            headers["Authorization"] = auth

        # Configure proxy
        proxy = None
        if use_proxy == 1:
            proxy = self._get_proxy_config(tag)

        # Create SYNCHRONOUS HTTP client with SSL verification disabled
        with httpx.Client(
                verify=False,  # Disable SSL verification
                proxy=proxy,
                timeout=30.0
        ) as client:
            try:
                response = client.post(url, content=body, headers=headers)

                http_response = HTTPResponse(
                    code=response.status_code,
                    body=response.text,
                    headers=dict(response.headers)
                )

                if response.status_code == 200:
                    logger.info(
                        f"[BROKEREME] [{tag}] Success Calling url {url} with parameters {body} "
                        f"error code {response.status_code}"
                    )
                else:
                    logger.info(
                        f"[BROKEREME] [{tag}] failed Calling url {url} with parameters {body} "
                        f"error code {response.status_code}"
                    )

                logger.info(f"[BROKEREME] [{tag}] Response body :: {response.text}")
                return http_response

            except httpx.TimeoutException as e:
                logger.error(f"[BROKEREME] [{tag}] Timeout calling url {url}: {str(e)}")
                return HTTPResponse(code=None, body=None)
            except Exception as e:
                logger.error(
                    f"[BROKEREME] [{tag}] failed Calling url {url} with parameters {body} "
                    f"exception {str(e)}", exc_info=True
                )
                return HTTPResponse(code=None, body=None)

    def post_request_with_timeout(
            self,
            url: str,
            body: Optional[str],
            auth: Optional[str],
            use_proxy: int,
            tag: str,
            timeout: float = 120.0
    ) -> HTTPResponse:
        """
        Make a POST request with custom timeout

        Args:
            url: Target URL
            body: Request body (JSON string)
            auth: Authorization header value
            use_proxy: 1 to use proxy, 0 otherwise
            tag: Tag for logging
            timeout: Timeout in seconds (default: 120)

        Returns:
            HTTPResponse object
        """
        logger.info(f"[BROKEREME] [{tag}] Calling url {url} with parameters {body}")

        headers = {
            "Content-Type": "application/json"
        }

        if auth:
            headers["Authorization"] = auth

        # Configure proxy
        proxy = None
        if use_proxy == 1:
            proxy = self._get_proxy_config(tag)

        # Create SYNCHRONOUS HTTP client with custom timeout
        with httpx.Client(
                verify=False,
                proxy=proxy,
                timeout=httpx.Timeout(timeout, connect=60.0)
        ) as client:
            try:
                response = client.post(url, content=body, headers=headers)

                http_response = HTTPResponse(
                    code=response.status_code,
                    body=response.text,
                    headers=dict(response.headers)
                )

                if response.status_code == 200:
                    logger.info(
                        f"[BROKEREME] [{tag}] Success Calling url {url} "
                        f"error code {response.status_code}"
                    )
                else:
                    logger.info(
                        f"[BROKEREME] [{tag}] failed Calling url {url} "
                        f"error code {response.status_code}"
                    )

                logger.info(f"[BROKEREME] [{tag}] Response body :: {response.text}")
                return http_response

            except httpx.TimeoutException as e:
                logger.error(
                    f"[BROKEREME] [{tag}] SocketTimeoutException occurred while calling url {url} "
                    f"with parameters {body}", exc_info=True
                )
                return HTTPResponse(code=None, body=None)
            except Exception as e:
                logger.error(
                    f"[BROKEREME] [{tag}] failed Calling url {url} with parameters {body} "
                    f"exception {str(e)}", exc_info=True
                )
                return HTTPResponse(code=None, body=None)

    def put_request(
            self,
            url: str,
            body: Optional[str],
            auth: Optional[str],
            use_proxy: int,
            tag: str
    ) -> HTTPResponse:
        """
        Make a PUT request

        Args:
            url: Target URL
            body: Request body (JSON string)
            auth: Authorization header value
            use_proxy: 1 to use proxy, 0 otherwise
            tag: Tag for logging

        Returns:
            HTTPResponse object
        """
        logger.info(f"[BROKEREME] [{tag}] Calling url {url} with parameters {body}")

        headers = {
            "Content-Type": "application/json"
        }

        if auth:
            headers["Authorization"] = auth

        # Configure proxy
        proxy = None
        if use_proxy == 1:
            proxy = self._get_proxy_config(tag)

        # Create SYNCHRONOUS HTTP client
        with httpx.Client(
                verify=False,
                proxy=proxy,
                timeout=30.0
        ) as client:
            try:
                response = client.put(url, content=body, headers=headers)

                http_response = HTTPResponse(
                    code=response.status_code,
                    body=response.text,
                    headers=dict(response.headers)
                )

                if response.status_code == 200:
                    logger.info(
                        f"[BROKEREME] [{tag}] Success Calling url {url} "
                        f"error code {response.status_code}"
                    )
                else:
                    logger.info(
                        f"[BROKEREME] [{tag}] failed Calling url {url} "
                        f"error code {response.status_code}"
                    )

                logger.info(f"[BROKEREME] [{tag}] Response body :: {response.text}")
                return http_response

            except Exception as e:
                logger.error(
                    f"[BROKEREME] [{tag}] failed Calling url {url} with parameters {body} "
                    f"exception {str(e)}", exc_info=True
                )
                return HTTPResponse(code=None, body=None)

    def get_request(
            self,
            url: str,
            auth: Optional[str],
            use_proxy: int,
            tag: str
    ) -> HTTPResponse:
        """
        Make a GET request

        Args:
            url: Target URL
            auth: Authorization header value
            use_proxy: 1 to use proxy, 0 otherwise
            tag: Tag for logging

        Returns:
            HTTPResponse object
        """
        logger.info(f"[BROKEREME] [{tag}] Calling url {url}")

        headers = {
            "Content-Type": "application/json"
        }

        if auth:
            headers["Authorization"] = auth

        # Configure proxy
        proxy = None
        if use_proxy == 1:
            proxy = self._get_proxy_config(tag)

        # Create SYNCHRONOUS HTTP client
        with httpx.Client(
                verify=False,
                proxy=proxy,
                timeout=30.0
        ) as client:
            try:
                response = client.get(url, headers=headers)

                http_response = HTTPResponse(
                    code=response.status_code,
                    body=response.text,
                    headers=dict(response.headers)
                )

                if response.status_code == 200:
                    logger.info(f"[BROKEREME] [{tag}] Success Calling url {url}")
                else:
                    logger.info(
                        f"[BROKEREME] [{tag}] failed Calling url {url} "
                        f"error code {response.status_code}"
                    )

                logger.info(f"[BROKEREME] [{tag}] Response body :: {response.text}")
                return http_response

            except Exception as e:
                logger.error(
                    f"[BROKEREME] [{tag}] failed Calling url {url} "
                    f"exception {str(e)}", exc_info=True
                )
                return HTTPResponse(code=None, body=None)

    def _get_proxy_config(self, tag: str) -> Optional[str]:
        """Get proxy configuration - returns proxy URL string for httpx"""
        try:
            proxy_host = self.get_proxy_host()
            proxy_port = self.get_proxy_port()

            if proxy_host and proxy_port:
                logger.info(f"[BROKEREME] [{tag}] ###### USING PROXY #####")
                # httpx.Client expects a single proxy URL string, not a dict
                return f"http://{proxy_host}:{proxy_port}"
        except Exception as e:
            logger.error(f"[BROKEREME] [{tag}] failed getting proxy data {str(e)}")

        return None

    def get_proxy_host(self) -> Optional[str]:
        """Get proxy host from parameters (cached)"""
        if self._proxy_host is None:
            param = self.parameter_service.get_parameter_by_code("proxy_host")
            if param:
                self._proxy_host = param.prm_string_value.strip()
        return self._proxy_host

    def get_proxy_port(self) -> Optional[str]:
        """Get proxy port from parameters (cached)"""
        if self._proxy_port is None:
            param = self.parameter_service.get_parameter_by_code("proxy_port")
            if param:
                self._proxy_port = param.prm_string_value.strip()
        return self._proxy_port

    def get_nombo_param(self) -> Optional[Parameter]:
        """Get Nombo URL parameter (cached with expiry)"""
        if self._url_nombo_param is None or self._is_url_expired():
            logger.info("[NOMBO] param is null or the url is expired: fetching new one")
            self._url_nombo_param = self.parameter_service.get_parameter_by_code("URL_NOMBO")
            # Set expiry to 2 minutes from now
            self._url_nombo_expire = datetime.now().timestamp() + 120
        return self._url_nombo_param

    def _is_url_expired(self) -> bool:
        """Check if URL parameter has expired"""
        current_time = datetime.now().timestamp()
        time_left = self._url_nombo_expire - current_time
        return time_left < 1

    def get_api_key(self) -> Optional[Parameter]:
        """Get API key parameter (cached)"""
        if self._api_key_param is None:
            self._api_key_param = self.parameter_service.get_parameter_by_code("API_KEY_NOMBO")
        return self._api_key_param

    @staticmethod
    def encode_auth(username: str, password: str) -> str:
        """
        Encode username and password to Base64 for Basic Auth

        Args:
            username: Username
            password: Password

        Returns:
            Base64 encoded string
        """
        auth_string = f"{username}:{password}"
        auth_bytes = auth_string.encode('utf-8')
        encoded = base64.b64encode(auth_bytes)
        return encoded.decode('utf-8')