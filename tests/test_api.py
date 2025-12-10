"""Tests for API endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check_success(self, client: TestClient):
        """Test successful health check."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "version" in data
        assert "database" in data
        assert "timestamp" in data

    def test_health_check_no_auth_required(self, client: TestClient):
        """Test health check doesn't require authentication."""
        response = client.get("/health")
        assert response.status_code == 200


class TestDashboardEndpoint:
    """Tests for dashboard endpoint."""

    def test_dashboard_requires_auth(self, client: TestClient):
        """Test dashboard requires authentication."""
        response = client.get("/dashboard")
        assert response.status_code == 401

    def test_dashboard_with_auth(self, client: TestClient, auth_headers: dict):
        """Test dashboard with valid authentication."""
        response = client.get("/dashboard", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "summary" in data
        assert "transactions" in data
        assert "alerts" in data
        assert "charts" in data

    def test_dashboard_summary_fields(self, client: TestClient, auth_headers: dict):
        """Test dashboard summary contains expected fields."""
        response = client.get("/dashboard", headers=auth_headers)
        data = response.json()

        summary = data["summary"]
        assert "total_balance_xrp" in summary
        assert "inflow_24h" in summary
        assert "outflow_24h" in summary
        assert "alert_count" in summary


class TestTransactionsEndpoint:
    """Tests for transactions endpoint."""

    def test_transactions_requires_auth(self, client: TestClient):
        """Test transactions endpoint requires authentication."""
        response = client.get("/transactions")
        assert response.status_code == 401

    def test_transactions_with_auth(self, client: TestClient, auth_headers: dict):
        """Test transactions with valid authentication."""
        response = client.get("/transactions", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_transactions_with_limit(self, client: TestClient, auth_headers: dict):
        """Test transactions with limit parameter."""
        response = client.get("/transactions?limit=10", headers=auth_headers)
        assert response.status_code == 200

    def test_transactions_with_direction_filter(self, client: TestClient, auth_headers: dict):
        """Test transactions with direction filter."""
        response = client.get("/transactions?direction=inbound", headers=auth_headers)
        assert response.status_code == 200

    def test_transactions_invalid_direction(self, client: TestClient, auth_headers: dict):
        """Test transactions with invalid direction filter."""
        response = client.get("/transactions?direction=invalid", headers=auth_headers)
        assert response.status_code == 422  # Validation error


class TestAlertsEndpoint:
    """Tests for alerts endpoint."""

    def test_alerts_requires_auth(self, client: TestClient):
        """Test alerts endpoint requires authentication."""
        response = client.get("/alerts")
        assert response.status_code == 401

    def test_alerts_list(self, client: TestClient, auth_headers: dict):
        """Test listing alerts."""
        response = client.get("/alerts", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "items" in data

    def test_alerts_filter_by_status(self, client: TestClient, auth_headers: dict):
        """Test filtering alerts by status."""
        response = client.get("/alerts?status=open", headers=auth_headers)
        assert response.status_code == 200

    def test_create_alert_rule(self, client: TestClient, auth_headers: dict):
        """Test creating an alert rule."""
        rule_data = {
            "name": "Test Rule",
            "min_amount_xrp": 100.0,
            "direction": "inbound",
        }
        response = client.post("/alerts", json=rule_data, headers=auth_headers)
        assert response.status_code == 201

        data = response.json()
        assert "id" in data
        assert data["name"] == "Test Rule"

    def test_create_alert_rule_invalid_direction(self, client: TestClient, auth_headers: dict):
        """Test creating alert rule with invalid direction."""
        rule_data = {
            "name": "Test Rule",
            "direction": "invalid",
        }
        response = client.post("/alerts", json=rule_data, headers=auth_headers)
        assert response.status_code == 422

    def test_acknowledge_nonexistent_alert(self, client: TestClient, auth_headers: dict):
        """Test acknowledging a non-existent alert."""
        response = client.post("/alerts/99999/ack", headers=auth_headers)
        assert response.status_code == 404


class TestAuthentication:
    """Tests for API authentication."""

    def test_invalid_api_key(self, client: TestClient):
        """Test request with invalid API key."""
        headers = {"X-API-Key": "invalid-key"}
        response = client.get("/dashboard", headers=headers)
        assert response.status_code == 401

    def test_missing_api_key(self, client: TestClient):
        """Test request without API key."""
        response = client.get("/dashboard")
        assert response.status_code == 401

    def test_empty_api_key(self, client: TestClient):
        """Test request with empty API key."""
        headers = {"X-API-Key": ""}
        response = client.get("/dashboard", headers=headers)
        assert response.status_code == 401
