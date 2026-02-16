"""Unit tests for auth state management.

Tests for get_auth_state, set_auth_state, subscribe_to_auth_changes,
_make_unauthenticated_state, and _notify_listeners. All file storage
tests use the ``tmp_path`` pytest fixture for isolation (no writes to
~/.config).

Issue: #116
"""

from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from auth.auth_state import (
    _listeners,
    _make_unauthenticated_state,
    _notify_listeners,
    get_auth_state,
    set_auth_state,
    subscribe_to_auth_changes,
)
from auth.token_manager import (
    clear_tokens,
    get_stored_tokens,
    store_tokens,
)
from auth.types import AuthState, LinkedInTokens, UserProfile


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clean_listeners():
    """Ensure auth state listeners are cleared between tests."""
    _listeners.clear()
    yield
    _listeners.clear()


@pytest.fixture()
def valid_tokens() -> LinkedInTokens:
    """Return a valid (non-expired) token set."""
    return LinkedInTokens(
        access_token="valid-access-token-abc123",
        expires_at=int(time.time()) + 86400 * 30,  # 30 days from now
        refresh_token="valid-refresh-token-xyz789",
    )


@pytest.fixture()
def expired_tokens() -> LinkedInTokens:
    """Return an expired token set (expired 1 hour ago)."""
    return LinkedInTokens(
        access_token="expired-access-token",
        expires_at=int(time.time()) - 3600,
        refresh_token="refresh-for-expired",
    )


@pytest.fixture()
def sample_user_profile() -> UserProfile:
    """Return a sample user profile."""
    return UserProfile(
        linkedin_id="linkedin-member-12345",
        email="test@example.com",
        display_name="Test User",
        profile_picture="https://media.licdn.com/photo.jpg",
    )


@pytest.fixture()
def authenticated_state(valid_tokens, sample_user_profile) -> AuthState:
    """Return an authenticated AuthState with user profile and tokens."""
    return AuthState(
        is_authenticated=True,
        user=sample_user_profile,
        tokens=valid_tokens,
        last_validated=int(time.time()),
    )


@pytest.fixture()
def unauthenticated_state() -> AuthState:
    """Return an unauthenticated AuthState."""
    return AuthState(
        is_authenticated=False,
        user=None,
        tokens=None,
        last_validated=0,
    )


# ---------------------------------------------------------------------------
# _make_unauthenticated_state
# ---------------------------------------------------------------------------


class TestMakeUnauthenticatedState:
    """Tests for _make_unauthenticated_state() helper."""

    def test_returns_unauthenticated(self):
        """Returns state with is_authenticated=False."""
        state = _make_unauthenticated_state()
        assert state["is_authenticated"] is False

    def test_user_is_none(self):
        """Returns state with user=None."""
        state = _make_unauthenticated_state()
        assert state["user"] is None

    def test_tokens_is_none(self):
        """Returns state with tokens=None."""
        state = _make_unauthenticated_state()
        assert state["tokens"] is None

    def test_last_validated_is_zero(self):
        """Returns state with last_validated=0."""
        state = _make_unauthenticated_state()
        assert state["last_validated"] == 0

    def test_returns_all_required_keys(self):
        """Returned state contains all AuthState keys."""
        state = _make_unauthenticated_state()
        assert "is_authenticated" in state
        assert "user" in state
        assert "tokens" in state
        assert "last_validated" in state

    def test_returns_new_dict_each_call(self):
        """Each call returns a distinct dict (no shared mutable state)."""
        state1 = _make_unauthenticated_state()
        state2 = _make_unauthenticated_state()
        assert state1 is not state2


# ---------------------------------------------------------------------------
# get_auth_state — unauthenticated scenarios
# ---------------------------------------------------------------------------


class TestGetAuthStateUnauthenticated:
    """Tests for get_auth_state() when no tokens are stored."""

    def test_unauthenticated_when_no_tokens(self, tmp_path):
        """get_auth_state returns unauthenticated when no tokens stored."""
        storage = tmp_path / "tokens.json"
        state = get_auth_state(storage_path=storage)

        assert state["is_authenticated"] is False
        assert state["user"] is None
        assert state["tokens"] is None

    def test_unauthenticated_when_file_missing(self, tmp_path):
        """get_auth_state returns unauthenticated when storage file does not exist."""
        storage = tmp_path / "nonexistent" / "tokens.json"
        state = get_auth_state(storage_path=storage)

        assert state["is_authenticated"] is False

    def test_unauthenticated_when_storage_corrupted(self, tmp_path):
        """Scenario 110: Corrupted storage falls back to unauthenticated (no crash)."""
        storage = tmp_path / "tokens.json"
        storage.write_text("this is definitely not encrypted token data")

        state = get_auth_state(storage_path=storage)

        assert state["is_authenticated"] is False
        assert state["tokens"] is None

    def test_last_validated_is_zero_when_unauthenticated(self, tmp_path):
        """last_validated is 0 when unauthenticated."""
        storage = tmp_path / "tokens.json"
        state = get_auth_state(storage_path=storage)

        assert state["last_validated"] == 0


