from fastapi.testclient import TestClient

from app.main import app


def test_strategy_requires_approved_discovery_and_generates_vertical_slice():
    with TestClient(app) as client:
        project = client.post("/api/v1/projects", json={"name": "Strategy Demo"})
        assert project.status_code == 201
        project_id = project.json()["id"]

        not_ready = client.post(f"/api/v1/website-strategy/generate?project_id={project_id}")
        assert not_ready.status_code == 404

        client.post(f"/api/v1/business-discovery/start?project_id={project_id}")
        client.post("/api/v1/business-discovery/message", json={"project_id": project_id, "message": "We run a marketing agency."})
        complete = client.post("/api/v1/business-discovery/message", json={"project_id": project_id, "message": "Our goal is to generate leads."})
        assert complete.status_code == 200
        assert complete.json()["status"] == "awaiting_approval"
        client.post(f"/api/v1/business-discovery/approve/{project_id}")

        generated = client.post(f"/api/v1/website-strategy/generate?project_id={project_id}")
        assert generated.status_code == 201
        body = generated.json()
        assert body["status"] == "ready_for_review"
        assert [page["path"] for page in body["sitemap"]] == ["/", "/about", "/services", "/contact"]
        assert body["content"]["primary_cta"]
        assert body["design"]["responsive_priority"] == "high"
        assert body["evaluation"]["ready"] is True
        assert body["evaluation"]["traceability"] == 1.0

        revised = client.post(f"/api/v1/website-strategy/{project_id}/revise", json={"feedback": "CTA: Book a consultation"})
        assert revised.status_code == 200
        assert revised.json()["version"] == 2
        assert revised.json()["content"]["primary_cta"] == "Book a consultation"
        assert revised.json()["status"] == "ready_for_review"

        approved = client.post(f"/api/v1/website-strategy/{project_id}/approve")
        assert approved.status_code == 200
        assert approved.json()["status"] == "approved"

        blocked = client.post(f"/api/v1/website-strategy/{project_id}/revise", json={"feedback": "CTA: Contact us"})
        assert blocked.status_code == 409

def test_strategy_revision_applies_natural_language_feedback():
    with TestClient(app) as client:
        project = client.post(
            "/api/v1/projects",
            json={"name": "Natural Language Revision Demo"},
        )
        assert project.status_code == 201
        project_id = project.json()["id"]

        started = client.post(
            f"/api/v1/business-discovery/start?project_id={project_id}"
        )
        assert started.status_code == 201

        first = client.post(
            "/api/v1/business-discovery/message",
            json={
                "project_id": project_id,
                "message": (
                    "We run a B2B marketing consultancy helping companies "
                    "improve their commercial growth."
                ),
            },
        )
        assert first.status_code == 200

        complete = client.post(
            "/api/v1/business-discovery/message",
            json={
                "project_id": project_id,
                "message": (
                    "Our primary goal is to attract larger B2B clients and "
                    "generate more qualified commercial enquiries."
                ),
            },
        )
        assert complete.status_code == 200
        assert complete.json()["status"] == "awaiting_approval"

        approved_discovery = client.post(
            f"/api/v1/business-discovery/approve/{project_id}"
        )
        assert approved_discovery.status_code == 200

        generated = client.post(
            f"/api/v1/website-strategy/generate?project_id={project_id}"
        )
        assert generated.status_code == 201
        original = generated.json()

        feedback = (
            "Make the positioning more specific to B2B marketing "
            "decision-makers and make the primary conversion action "
            "a consultation request."
        )

        revised = client.post(
            f"/api/v1/website-strategy/{project_id}/revise",
            json={"feedback": feedback},
        )
        assert revised.status_code == 200

        body = revised.json()
        assert body["version"] == 2
        assert body["strategy_id"] != original["strategy_id"]
        assert body["status"] == "ready_for_review"
        assert body["approved_at"] is None

        assert body["content"]["positioning"] != original["content"]["positioning"]
        assert "B2B marketing decision-makers" in body["content"]["positioning"]
        assert body["content"]["key_messages"][0] == "Designed for B2B marketing decision-makers."
        assert body["content"]["primary_cta"] == "Request a consultation"

        assert body["sitemap"][0]["primary_cta"] == "Request a consultation"
        assert body["sitemap"][3]["primary_cta"] == "Request a consultation"
        assert feedback in body["revision_feedback"]
        assert feedback in body["rationale"][-1]
        assert body["source_context_version"] == original["source_context_version"]
        assert body["evaluation"]["traceability"] == 1.0
        assert body["evaluation"]["ready"] is True


