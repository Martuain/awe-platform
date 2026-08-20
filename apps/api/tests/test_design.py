from fastapi.testclient import TestClient
from app.main import app


def test_brand_design_requires_approved_strategy_and_is_approvable():
    with TestClient(app) as client:
        project = client.post('/api/v1/projects', json={'name': 'Design Demo'}).json()
        pid = project['id']
        assert client.post(f'/api/v1/brand-design/generate?project_id={pid}').status_code == 404

        client.post(f'/api/v1/business-discovery/start?project_id={pid}')
        client.post('/api/v1/business-discovery/message', json={'project_id': pid, 'message': 'We run a consulting business.'})
        client.post('/api/v1/business-discovery/message', json={'project_id': pid, 'message': 'Our goal is to generate leads.'})
        client.post(f'/api/v1/business-discovery/approve/{pid}')
        assert client.post(f'/api/v1/website-strategy/generate?project_id={pid}').status_code == 201
        assert client.post(f'/api/v1/website-strategy/{pid}/approve').status_code == 200

        generated = client.post(f'/api/v1/brand-design/generate?project_id={pid}')
        assert generated.status_code == 201
        body = generated.json()
        assert body['status'] == 'ready_for_review'
        assert body['source_strategy_version'] == 1
        assert body['accessibility_requirements']
        assert body['color_palette']['primary']

        approved = client.post(f'/api/v1/brand-design/{pid}/approve')
        assert approved.status_code == 200
        assert approved.json()['status'] == 'approved'
