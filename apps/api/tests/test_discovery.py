from fastapi.testclient import TestClient

from app.main import app


def test_discovery_lifecycle():
    with TestClient(app) as client:
        project = client.post("/api/v1/projects", json={"name": "Demo Studio"})
        assert project.status_code == 201
        project_id = project.json()["id"]

        started = client.post(f"/api/v1/business-discovery/start?project_id={project_id}")
        assert started.status_code == 201
        assert started.json()["status"] == "collecting"
        assert started.json()["open_questions"] == [
            "What industry does the business operate in?"
        ]

        first = client.post(
            "/api/v1/business-discovery/message",
            json={
                "project_id": project_id,
                "message": "We run a marketing agency.",
            },
        )
        assert first.status_code == 200
        assert first.json()["knowledge"]["industry"]["value"] == "marketing"
        assert first.json()["status"] == "collecting"
        assert first.json()["open_questions"] == [
            "What is the primary business goal for the website?"
        ]

        second = client.post(
            "/api/v1/business-discovery/message",
            json={
                "project_id": project_id,
                "message": "Our primary business goal is to generate more qualified commercial enquiries.",
            },
        )
        assert second.status_code == 200
        assert second.json()["knowledge"]["goals"][0]["value"] == (
            "generate more qualified commercial enquiries"
        )
        assert second.json()["knowledge"]["industry"]["value"] == "marketing"
        assert second.json()["status"] == "awaiting_approval"
        assert second.json()["open_questions"] == []

        # Optional fields can be captured later, but do not block the MVP gate.
        optional = client.post(
            "/api/v1/business-discovery/message",
            json={
                "project_id": project_id,
                "message": "We primarily serve B2B SaaS founders and marketing leaders. Clients choose us because we combine strategy with hands-on growth execution.",
            },
        )
        assert optional.status_code == 200
        assert optional.json()["knowledge"]["audience"][0]["value"] == (
            "B2B SaaS founders and marketing leaders"
        )
        assert optional.json()["knowledge"]["value_proposition"]["value"] == (
            "we combine strategy with hands-on growth execution"
        )
        assert optional.json()["status"] == "awaiting_approval"
        assert optional.json()["open_questions"] == []

        approved = client.post(f"/api/v1/business-discovery/approve/{project_id}")
        assert approved.status_code == 200
        assert approved.json()["context"]["status"] == "approved"

        immutable = client.post(
            "/api/v1/business-discovery/message",
            json={
                "project_id": project_id,
                "message": "This must not mutate approved context.",
            },
        )
        assert immutable.status_code == 409


def test_discovery_accumulates_multiple_goals_and_does_not_erase_knowledge():
    with TestClient(app) as client:
        project = client.post("/api/v1/projects", json={"name": "Acme"}).json()
        project_id = project["id"]
        client.post(f"/api/v1/business-discovery/start?project_id={project_id}")

        first = client.post(
            "/api/v1/business-discovery/message",
            json={
                "project_id": project_id,
                "message": "We are a fintech company and want more customers and visibility.",
            },
        ).json()

        assert first["knowledge"]["industry"]["value"] == "fintech"
        assert [goal["value"] for goal in first["knowledge"]["goals"]] == [
            "more customers and visibility",
        ]

        second = client.post(
            "/api/v1/business-discovery/message",
            json={
                "project_id": project_id,
                "message": "Our primary business goal is to increase qualified sales.",
            },
        ).json()

        assert second["knowledge"]["industry"]["value"] == "fintech"
        goal_values = [goal["value"] for goal in second["knowledge"]["goals"]]
        assert "more customers and visibility" in goal_values
        assert "increase qualified sales" in goal_values


def test_discovery_accepts_natural_language_goal_without_keyword():
    with TestClient(app) as client:
        project = client.post("/api/v1/projects", json={"name": "Studio"}).json()
        project_id = project["id"]
        client.post(f"/api/v1/business-discovery/start?project_id={project_id}")

        result = client.post(
            "/api/v1/business-discovery/message",
            json={
                "project_id": project_id,
                "message": "We are a consulting firm. The website should help us attract larger enterprise clients.",
            },
        ).json()

        assert result["knowledge"]["industry"]["value"] == "consulting"
        assert result["knowledge"]["goals"][0]["value"] == (
            "attract larger enterprise clients"
        )
        assert result["status"] == "awaiting_approval"
        assert result["open_questions"] == []
