"""Tests for the Formula E Driver Performance Analyzer."""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


class TestHealth:
    def test_health_returns_200(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "healthy"
        assert body["service"] == "driver-performance-analyzer"


# ---------------------------------------------------------------------------
# Evaluation – scoring scenarios
# ---------------------------------------------------------------------------


class TestEvaluation:
    """POST /api/v1/evaluate with various telemetry inputs."""

    def _post(self, **overrides):
        payload = {
            "driver_id": "TEST01",
            "lap_number": 1,
            "turn_3_regen_kw": 0.0,
            "turn_13_regen_kw": 0.0,
            "lift_coast_distance_meters": 0.0,
            **overrides,
        }
        return client.post("/api/v1/evaluate", json=payload)

    # -- Ideal lap --------------------------------------------------------

    def test_ideal_lap(self):
        """Both turns >= 500 kW, lift-coast >= 50 m → 100, EXCELLENT."""
        resp = self._post(
            turn_3_regen_kw=550,
            turn_13_regen_kw=520,
            lift_coast_distance_meters=55,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["efficiency_score"] == 100
        assert body["rating"] == "EXCELLENT"
        assert body["sensor_fault_detected"] is False
        assert body["feedback"] == []

    # -- Partial braking --------------------------------------------------

    def test_partial_braking(self):
        """Only one turn >= 500 kW → braking = 25."""
        resp = self._post(
            turn_3_regen_kw=510,
            turn_13_regen_kw=300,
            lift_coast_distance_meters=55,
        )
        body = resp.json()
        assert body["efficiency_score"] == 75  # 25 + 50
        assert body["rating"] == "OPTIMAL"
        assert any("Turn 13" in fb for fb in body["feedback"])

    # -- Low lift-and-coast -----------------------------------------------

    def test_low_lift_coast(self):
        """Lift-coast < 25 m → 0 points from lift-coast."""
        resp = self._post(
            turn_3_regen_kw=510,
            turn_13_regen_kw=520,
            lift_coast_distance_meters=10,
        )
        body = resp.json()
        assert body["efficiency_score"] == 50  # 50 + 0
        assert body["rating"] == "NEEDS_IMPROVEMENT"
        assert any("Lift-and-coast" in fb for fb in body["feedback"])

    # -- Sensor fault (> 600 kW) ------------------------------------------

    def test_sensor_fault_flags_and_caps(self):
        """Values > 600 kW must be flagged and capped at 600 for scoring."""
        resp = self._post(
            turn_3_regen_kw=700,
            turn_13_regen_kw=800,
            lift_coast_distance_meters=55,
        )
        body = resp.json()
        assert body["sensor_fault_detected"] is True
        assert body["efficiency_score"] == 100  # both capped at 600 >= 500; lc >= 50
        assert body["rating"] == "EXCELLENT"
        # Both sensor faults should produce warnings.
        fault_msgs = [fb for fb in body["feedback"] if "Sensor fault" in fb]
        assert len(fault_msgs) == 2
        # Chart URL should use the capped values, not the originals.
        assert "t3=600" in body["chart_url"]
        assert "t13=600" in body["chart_url"]

    # -- Boundary values --------------------------------------------------

    def test_boundary_500_both(self):
        """Exactly 500 kW on both turns counts as meeting the threshold."""
        resp = self._post(
            turn_3_regen_kw=500,
            turn_13_regen_kw=500,
            lift_coast_distance_meters=50,
        )
        body = resp.json()
        assert body["efficiency_score"] == 100
        assert body["rating"] == "EXCELLENT"

    def test_boundary_600_exactly(self):
        """Exactly 600 kW should NOT trigger sensor fault (only > 600)."""
        resp = self._post(
            turn_3_regen_kw=600,
            turn_13_regen_kw=600,
            lift_coast_distance_meters=50,
        )
        body = resp.json()
        assert body["sensor_fault_detected"] is False
        assert body["efficiency_score"] == 100

    def test_boundary_lift_coast_50(self):
        """Exactly 50 m gets full lift-coast points."""
        resp = self._post(
            turn_3_regen_kw=500,
            turn_13_regen_kw=500,
            lift_coast_distance_meters=50,
        )
        body = resp.json()
        assert body["efficiency_score"] == 100

    def test_boundary_lift_coast_25(self):
        """Exactly 25 m gets mid-range lift-coast points (25)."""
        resp = self._post(
            turn_3_regen_kw=500,
            turn_13_regen_kw=500,
            lift_coast_distance_meters=25,
        )
        body = resp.json()
        assert body["efficiency_score"] == 75  # 50 + 25
        assert body["rating"] == "OPTIMAL"

    def test_boundary_just_below_25(self):
        """24.9 m → 0 lift-coast points."""
        resp = self._post(
            turn_3_regen_kw=500,
            turn_13_regen_kw=500,
            lift_coast_distance_meters=24.9,
        )
        body = resp.json()
        assert body["efficiency_score"] == 50  # 50 + 0
        assert body["rating"] == "NEEDS_IMPROVEMENT"

    # -- Minimum score clamping -------------------------------------------

    def test_minimum_score_clamped_to_1(self):
        """Raw 10 + 0 = 10, which is above 1, but let's also ensure
        the very worst score (neither braking, no coast) gives 10."""
        resp = self._post(
            turn_3_regen_kw=0,
            turn_13_regen_kw=0,
            lift_coast_distance_meters=0,
        )
        body = resp.json()
        assert body["efficiency_score"] == 10  # 10 + 0

    # -- Validation errors (422) ------------------------------------------

    def test_validation_negative_regen(self):
        """Negative regen value → 422."""
        resp = self._post(turn_3_regen_kw=-10)
        assert resp.status_code == 422

    def test_validation_negative_lift_coast(self):
        """Negative lift-coast → 422."""
        resp = self._post(lift_coast_distance_meters=-5)
        assert resp.status_code == 422

    def test_validation_zero_lap_number(self):
        """lap_number 0 → 422 (must be >= 1)."""
        resp = self._post(lap_number=0)
        assert resp.status_code == 422

    def test_validation_missing_driver_id(self):
        """Missing required field → 422."""
        resp = client.post(
            "/api/v1/evaluate",
            json={
                "lap_number": 1,
                "turn_3_regen_kw": 500,
                "turn_13_regen_kw": 500,
                "lift_coast_distance_meters": 50,
            },
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Chart endpoint
# ---------------------------------------------------------------------------


class TestChart:
    def test_chart_returns_png(self):
        """GET /api/v1/chart should return image/png with PNG magic bytes."""
        resp = client.get("/api/v1/chart?t3=500&t13=500&lc=55")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/png"
        # PNG magic bytes: \x89PNG\r\n\x1a\n
        assert resp.content[:4] == b"\x89PNG"


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


class TestDashboard:
    def test_dashboard_returns_200_with_title(self):
        """GET /dashboard should return HTML containing the page title."""
        resp = client.get("/dashboard")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "Formula E" in resp.text
        assert "Performance Analyzer" in resp.text