# ---------------------------------------------------------------------------
# get_auth_state — authenticated scenarios
# ---------------------------------------------------------------------------


class TestGetAuthStateAuthenticated:
    """Tests for get_auth_state() when valid tokens are stored."""

    def test_authenticated_when_valid_tokens_stored(self, tmp_path, valid_tokens):
        """get_auth_state returns authenticated when valid tokens exist."""
        storage = tmp_path / "tokens.json"
        store_tokens(valid_tokens, storage_path=storage)

        state = get_auth_state(storage_path=storage)

        assert state["is_authenticated"] is True
        assert state["tokens"] is not None
        assert state["tokens"]["access_token"] == valid_tokens["access_token"]

    def test_user_is_none_from_get_auth_state(self, tmp_path, valid_tokens):
        """get_auth_state does not populate user profile (caller's responsibility)."""
        storage = tmp_path / "tokens.json"
        store_tokens(valid_tokens, storage_path=storage)

        state = get_auth_state(storage_path=storage)

        # User profile is set by caller after backend validation
        assert state["user"] is None

    def test_tokens_match_stored(self, tmp_path, valid_tokens):
        """Tokens in auth state match what was stored."""
        storage = tmp_path / "tokens.json"
        store_tokens(valid_tokens, storage_path=storage)

        state = get_auth_state(storage_path=storage)

        assert state["tokens"]["access_token"] == valid_tokens["access_token"]
        assert state["tokens"]["expires_at"] == valid_tokens["expires_at"]
        assert state["tokens"]["refresh_token"] == valid_tokens["refresh_token"]

    def test_authenticated_with_expired_tokens(self, tmp_path, expired_tokens):
        """get_auth_state returns authenticated even with expired tokens (local check only)."""
        storage = tmp_path / "tokens.json"
        store_tokens(expired_tokens, storage_path=storage)

        state = get_auth_state(storage_path=storage)

        # get_auth_state only checks if tokens exist, not validity
        assert state["is_authenticated"] is True
        assert state["tokens"] is not None

    def test_uses_default_path_when_none(self):
        """get_auth_state uses default storage path when storage_path is None."""
        with patch("auth.auth_state.get_stored_tokens") as mock_get:
            mock_get.return_value = None

            get_auth_state(storage_path=None)

            mock_get.assert_called_once_with(storage_path=None)


# ---------------------------------------------------------------------------
# set_auth_state — persistence
# ---------------------------------------------------------------------------


