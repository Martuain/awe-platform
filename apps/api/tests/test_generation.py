from fastapi.testclient import TestClient
from app.main import app


def test_generation_requires_approved_specification_and_generates_pages():
    with TestClient(app) as client:
        pid = client.post("/api/v1/projects", json={"name": "Generation Demo"}).json()["id"]
        assert client.post(f"/api/v1/website-generation/generate?project_id={pid}").status_code == 404
        client.post(f"/api/v1/business-discovery/start?project_id={pid}")
        client.post("/api/v1/business-discovery/message", json={"project_id": pid, "message": "We run a marketing agency."})
        client.post("/api/v1/business-discovery/message", json={"project_id": pid, "message": "Our goal is to generate leads."})
        client.post(f"/api/v1/business-discovery/approve/{pid}")
        client.post(f"/api/v1/website-strategy/generate?project_id={pid}")
        client.post(f"/api/v1/website-strategy/{pid}/approve")
        client.post(f"/api/v1/brand-design/generate?project_id={pid}")
        client.post(f"/api/v1/brand-design/{pid}/approve")
        client.post(f"/api/v1/website-specification/generate?project_id={pid}")
        client.post(f"/api/v1/website-specification/{pid}/approve")
        generated = client.post(f"/api/v1/website-generation/generate?project_id={pid}")
        assert generated.status_code == 201
        body = generated.json()
        assert body["status"] == "validated"
        assert body["source_specification_version"] == 1
        assert body["pages_generated"]
        assert any(file["path"] == "app/page.tsx" for file in body["files"])
        package = next(file["content"] for file in body["files"] if file["path"] == "package.json")
        assert package.find('"typescript":"5.8.2"') >= 0
        assert package.find('"@types/react":"19.1.10"') >= 0
        assert package.find('"@types/node":"20.17.6"') >= 0
        layout = next(file["content"] for file in body["files"] if file["path"] == "app/layout.tsx")
        contact = next(file["content"] for file in body["files"] if file["path"] == "app/contact/page.tsx")
        assert "title:" in layout
        assert 'form className="card contact-form"' in contact
        assert 'name="email"' in contact
        assert body["validation"]["specification_approved"] is True


def test_generation_keeps_vertical_copy_out_of_specification_labels():
    with TestClient(app) as client:
        pid = client.post("/api/v1/projects", json={"name": "Fresh E2E Café"}).json()["id"]
        client.post(f"/api/v1/business-discovery/start?project_id={pid}")
        client.post("/api/v1/business-discovery/message", json={
            "project_id": pid,
            "message": (
                "We are a specialty coffee shop called Fresh E2E Café. "
                "Our main goal is to showcase our menu and atmosphere, explain "
                "what makes our coffee special, and encourage people to visit the shop."
            ),
        })
        client.post(f"/api/v1/business-discovery/approve/{pid}")
        assert client.post(f"/api/v1/website-strategy/generate?project_id={pid}").status_code == 201
        assert client.post(f"/api/v1/website-strategy/{pid}/approve").status_code == 200
        assert client.post(f"/api/v1/brand-design/generate?project_id={pid}").status_code == 201
        assert client.post(f"/api/v1/brand-design/{pid}/approve").status_code == 200
        assert client.post(f"/api/v1/website-specification/generate?project_id={pid}").status_code == 201
        assert client.post(f"/api/v1/website-specification/{pid}/approve").status_code == 200

        body = client.post(f"/api/v1/website-generation/generate?project_id={pid}").json()
        assert body["validation"]["business_content_present"] is True
        files = {item["path"]: item["content"] for item in body["files"]}
        assert "Menu & Coffee" in files["app/services/page.tsx"] or "Menu highlights" in files["app/services/page.tsx"]
        assert "Coffee, food and hospitality" in files["app/page.tsx"]
        generated_text = "".join(files.values())
        assert "Hero/value proposition" not in generated_text
        assert "Proof or credibility" not in generated_text
        assert "Primary conversion section" not in generated_text
        assert "Help prospective customers understand and act on the value offered by" not in generated_text
        assert "value offered by restaurant" not in generated_text
        assert "A welcoming place for carefully prepared coffee" in generated_text
