"""Production & Sandbox PayPal REST v2 API Client with OAuth2 Single-Flight Token Manager.
Adheres to Master PRD V2 Section 8.3 & Section 8.5.
"""
import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import httpx

logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PayPalError(Exception):
    """Base exception for PayPal operations."""
    pass


class PayPalAuthError(PayPalError):
    """Raised when OAuth2 authentication fails."""
    pass


class PayPalAPIError(PayPalError):
    """Raised when PayPal returns a 4xx or 5xx status."""
    def __init__(self, message: str, status_code: int, response_body: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class PayPalConnectionError(PayPalError):
    """Raised on network or transport failure."""
    pass


class PayPalClient:
    """Async HTTP client for PayPal REST v2 APIs."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout_seconds: float = 15.0,
    ):
        self.client_id = (client_id if client_id is not None else os.environ.get("PAYPAL_CLIENT_ID", "")).strip()
        self.client_secret = (client_secret if client_secret is not None else os.environ.get("PAYPAL_CLIENT_SECRET", "")).strip()
        self.base_url = (
            base_url or os.environ.get("PAYPAL_API_BASE_URL", "https://api-m.sandbox.paypal.com")
        ).rstrip("/")
        self.timeout = timeout_seconds

        # Token caching state & single-flight lock
        self._cached_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._token_lock = asyncio.Lock()

    @property
    def is_configured(self) -> bool:
        """True if non-empty client credentials are present."""
        return bool(self.client_id and self.client_secret)

    async def get_access_token(self, force_refresh: bool = False) -> str:
        """Fetch or reuse cached OAuth2 Bearer token with a 60-second safety buffer."""
        now = utcnow()
        if (
            not force_refresh
            and self._cached_token
            and self._token_expires_at
            and now < self._token_expires_at - timedelta(seconds=60)
        ):
            return self._cached_token

        async with self._token_lock:
            # Double-check inside lock
            now = utcnow()
            if (
                not force_refresh
                and self._cached_token
                and self._token_expires_at
                and now < self._token_expires_at - timedelta(seconds=60)
            ):
                return self._cached_token

            if not self.is_configured:
                raise PayPalAuthError(
                    "PayPal credentials missing: PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET must be set."
                )

            token_url = f"{self.base_url}/v1/oauth2/token"
            headers = {
                "Accept": "application/json",
                "Accept-Language": "en_US",
            }
            data = {"grant_type": "client_credentials"}

            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    res = await client.post(
                        token_url,
                        data=data,
                        headers=headers,
                        auth=(self.client_id, self.client_secret),
                    )
                    if res.status_code == 200:
                        body = res.json()
                        token = body.get("access_token")
                        expires_in = body.get("expires_in", 3600)
                        if not token:
                            raise PayPalAuthError("OAuth response missing 'access_token' field")
                        self._cached_token = token
                        self._token_expires_at = now + timedelta(seconds=expires_in)
                        logger.info("Successfully fetched fresh PayPal OAuth2 token; valid for %ds", expires_in)
                        return token
                    elif res.status_code in (401, 403):
                        raise PayPalAuthError(f"PayPal OAuth authentication rejected [HTTP {res.status_code}]")
                    else:
                        raise PayPalAPIError(
                            f"PayPal OAuth token request failed [HTTP {res.status_code}]",
                            status_code=res.status_code,
                            response_body=res.text[:300],
                        )
            except (PayPalAuthError, PayPalAPIError):
                raise
            except Exception as exc:
                raise PayPalConnectionError(f"Network error contacting PayPal OAuth endpoint ({token_url}): {exc}") from exc

    async def request(
        self,
        method: str,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Execute an authenticated request against the PayPal REST API."""
        token = await self.get_access_token()
        url = f"{self.base_url}{path}" if path.startswith("/") else f"{self.base_url}/{path}"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if idempotency_key:
            headers["PayPal-Request-Id"] = idempotency_key
        if extra_headers:
            headers.update(extra_headers)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.request(
                    method=method.upper(),
                    url=url,
                    json=json_data,
                    headers=headers,
                )

                if res.status_code in (200, 201):
                    return res.json()
                elif res.status_code == 204:
                    # Void or empty body success
                    return {}
                elif res.status_code == 401:
                    # Token might have expired early; clear cache and raise
                    self._cached_token = None
                    self._token_expires_at = None
                    raise PayPalAuthError("PayPal token rejected (HTTP 401 Unauthorized)")
                else:
                    error_detail = res.text[:500]
                    try:
                        error_json = res.json()
                    except Exception:
                        error_json = {"raw": error_detail}
                    raise PayPalAPIError(
                        f"PayPal REST API error [HTTP {res.status_code}]: {error_detail}",
                        status_code=res.status_code,
                        response_body=error_json,
                    )
        except (PayPalAuthError, PayPalAPIError):
            raise
        except Exception as exc:
            raise PayPalConnectionError(f"Network error during PayPal REST {method} {url}: {exc}") from exc