class TestSetAuthState:
    """Tests for set_auth_state() persistence behavior."""

    def test_set_auth_state_persists_tokens(self, tmp_path, valid_tokens):
        """set_auth_state persists tokens to disk when authenticated."""
        storage = tmp_path / "tokens.json"

        state = AuthState(
            is_authenticated=True,
            user=None,
            tokens=valid_tokens,
            last_validated=int(time.time()),
        )
        set_auth_state(state, storage_path=storage)

        retrieved = get_stored_tokens(storage_path=storage)
        assert retrieved is not None
        assert retrieved["access_token"] == valid_tokens["access_token"]

    def test_set_auth_state_with_user_profile(
        self, tmp_path, valid_tokens, sample_user_profile
    ):
        """set_auth_state with user profile persists tokens."""
        storage = tmp_path / "tokens.json"

        state = AuthState(
            is_authenticated=True,
            user=sample_user_profile,
            tokens=valid_tokens,
            last_validated=int(time.time()),
        )
        set_auth_state(state, storage_path=storage)

        retrieved = get_stored_tokens(storage_path=storage)
        assert retrieved is not None
        assert retrieved["access_token"] == valid_tokens["access_token"]

    def test_set_unauthenticated_state_does_not_persist(self, tmp_path):
        """set_auth_state with unauthenticated state does not write tokens."""
        storage = tmp_path / "tokens.json"

        state = AuthState(
            is_authenticated=False,
            user=None,
            tokens=None,
            last_validated=0,
        )
        set_auth_state(state, storage_path=storage)

        assert not storage.exists()
        assert get_stored_tokens(storage_path=storage) is None

    def test_set_auth_state_does_not_clear_on_unauthenticated(
        self, tmp_path, valid_tokens
    ):
        """set_auth_state with unauthenticated state does not clear existing tokens."""
        storage = tmp_path / "tokens.json"
        store_tokens(valid_tokens, storage_path=storage)

        state = AuthState(
            is_authenticated=False,
            user=None,
            tokens=None,
            last_validated=0,
        )
        set_auth_state(state, storage_path=storage)

        # Tokens should still be on disk (use clear_tokens for logout)
        assert get_stored_tokens(storage_path=storage) is not None

    def test_set_auth_state_overwrites_existing_tokens(
        self, tmp_path, valid_tokens
    ):
        """set_auth_state overwrites previously stored tokens."""
        storage = tmp_path / "tokens.json"
        store_tokens(valid_tokens, storage_path=storage)

        new_tokens = LinkedInTokens(
            access_token="updated-access-token",
            expires_at=int(time.time()) + 86400 * 60,
            refresh_token="updated-refresh-token",
        )
        state = AuthState(
            is_authenticated=True,
            user=None,
            tokens=new_tokens,
            last_validated=int(time.time()),
        )
        set_auth_state(state, storage_path=storage)

        retrieved = get_stored_tokens(storage_path=storage)
        assert retrieved is not None
        assert retrieved["access_token"] == "updated-access-token"

    def test_set_auth_state_uses_default_path_when_none(self, valid_tokens):
        """set_auth_state uses default storage path when storage_path is None."""
        state = AuthState(
            is_authenticated=True,
            user=None,
            tokens=valid_tokens,
            last_validated=int(time.time()),
        )

        with patch("auth.auth_state.store_tokens") as mock_store:
            set_auth_state(state, storage_path=None)

            mock_store.assert_called_once_with(
                valid_tokens, storage_path=None
            )

    def test_set_authenticated_state_without_tokens_no_persist(self, tmp_path):
        """set_auth_state with is_authenticated=True but tokens=None does not persist."""
        storage = tmp_path / "tokens.json"

        state = AuthState(
            is_authenticated=True,
            user=None,
            tokens=None,
            last_validated=0,
        )
        set_auth_state(state, storage_path=storage)

        assert not storage.exists()


# ---------------------------------------------------------------------------
# T100 / Scenario 100 — subscribe_to_auth_changes and notifications
# ---------------------------------------------------------------------------


