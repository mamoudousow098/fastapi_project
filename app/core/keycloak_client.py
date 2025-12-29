# ============================================================================
# File: app/core/keycloak_client.py
# Client for making authenticated requests to other services
# ============================================================================
import httpx
from typing import Optional, Dict, Any

from app.core.config import settings


class KeycloakClient:
    """Client for OAuth2 client credentials flow"""

    def __init__(self):
        self.token_url = settings.KEYCLOAK_TOKEN_URI
        self.client_id = settings.KEYCLOAK_CLIENT_ID
        self.client_secret = settings.KEYCLOAK_CLIENT_SECRET
        self._access_token: Optional[str] = None

    async def get_access_token(self) -> str:
        """
        Get access token using client credentials grant
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            if response.status_code != 200:
                raise Exception(f"Failed to get access token: {response.text}")

            token_data = response.json()
            self._access_token = token_data["access_token"]
            return self._access_token

    async def make_authenticated_request(
            self,
            url: str,
            method: str = "GET",
            **kwargs
    ) -> httpx.Response:
        """
        Make an authenticated request to another service
        """
        token = await self.get_access_token()

        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"Bearer {token}"
        kwargs["headers"] = headers

        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, **kwargs)
            return response
