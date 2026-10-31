import pytest

from medilink_ai.gateway.identity.exceptions import IdentityProviderUnavailableError
from medilink_ai.gateway.identity.factory import create_identity_provider


def test_production_requires_explicit_identity_provider(monkeypatch):
    monkeypatch.setenv("MEDILINK_ENVIRONMENT", "production")
    monkeypatch.delenv("MEDILINK_IDENTITY_PROVIDER", raising=False)
    with pytest.raises(IdentityProviderUnavailableError):
        create_identity_provider()


def test_request_state_provider_is_explicitly_selectable(monkeypatch):
    monkeypatch.setenv("MEDILINK_ENVIRONMENT", "production")
    monkeypatch.setenv("MEDILINK_IDENTITY_PROVIDER", "request_state")
    assert create_identity_provider().__class__.__name__ == "RequestStateIdentityProvider"
