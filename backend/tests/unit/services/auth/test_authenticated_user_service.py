"""AuthenticatedUserService 실제 DB 백킹 동작 검증."""

import uuid
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from app.models.user import User as DBUser
from app.models.user_data import AuthenticatedUser
from app.services.auth.user_data_service import (
    AuthenticatedUserService,
    _to_authenticated_user,
)


def _make_db_user(**overrides) -> DBUser:
    base = DBUser(
        id=overrides.get("id", uuid.uuid4()),
        firebase_uid=overrides.get("firebase_uid", "fb_uid_xyz"),
        email=overrides.get("email", "u@example.com"),
        full_name=overrides.get("full_name"),
        nickname=overrides.get("nickname"),
        is_active=overrides.get("is_active", True),
        created_at=overrides.get("created_at", datetime.utcnow()),
        updated_at=overrides.get("updated_at", datetime.utcnow()),
    )
    return base


class TestToAuthenticatedUser:
    def test_id_matches_db_user(self):
        uid = uuid.uuid4()
        u = _make_db_user(id=uid, full_name="홍길동")
        result = _to_authenticated_user(u)
        assert result.id == uid
        assert result.firebase_uid == "fb_uid_xyz"
        assert result.email == "u@example.com"
        assert result.display_name == "홍길동"

    def test_falls_back_to_nickname_when_no_full_name(self):
        u = _make_db_user(full_name=None, nickname="nick")
        assert _to_authenticated_user(u).display_name == "nick"

    def test_is_active_default_true_when_none(self):
        u = _make_db_user(is_active=None)
        assert _to_authenticated_user(u).is_active is True


class TestGetByFirebaseUid:
    def test_returns_none_for_empty_uid(self):
        svc = AuthenticatedUserService(db=MagicMock())
        assert svc.get_by_firebase_uid("") is None
        assert svc.get_by_firebase_uid(None) is None  # type: ignore[arg-type]

    def test_returns_dto_with_db_user_id(self, monkeypatch):
        from app.services.auth import user_data_service as mod

        target_id = uuid.uuid4()
        db_user = _make_db_user(id=target_id, firebase_uid="fb_real")

        fake_crud = MagicMock()
        fake_crud.get_by_firebase_uid.return_value = db_user
        monkeypatch.setattr(mod, "crud_user", fake_crud)

        svc = AuthenticatedUserService(db=MagicMock())
        result = svc.get_by_firebase_uid("fb_real")
        assert isinstance(result, AuthenticatedUser)
        assert result.id == target_id
        fake_crud.get_by_firebase_uid.assert_called_once()

    def test_returns_none_when_user_missing(self, monkeypatch):
        from app.services.auth import user_data_service as mod

        fake_crud = MagicMock()
        fake_crud.get_by_firebase_uid.return_value = None
        monkeypatch.setattr(mod, "crud_user", fake_crud)

        svc = AuthenticatedUserService(db=MagicMock())
        assert svc.get_by_firebase_uid("nonexistent") is None


class TestCreateFromFirebaseAuth:
    def test_idempotent_returns_same_id(self, monkeypatch):
        from app.services.auth import user_data_service as mod

        target_id = uuid.uuid4()
        db_user = _make_db_user(id=target_id)

        fake_crud = MagicMock()
        fake_crud.get_or_create_by_firebase_uid.return_value = db_user
        monkeypatch.setattr(mod, "crud_user", fake_crud)

        svc = AuthenticatedUserService(db=MagicMock())
        r1 = svc.create_from_firebase_auth(
            firebase_uid="fb1", email="a@b.com", display_name="X"
        )
        r2 = svc.create_from_firebase_auth(
            firebase_uid="fb1", email="a@b.com", display_name="X"
        )
        assert r1.id == r2.id == target_id

    def test_fills_full_name_when_empty(self, monkeypatch):
        from app.services.auth import user_data_service as mod

        db_user = _make_db_user(full_name=None)
        fake_crud = MagicMock()
        fake_crud.get_or_create_by_firebase_uid.return_value = db_user
        monkeypatch.setattr(mod, "crud_user", fake_crud)

        mock_db = MagicMock()
        svc = AuthenticatedUserService(db=mock_db)
        svc.create_from_firebase_auth(
            firebase_uid="fb1", email="a@b.com", display_name="새이름"
        )
        assert db_user.full_name == "새이름"
        mock_db.commit.assert_called()


class TestUpdateProfile:
    def test_invalid_uuid_raises(self, monkeypatch):
        svc = AuthenticatedUserService(db=MagicMock())
        with pytest.raises(ValueError, match="Invalid user_id"):
            svc.update_profile("not-a-uuid", {"display_name": "x"})

    def test_user_not_found_raises(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        svc = AuthenticatedUserService(db=mock_db)
        with pytest.raises(ValueError, match="User not found"):
            svc.update_profile(str(uuid.uuid4()), {"display_name": "x"})

    def test_maps_display_name_to_full_name(self):
        target_id = uuid.uuid4()
        db_user = _make_db_user(id=target_id, full_name="old")
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = db_user

        svc = AuthenticatedUserService(db=mock_db)
        result = svc.update_profile(str(target_id), {"display_name": "new"})

        assert db_user.full_name == "new"
        assert result.display_name == "new"
        mock_db.commit.assert_called()


class TestDeactivateUser:
    def test_sets_is_active_false(self):
        target_id = uuid.uuid4()
        db_user = _make_db_user(id=target_id, is_active=True)
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = db_user

        svc = AuthenticatedUserService(db=mock_db)
        result = svc.deactivate_user(str(target_id))
        assert db_user.is_active is False
        assert result.is_active is False
        mock_db.commit.assert_called()