class TestSubscribeToAuthChanges:
    """Tests for subscribe_to_auth_changes() and the observer pattern."""

    def test_t100_auth_state_notifies_listeners(self, tmp_path, valid_tokens):
        """T100: Subscribers receive state updates."""
        storage = tmp_path / "tokens.json"
        received_states: list[AuthState] = []

        subscribe_to_auth_changes(lambda s: received_states.append(s))

        state = AuthState(
            is_authenticated=True,
            user=UserProfile(
                linkedin_id="sub-123",
                email="test@example.com",
                display_name="Test User",
                profile_picture=None,
            ),
            tokens=valid_tokens,
            last_validated=int(time.time()),
        )
        set_auth_state(state, storage_path=storage)

        assert len(received_states) == 1
        assert received_states[0]["is_authenticated"] is True
        assert received_states[0]["user"]["email"] == "test@example.com"

    def test_100_state_change_notification(self, tmp_path, valid_tokens):
        """Scenario 100: Login completion triggers listener callback."""
        storage = tmp_path / "tokens.json"
        callback_count = 0

        def on_change(state: AuthState) -> None:
            nonlocal callback_count
            callback_count += 1

        subscribe_to_auth_changes(on_change)

        state = AuthState(
            is_authenticated=True,
            user=None,
            tokens=valid_tokens,
            last_validated=int(time.time()),
        )
        set_auth_state(state, storage_path=storage)

        assert callback_count == 1

    def test_subscribe_returns_unsubscribe_callable(self):
        """subscribe_to_auth_changes returns a callable unsubscribe function."""
        unsub = subscribe_to_auth_changes(lambda s: None)
        assert callable(unsub)

    def test_unsubscribe_stops_notifications(self, tmp_path, valid_tokens):
        """Unsubscribed listeners do not receive further updates."""
        storage = tmp_path / "tokens.json"
        received: list[AuthState] = []

        unsub = subscribe_to_auth_changes(lambda s: received.append(s))

        state = AuthState(
            is_authenticated=True,
            user=None,
            tokens=valid_tokens,
            last_validated=int(time.time()),
        )
        set_auth_state(state, storage_path=storage)
        assert len(received) == 1

        unsub()

        set_auth_state(state, storage_path=storage)
        assert len(received) == 1  # Still 1 — unsubscribed

    def test_unsubscribe_is_idempotent(self, tmp_path, valid_tokens):
        """Calling unsubscribe multiple times does not raise."""
        unsub = subscribe_to_auth_changes(lambda s: None)

        unsub()
        unsub()  # Second call should not raise

    def test_multiple_listeners_all_notified(self, tmp_path, valid_tokens):
        """All subscribed listeners receive the state change."""
        storage = tmp_path / "tokens.json"
        results = {"a": 0, "b": 0}

        subscribe_to_auth_changes(
            lambda s: results.update(a=results["a"] + 1)
        )
        subscribe_to_auth_changes(
            lambda s: results.update(b=results["b"] + 1)
        )

        state = AuthState(
            is_authenticated=True,
            user=None,
            tokens=valid_tokens,
            last_validated=0,
        )
        set_auth_state(state, storage_path=storage)

        assert results["a"] == 1
        assert results["b"] == 1

    def test_listener_exception_does_not_block_others(
        self, tmp_path, valid_tokens
    ):
        """A failing listener does not prevent other listeners from running."""
        storage = tmp_path / "tokens.json"
        reached = []

        def bad_listener(s: AuthState) -> None:
            raise RuntimeError("boom")

        def good_listener(s: AuthState) -> None:
            reached.append(True)

        subscribe_to_auth_changes(bad_listener)
        subscribe_to_auth_changes(good_listener)

        state = AuthState(
            is_authenticated=True,
            user=None,
            tokens=valid_tokens,
            last_validated=0,
        )
        set_auth_state(state, storage_path=storage)

        assert len(reached) == 1  # good_listener was called despite bad_listener

    def test_listener_receives_correct_state(
        self, tmp_path, valid_tokens, sample_user_profile
    ):
        """Listener receives the exact state that was set."""
        storage = tmp_path / "tokens.json"
        received_states: list[AuthState] = []

        subscribe_to_auth_changes(lambda s: received_states.append(s))

        state = AuthState(
            is_authenticated=True,
            user=sample_user_profile,
            tokens=valid_tokens,
            last_validated=1700000000,
        )
        set_auth_state(state, storage_path=storage)

        assert len(received_states) == 1
        assert received_states[0]["is_authenticated"] is True
        assert received_states[0]["user"]["linkedin_id"] == "linkedin-member-12345"
        assert received_states[0]["user"]["display_name"] == "Test User"
        assert received_states[0]["tokens"]["access_token"] == valid_tokens["access_token"]
        assert received_states[0]["last_validated"] == 1700000000

    def test_listeners_notified_on_unauthenticated_state(self, tmp_path):
        """Listeners are notified even when setting unauthenticated state."""
        storage = tmp_path / "tokens.json"
        received_states: list[AuthState] = []

        subscribe_to_auth_changes(lambda s: received_states.append(s))

        state = AuthState(
            is_authenticated=False,
            user=None,
            tokens=None,
            last_validated=0,
        )
        set_auth_state(state, storage_path=storage)

        assert len(received_states) == 1
        assert received_states[0]["is_authenticated"] is False

    def test_multiple_set_calls_trigger_multiple_notifications(
        self, tmp_path, valid_tokens
    ):
        """Each set_auth_state call triggers a notification."""
        storage = tmp_path / "tokens.json"
        call_count = 0

        def counter(s: AuthState) -> None:
            nonlocal call_count
            call_count += 1

        subscribe_to_auth_changes(counter)

        state = AuthState(
            is_authenticated=True,
            user=None,
            tokens=valid_tokens,
            last_validated=0,
        )
        set_auth_state(state, storage_path=storage)
        set_auth_state(state, storage_path=storage)
        set_auth_state(state, storage_path=storage)

        assert call_count == 3

    def test_no_listeners_does_not_raise(self, tmp_path, valid_tokens):
        """set_auth_state with no listeners registered does not raise."""
        storage = tmp_path / "tokens.json"

        state = AuthState(
            is_authenticated=True,
            user=None,
            tokens=valid_tokens,
            last_validated=0,
        )
        # Should not raise even with no listeners
        set_auth_state(state, storage_path=storage)


