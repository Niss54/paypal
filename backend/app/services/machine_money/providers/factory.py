"""Provider factory to resolve the active Lightning payment provider based on configuration."""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

from backend.app.services.machine_money.providers.base import LightningProvider
from backend.app.services.machine_money.providers.mock import MockLightningProvider
from backend.app.services.machine_money.providers.lnbits import LNbitsProvider
from backend.app.services.machine_money.providers.nwc import NWCProvider
from backend.app.services.machine_money.providers.paypal import PayPalProvider

_cached_provider: Optional[LightningProvider] = None


def get_payment_provider(force_refresh: bool = False) -> LightningProvider:
    """Returns the instance of the configured payment provider.
    Respects MACHINE_MONEY_PROVIDER environment variable ('mock' | 'lnbits' | 'nwc' | 'paypal').
    """
    global _cached_provider
    provider_type = os.environ.get("MACHINE_MONEY_PROVIDER", "mock").strip().lower()

    if _cached_provider is not None and not force_refresh:
        if getattr(_cached_provider, "name", "") == provider_type:
            return _cached_provider

    if provider_type == "paypal":
        _cached_provider = PayPalProvider()
    elif provider_type == "lnbits":
        _cached_provider = LNbitsProvider()
    elif provider_type in ("nwc", "nostr"):
        _cached_provider = NWCProvider()
    else:
        # Resilient fallback or explicitly requested mock provider
        _cached_provider = MockLightningProvider()

    return _cached_provider
