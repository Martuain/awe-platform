import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.models import Project, TeamInvitation, TeamMember, TeamRole
from app.security import _hash_secret
from app.store import InMemoryRepository


@pytest.mark.asyncio
async def test_team_member_can_access_same_tenant_project_but_not_other_tenant():
    repo = InMemoryRepository()
    tenant = uuid4()
    owner = uuid4()
    member = uuid4()
    outsider = uuid4()

    await repo.add_team_member(TeamMember(user_id=owner, tenant_id=tenant, role=TeamRole.ADMIN))
    await repo.add_team_member(TeamMember(user_id=member, tenant_id=tenant, role=TeamRole.MEMBER))
    project = await repo.create_project("Shared", owner)
    other = await repo.create_project("Private", outsider)

    assert await repo.can_access_project(project.id, member, tenant)
    assert not await repo.can_access_project(other.id, member, tenant)
    assert [p.id for p in await repo.list_projects_for_user(member, tenant)] == [project.id]


@pytest.mark.asyncio
async def test_invitation_token_is_required_and_acceptance_adds_member():
    repo = InMemoryRepository()
    tenant = uuid4()
    inviter = uuid4()
    invitee = uuid4()
    raw = "awei_" + "secret-token-" + uuid4().hex
    invitation = TeamInvitation(
        tenant_id=tenant,
        inviter_id=inviter,
        email="invitee@example.com",
        role=TeamRole.MEMBER,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    await repo.create_team_invitation(invitation, _hash_secret(raw))

    with pytest.raises(KeyError):
        await repo.accept_team_invitation(invitation.id, invitee, _hash_secret("wrong"), datetime.now(timezone.utc))

    accepted = await repo.accept_team_invitation(invitation.id, invitee, _hash_secret(raw), datetime.now(timezone.utc))
    assert accepted.status == "accepted"
    assert await repo.get_team_role(tenant, invitee) == TeamRole.MEMBER