# ---------------------------------------------------------------------------
# _notify_listeners
# ---------------------------------------------------------------------------


class TestNotifyListeners:
    """Tests for _notify_listeners() internal function."""

    def test_notifies_all_registered_listeners(self, valid_tokens):
        """All registered listeners are invoked."""
        results = []

        _listeners.append(lambda s: results.append("a"))
        _listeners.append(lambda s: results.append("b"))
        _listeners.append(lambda s: results.append("c"))

        state = AuthState(
            is_authenticated=True,
            user=None,
            tokens=valid_tokens,
            last_validated=0,
        )
        _notify_listeners(state)

        assert results == ["a", "b", "c"]

    def test_exception_in_listener_logged_not_raised(self, valid_tokens):
        """Exceptions in listeners are caught (not propagated)."""
        reached = []

        def failing(s: AuthState) -> None:
            raise ValueError("test error")

        def succeeding(s: AuthState) -> None:
            reached.append(True)

        _listeners.append(failing)
        _listeners.append(succeeding)

        state = AuthState(
            is_authenticated=True,
            user=None,
            tokens=valid_tokens,
            last_validated=0,
        )
        # Should not raise
        _notify_listeners(state)

        assert len(reached) == 1

    def test_empty_listeners_is_noop(self):
        """No listeners registered — _notify_listeners is a no-op."""
        state = AuthState(
            is_authenticated=False,
            user=None,
            tokens=None,
            last_validated=0,
        )
        # Should not raise
        _notify_listeners(state)

    def test_listener_modification_during_iteration_safe(self, valid_tokens):
        """Modifying the listener list during notification does not crash."""
        results = []

        def self_removing_listener(s: AuthState) -> None:
            results.append("removed")
            # Attempt to remove self during iteration
            try:
                _listeners.remove(self_removing_listener)
            except ValueError:
                pass

        def normal_listener(s: AuthState) -> None:
            results.append("normal")

        _listeners.append(self_removing_listener)
        _listeners.append(normal_listener)

        state = AuthState(
            is_authenticated=True,
            user=None,
            tokens=valid_tokens,
            last_validated=0,
        )
        # _notify_listeners iterates over a copy, so this should be safe
        _notify_listeners(state)

        assert "removed" in results
        assert "normal" in results


# ---------------------------------------------------------------------------
# Scenario 060 — Logout clears state
# ---------------------------------------------------------------------------


class TestLogoutClearsAuthState:
    """Tests that logout (clear_tokens) results in unauthenticated state."""

    def test_060_logout_clears_state(self, tmp_path, valid_tokens):
        """Scenario 060: Logout clears all data, auth state resets."""
        storage = tmp_path / "tokens.json"
        store_tokens(valid_tokens, storage_path=storage)

        # Verify authenticated
        state = get_auth_state(storage_path=storage)
        assert state["is_authenticated"] is True

        # Logout
        clear_tokens(storage_path=storage)

        # Verify unauthenticated
        state = get_auth_state(storage_path=storage)
        assert state["is_authenticated"] is False
        assert state["tokens"] is None

    def test_logout_then_reauth(self, tmp_path, valid_tokens):
        """After logout and re-storing tokens, state is authenticated again."""
        storage = tmp_path / "tokens.json"
        store_tokens(valid_tokens, storage_path=storage)
        clear_tokens(storage_path=storage)

        assert get_auth_state(storage_path=storage)["is_authenticated"] is False

        # Re-authenticate
        new_tokens = LinkedInTokens(
            access_token="new-access-after-logout",
            expires_at=int(time.time()) + 86400,
            refresh_token="new-refresh",
        )
        store_tokens(new_tokens, storage_path=storage)

        state = get_auth_state(storage_path=storage)
        assert state["is_authenticated"] is True
        assert state["tokens"]["access_token"] == "new-access-after-logout"


# ---------------------------------------------------------------------------
# Integration: set_auth_state -> get_auth_state round-trip
# ---------------------------------------------------------------------------


