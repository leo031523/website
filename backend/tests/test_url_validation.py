import pytest
from app.core.config import settings
from app.services.ai.url_validation import UnsafeProviderURLError, validate_provider_base_url


def test_rejects_non_http_scheme():
    with pytest.raises(UnsafeProviderURLError):
        validate_provider_base_url("ftp://example.com/v1")


def test_rejects_javascript_scheme():
    with pytest.raises(UnsafeProviderURLError):
        validate_provider_base_url("javascript:alert(1)")


def test_rejects_missing_hostname():
    with pytest.raises(UnsafeProviderURLError):
        validate_provider_base_url("http:///v1")


def test_allows_public_looking_url_in_development():
    # 開發環境不做 loopback/內網檢查，只要 scheme／hostname 合法就過
    validate_provider_base_url("http://localhost:11434/v1")


def test_allows_loopback_ip_literal_in_development(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "development")
    validate_provider_base_url("http://127.0.0.1:11434/v1")


def test_rejects_loopback_ip_literal_in_production(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    with pytest.raises(UnsafeProviderURLError):
        validate_provider_base_url("http://127.0.0.1:11434/v1")


def test_rejects_private_network_ip_in_production(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    with pytest.raises(UnsafeProviderURLError):
        validate_provider_base_url("http://10.0.0.5/v1")
    with pytest.raises(UnsafeProviderURLError):
        validate_provider_base_url("http://192.168.1.1/v1")


def test_rejects_cloud_metadata_ip_in_production(monkeypatch):
    """169.254.169.254 是 AWS/GCP/Azure 共用的 metadata endpoint，SSRF
    攻擊常見目標，屬於 link-local 範圍，一定要擋。"""
    monkeypatch.setattr(settings, "app_env", "production")
    with pytest.raises(UnsafeProviderURLError):
        validate_provider_base_url("http://169.254.169.254/latest/meta-data")


def test_rejects_ipv6_loopback_in_production(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    with pytest.raises(UnsafeProviderURLError):
        validate_provider_base_url("http://[::1]:11434/v1")


def test_allows_public_ip_literal_in_production(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    validate_provider_base_url("http://8.8.8.8/v1")


def test_allowlisted_hostname_bypasses_check_in_production(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "ai_local_model_allowlist", "localhost, internal-model.local")
    validate_provider_base_url("http://localhost:11434/v1")


def test_non_allowlisted_hostname_still_rejected_in_production(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "ai_local_model_allowlist", "internal-model.local")
    with pytest.raises(UnsafeProviderURLError):
        validate_provider_base_url("http://127.0.0.1:11434/v1")
