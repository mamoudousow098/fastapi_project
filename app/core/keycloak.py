# ============================================================================
# File: app/core/keycloak.py
# Keycloak authentication and authorization
# ============================================================================
import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException, Security, status
from fastapi.security import OAuth2AuthorizationCodeBearer, HTTPBearer, HTTPAuthorizationCredentials

# IMPORTANT: Use python-jose, NOT PyJWT
from jose import jwt, JWTError, jwk
from jose.exceptions import ExpiredSignatureError, JWTClaimsError
from jose.utils import base64url_decode

import httpx
from functools import lru_cache

from app.core.config import settings

logger = logging.getLogger(__name__)

# OAuth2 scheme for Swagger UI
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{settings.KEYCLOAK_ISSUER_URI}/protocol/openid-connect/auth",
    tokenUrl=f"{settings.KEYCLOAK_ISSUER_URI}/protocol/openid-connect/token",
    scopes={
        "openid": "OpenID Connect",
        "profile": "User profile",
        "email": "Email address"
    }
)

# Alternative: Bearer token scheme for API usage
http_bearer = HTTPBearer()


@lru_cache(maxsize=1)
def get_jwks() -> Dict[str, Any]:
    """
    Fetch and cache JWKS (JSON Web Key Set) from Keycloak
    """
    try:
        response = httpx.get(settings.KEYCLOAK_JWKS_URI, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch JWKS: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to fetch authentication keys"
        )


def get_public_key(token: str) -> str:
    """
    Get the public key for JWT verification from JWKS
    """
    try:
        # Decode header to get kid (key ID)
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        if not kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token header"
            )

        # Get JWKS and find the matching key
        jwks = get_jwks()
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                return jwk.construct(key).to_pem().decode("utf-8")

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Public key not found"
        )
    except JWTError as e:
        logger.error(f"JWT error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode JWT token
    """
    try:
        # Get public key
        public_key = get_public_key(token)

        # Verify and decode token
        payload = jwt.decode(
            token,
            public_key,
            algorithms=[settings.JWT_ALGORITHM],
            issuer=settings.KEYCLOAK_ISSUER_URI,
            audience=settings.JWT_AUDIENCE,
            options={
                "verify_signature": True,
                "verify_aud": settings.JWT_AUDIENCE is not None,
                "verify_iat": True,
                "verify_exp": True,
                "verify_nbf": True,
                "verify_iss": True,
            }
        )

        return payload

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except JWTClaimsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token claims: {str(e)}"
        )
    except JWTError as e:
        logger.error(f"JWT verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Security(http_bearer)
) -> Dict[str, Any]:
    """
    Dependency to get current authenticated user from JWT token
    """
    token = credentials.credentials
    payload = verify_token(token)

    return {
        "sub": payload.get("sub"),
        "preferred_username": payload.get("preferred_username"),
        "email": payload.get("email"),
        "name": payload.get("name"),
        "given_name": payload.get("given_name"),
        "family_name": payload.get("family_name"),
        "realm_access": payload.get("realm_access", {}),
        "resource_access": payload.get("resource_access", {}),
        "scope": payload.get("scope", "").split(),
    }


def require_role(required_role: str):
    """
    Dependency factory to check if user has required role

    Usage:
        @app.get("/admin", dependencies=[Depends(require_role("admin"))])
    """
    async def check_role(current_user: Dict = Security(get_current_user)):
        roles = current_user.get("realm_access", {}).get("roles", [])

        if required_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have required role: {required_role}"
            )

        return current_user

    return check_role


def require_any_role(*required_roles: str):
    """
    Dependency factory to check if user has any of the required roles

    Usage:
        @app.get("/resource", dependencies=[Depends(require_any_role("admin", "moderator"))])
    """
    async def check_roles(current_user: Dict = Security(get_current_user)):
        roles = current_user.get("realm_access", {}).get("roles", [])

        if not any(role in roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have any of the required roles: {', '.join(required_roles)}"
            )

        return current_user

    return check_roles