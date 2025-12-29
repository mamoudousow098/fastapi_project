from datetime import datetime, timedelta
from typing import Any, Optional, Dict
from passlib.context import CryptContext
from jose import jwt, JWTError
from jose.exceptions import ExpiredSignatureError, JWTClaimsError
from app.core.config import settings

from fastapi import HTTPException, status


from functools import lru_cache
import httpx

@lru_cache(maxsize=1)
def get_keycloak_public_key() -> str:
    """Fetch public key from Keycloak JWKS endpoint"""
    jwks_url = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/certs"

    try:
        response = httpx.get(jwks_url, timeout=10)
        response.raise_for_status()
        jwks = response.json()

        # Get first key (or match by kid if needed)
        from jose import jwk
        key_data = jwks["keys"][0]
        public_key = jwk.construct(key_data).to_pem().decode('utf-8')

        return public_key
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Cannot fetch Keycloak public key: {str(e)}"
        )


def get_user_from_token_verified(authorization: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Extract and VERIFY user information from Keycloak JWT token
    """
    if not authorization:
        return None

    try:
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format"
            )

        token = authorization.replace("Bearer ", "")

        # Get public key from Keycloak
        public_key = get_keycloak_public_key()

        # Decode and VERIFY token with Keycloak public key
        decoded = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=settings.KEYCLOAK_CLIENT_ID,  # Or None if no audience check
            issuer=f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}",
            options={
                "verify_signature": True,
                "verify_aud": False,  # Set to True if you have audience in token
                "verify_exp": True,
                "verify_iss": True,
            }
        )

        # Extract user information
        user_info = {
            "username": decoded.get("preferred_username") or decoded.get("sub"),
            "account_number": decoded.get("account_number"),
            "pos_account_number": decoded.get("pos_account_number"),
            "email": decoded.get("email"),
            "roles": decoded.get("realm_access", {}).get("roles", []),
            "client_id": decoded.get("azp") or decoded.get("client_id"),
        }

        return user_info

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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )


def get_user_from_token(authorization: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Extract user information from JWT token.
    Equivalent to AuthUtils.getUserFromToken()

    Args:
        authorization: Authorization header value (Bearer token)

    Returns:
        Dict containing user information or None if no token

    Raises:
        HTTPException: If token is invalid
    """
    if not authorization:
        return None

    try:
        # Extract token from "Bearer <token>"
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format"
            )

        token = authorization.replace("Bearer ", "")

        # Decode JWT token without verification
        # Note: jwt.decode() from python-jose requires a key even with verify_signature=False
        # We pass an empty string as key when not verifying
        decoded = jwt.decode(
            token,
            key="",  # Empty key when verify_signature is False
            options={"verify_signature": False}  # Set to True in production with proper secret
        )

        # Extract user information from token
        user_info = {
            "username": decoded.get("preferred_username") or decoded.get("sub"),
            "account_number": decoded.get("account_number"),
            "pos_account_number": decoded.get("pos_account_number"),
            "email": decoded.get("email"),
            "roles": decoded.get("realm_access", {}).get("roles", []),
            "client_id": decoded.get("azp") or decoded.get("client_id"),
            # Add other fields as needed
        }

        return user_info

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Error processing token: {str(e)}"
        )


def verify_token(token: str, secret_key: str, algorithms: list = ["HS256"]) -> Dict[str, Any]:
    """
    Verify and decode a JWT token with signature verification.

    Args:
        token: JWT token string
        secret_key: Secret key for verification
        algorithms: List of allowed algorithms

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        decoded = jwt.decode(
            token,
            secret_key,
            algorithms=algorithms
        )
        return decoded
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


# Context pour le hashing des mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie un mot de passe"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash un mot de passe"""
    return pwd_context.hash(password)


def create_access_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    """Crée un token JWT"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> dict:
    """Décode un token JWT"""
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM]
    )