def test_strategy_revision_explicit_cta_syntax_remains_supported():
    with TestClient(app) as client:
        project = client.post("/api/v1/projects", json={"name": "Explicit CTA Demo"})
        assert project.status_code == 201
        project_id = project.json()["id"]

        client.post(f"/api/v1/business-discovery/start?project_id={project_id}")
        client.post(
            "/api/v1/business-discovery/message",
            json={
                "project_id": project_id,
                "message": "We run a marketing agency.",
            },
        )
        complete = client.post(
            "/api/v1/business-discovery/message",
            json={
                "project_id": project_id,
                "message": "Our goal is to generate leads.",
            },
        )
        assert complete.status_code == 200
        client.post(f"/api/v1/business-discovery/approve/{project_id}")

        generated = client.post(
            f"/api/v1/website-strategy/generate?project_id={project_id}"
        )
        assert generated.status_code == 201

        revised = client.post(
            f"/api/v1/website-strategy/{project_id}/revise",
            json={"feedback": "CTA: Book a consultation"},
        )
        assert revised.status_code == 200
        assert revised.json()["content"]["primary_cta"] == "Book a consultation"
        assert revised.json()["sitemap"][0]["primary_cta"] == "Book a consultation"
        assert revised.json()["sitemap"][3]["primary_cta"] == "Book a consultation"



def test_strategy_derives_short_cta_from_business_goal():
    with TestClient(app) as client:
        project = client.post("/api/v1/projects", json={"name": "Coffee Strategy"}).json()
        project_id = project["id"]
        client.post(f"/api/v1/business-discovery/start?project_id={project_id}")
        client.post(
            "/api/v1/business-discovery/message",
            json={"project_id": project_id, "message": "We are a coffee shop. The business name is E2E Coffee Studio."},
        )
        complete = client.post(
            "/api/v1/business-discovery/message",
            json={
                "project_id": project_id,
                "message": "The main goal of the website is to build the brand, showcase the menu and atmosphere, and encourage people to visit the shop.",
            },
        )
        assert complete.status_code == 200
        client.post(f"/api/v1/business-discovery/approve/{project_id}")

        response = client.post(f"/api/v1/website-strategy/generate?project_id={project_id}")
        assert response.status_code == 201
        body = response.json()
        assert body["content"]["primary_cta"] == "Visit us"
        assert body["sitemap"][0]["primary_cta"] == "Visit us"


def test_strategy_uses_hospitality_page_vocabulary():
    with TestClient(app) as client:
        pid = client.post("/api/v1/projects", json={"name": "Hospitality Strategy"}).json()["id"]
        client.post(f"/api/v1/business-discovery/start?project_id={pid}")
        client.post("/api/v1/business-discovery/message", json={
            "project_id": pid,
            "message": "We are a specialty coffee shop called North Star Café. We welcome local customers and want the website to showcase our menu and encourage visits.",
        })
        client.post(f"/api/v1/business-discovery/approve/{pid}")
        body = client.post(f"/api/v1/website-strategy/generate?project_id={pid}").json()
        pages = {page["path"]: page for page in body["sitemap"]}
        assert pages["/services"]["name"] == "Menu & Coffee"
        assert "menu" in pages["/services"]["objective"].lower()
        assert pages["/contact"]["primary_cta"] == "Visit us"
