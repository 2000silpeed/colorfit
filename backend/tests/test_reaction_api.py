import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _mock_reaction(reaction_id=1, user_id=None, outfit_id="outfit_1", reaction_type="save"):
    r = MagicMock()
    r.id = reaction_id
    r.user_id = user_id or uuid.uuid4()
    r.outfit_id = outfit_id
    r.reaction_type = reaction_type
    return r


@pytest.fixture
def mock_db():
    session = AsyncMock()
    return session


class TestReactionValidation:
    def test_invalid_reaction_type(self):
        resp = client.post("/api/reaction", json={
            "user_id": str(uuid.uuid4()),
            "outfit_id": "o1",
            "reaction_type": "love",
        })
        assert resp.status_code == 422

    def test_missing_user_id(self):
        resp = client.post("/api/reaction", json={
            "outfit_id": "o1",
            "reaction_type": "save",
        })
        assert resp.status_code == 422

    def test_missing_outfit_id(self):
        resp = client.post("/api/reaction", json={
            "user_id": str(uuid.uuid4()),
            "reaction_type": "save",
        })
        assert resp.status_code == 422

    def test_save_type_accepted(self):
        from app.schemas.reaction import ReactionRequest
        req = ReactionRequest(user_id="abc", outfit_id="o1", reaction_type="save")
        assert req.reaction_type == "save"

    def test_dislike_type_accepted(self):
        from app.schemas.reaction import ReactionRequest
        req = ReactionRequest(user_id="abc", outfit_id="o1", reaction_type="dislike")
        assert req.reaction_type == "dislike"