class TestAuthStateRoundTrip:
    """Integration tests for set/get auth state round-trip."""

    def test_set_then_get_returns_authenticated(self, tmp_path, valid_tokens):
        """Setting authenticated state then getting returns authenticated."""
        storage = tmp_path / "tokens.json"

        state = AuthState(
            is_authenticated=True,
            user=None,
            tokens=valid_tokens,
            last_validated=int(time.time()),
        )
        set_auth_state(state, storage_path=storage)

        retrieved = get_auth_state(storage_path=storage)
        assert retrieved["is_authenticated"] is True
        assert retrieved["tokens"]["access_token"] == valid_tokens["access_token"]

    def test_set_then_get_preserves_token_values(self, tmp_path):
        """All token fields are preserved through set/get cycle."""
        storage = tmp_path / "tokens.json"

        tokens = LinkedInTokens(
            access_token="roundtrip-token",
            expires_at=1700000000,
            refresh_token="roundtrip-refresh",
        )
        state = AuthState(
            is_authenticated=True,
            user=None,
            tokens=tokens,
            last_validated=int(time.time()),
        )
        set_auth_state(state, storage_path=storage)

        retrieved = get_auth_state(storage_path=storage)
        assert retrieved["tokens"]["access_token"] == "roundtrip-token"
        assert retrieved["tokens"]["expires_at"] == 1700000000
        assert retrieved["tokens"]["refresh_token"] == "roundtrip-refresh"

    def test_set_authenticated_get_user_is_none(
        self, tmp_path, valid_tokens, sample_user_profile
    ):
        """get_auth_state does not return user profile (it's not persisted)."""
        storage = tmp_path / "tokens.json"

        state = AuthState(
            is_authenticated=True,
            user=sample_user_profile,
            tokens=valid_tokens,
            last_validated=int(time.time()),
        )
        set_auth_state(state, storage_path=storage)

        # User profile is NOT persisted to the token file
        retrieved = get_auth_state(storage_path=storage)
        assert retrieved["user"] is None

    def test_set_with_notification_then_get(
        self, tmp_path, valid_tokens
    ):
        """set_auth_state triggers listener AND persists; get reads persisted state."""
        storage = tmp_path / "tokens.json"
        notified = []

        subscribe_to_auth_changes(lambda s: notified.append(s))

        state = AuthState(
            is_authenticated=True,
            user=None,
            tokens=valid_tokens,
            last_validated=0,
        )
        set_auth_state(state, storage_path=storage)

        # Listener was notified
        assert len(notified) == 1
        assert notified[0]["is_authenticated"] is True

        # Persisted state is readable
        retrieved = get_auth_state(storage_path=storage)
        assert retrieved["is_authenticated"] is True


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestAuthStateEdgeCases:
    """Edge case tests for auth state management."""

    def test_get_auth_state_with_tokens_without_refresh(self, tmp_path):
        """Auth state works with tokens that have no refresh token."""
        storage = tmp_path / "tokens.json"
        tokens = LinkedInTokens(
            access_token="no-refresh",
            expires_at=int(time.time()) + 86400,
            refresh_token=None,
        )
        store_tokens(tokens, storage_path=storage)

        state = get_auth_state(storage_path=storage)
        assert state["is_authenticated"] is True
        assert state["tokens"]["refresh_token"] is None

    def test_set_auth_state_tokens_none_authenticated_true(self, tmp_path):
        """Authenticated state with tokens=None does not crash."""
        storage = tmp_path / "tokens.json"

        state = AuthState(
            is_authenticated=True,
            user=None,
            tokens=None,
            last_validated=0,
        )
        # Should not raise
        set_auth_state(state, storage_path=storage)

    def test_concurrent_subscribe_unsubscribe(self, tmp_path, valid_tokens):
        """Subscribe, notify, unsubscribe, subscribe again works correctly."""
        storage = tmp_path / "tokens.json"
        results_a: list[AuthState] = []
        results_b: list[AuthState] = []

        unsub_a = subscribe_to_auth_changes(lambda s: results_a.append(s))

        state = AuthState(
            is_authenticated=True,
            user=None,
            tokens=valid_tokens,
            last_validated=0,
        )
        set_auth_state(state, storage_path=storage)
        assert len(results_a) == 1

        unsub_a()

        unsub_b = subscribe_to_auth_changes(lambda s: results_b.append(s))
        set_auth_state(state, storage_path=storage)

        assert len(results_a) == 1  # A no longer notified
        assert len(results_b) == 1  # B was notified

        unsub_b()

    def test_listener_list_is_module_level(self):
        """_listeners is the module-level list used by subscribe/notify."""
        initial_len = len(_listeners)
        unsub = subscribe_to_auth_changes(lambda s: None)
        assert len(_listeners) == initial_len + 1
        unsub()
        assert len(_listeners) == initial_len
