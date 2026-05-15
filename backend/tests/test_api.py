"""
API smoke tests using FastAPI TestClient with an in-memory SQLite database.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SEED_DEMO_DATA"] = "true"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from models.db import Base
from storage.database import get_db

TEST_DB_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True, scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    from storage.seed import seed
    db = TestingSession()
    seed(db)
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_cluster_summary(client):
    resp = client.get("/api/v1/cluster/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "name" in data
    assert "workload_count" in data
    assert data["is_estimated"] is True
    assert data["estimated_monthly_cost_usd"] >= 0


def test_list_namespaces(client):
    resp = client.get("/api/v1/namespaces")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    names = [ns["name"] for ns in data]
    assert "production" in names


def test_list_workloads(client):
    resp = client.get("/api/v1/workloads")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert data["total"] > 0
    item = data["items"][0]
    assert "name" in item
    assert "namespace" in item
    assert item["is_estimated"] is True


def test_list_workloads_namespace_filter(client):
    resp = client.get("/api/v1/workloads?namespace=production")
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert item["namespace"] == "production"


def test_workload_detail(client):
    resp = client.get("/api/v1/workloads/1")
    assert resp.status_code == 200
    data = resp.json()
    assert "containers" in data
    assert "recommendations" in data


def test_workload_not_found(client):
    resp = client.get("/api/v1/workloads/999999")
    assert resp.status_code == 404


def test_list_recommendations(client):
    resp = client.get("/api/v1/recommendations")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    rec = data[0]
    assert "flag_type" in rec
    assert "confidence" in rec
    assert "risk" in rec
    assert "explanation" in rec
    assert rec["is_estimated"] is True


def test_recommendations_risk_filter(client):
    resp = client.get("/api/v1/recommendations?risk=high")
    assert resp.status_code == 200
    for rec in resp.json():
        assert rec["risk"] == "high"


def test_savings_estimate(client):
    resp = client.get("/api/v1/recommendations/savings")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_potential_savings_usd" in data
    assert data["is_estimated"] is True
    assert isinstance(data["savings_by_namespace"], list)


def test_recommendation_has_patch(client):
    resp = client.get("/api/v1/recommendations")
    recs = resp.json()
    patched = [r for r in recs if r.get("yaml_patch")]
    assert len(patched) > 0
    assert "advisory" in patched[0]["yaml_patch"].lower()


def test_recommendation_detail(client):
    recs = client.get("/api/v1/recommendations").json()
    if recs:
        rec_id = recs[0]["id"]
        resp = client.get(f"/api/v1/recommendations/{rec_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == rec_id
