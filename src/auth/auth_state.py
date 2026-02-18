"""Auth state management and event emitter.

Provides functions to read, update, and observe the current authentication
state of the CLI session. Implements the observer pattern so that
interested components can subscribe to auth-state changes and react
accordingly (e.g. update UI indicators, gate features).

The authentication state is derived from stored tokens (managed by
:mod:`auth.token_manager`). User-profile information is *not* persisted
to disk — it is populated by the caller after backend validation and
only lives in memory for the duration of the session.

Issue: #116
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Optional

from .token_manager import get_stored_tokens, store_tokens
from .types import AuthState

logger = logging.getLogger(__name__)

# Module-level listener list for the observer pattern.
# Each entry is a callback ``(AuthState) -> None``.
_listeners: list[Callable[[AuthState], None]] = []


def _make_unauthenticated_state() -> AuthState:
    """Return a fresh unauthenticated :class:`AuthState`.

    Returns a new dictionary on every call so callers can mutate it
    without affecting other references.

    Returns:
        An :class:`AuthState` with ``is_authenticated=False``,
        ``user=None``, ``tokens=None``, and ``last_validated=0``.
    """
    return AuthState(
        is_authenticated=False,
        user=None,
        tokens=None,
        last_validated=0,
    )


def get_auth_state(storage_path: Optional[Path] = None) -> AuthState:
    """Return the current authentication state.

    Reads stored tokens from disk via :func:`auth.token_manager.get_stored_tokens`.
    If valid tokens are found the state is ``is_authenticated=True``; otherwise
    the state is unauthenticated.

    .. note::
        The ``user`` field is always ``None`` in the returned state because
        user-profile information is not persisted to the token file. The
        caller is responsible for populating ``user`` after backend validation.

    Args:
        storage_path: Path to the token storage file. Passed through to
            :func:`~auth.token_manager.get_stored_tokens`. When ``None``,
            the default storage path is used.

    Returns:
        The current :class:`AuthState`.
    """
    tokens = get_stored_tokens(storage_path=storage_path)

    if tokens is None:
        return _make_unauthenticated_state()

    return AuthState(
        is_authenticated=True,
        user=None,
        tokens=tokens,
        last_validated=0,
    )


def set_auth_state(state: AuthState, storage_path: Optional[Path] = None) -> None:
    """Update the auth state, persist tokens if present, and notify listeners.

    When the provided state contains tokens (``state["tokens"]`` is not
    ``None``), they are persisted to disk via
    :func:`auth.token_manager.store_tokens`. If ``tokens`` is ``None``,
    nothing is written (use :func:`auth.token_manager.clear_tokens` for
    explicit logout).

    After persisting, all registered listeners are notified of the new
    state via :func:`_notify_listeners`.

    Args:
        state: The new :class:`AuthState` to set.
        storage_path: Path to the token storage file. Passed through to
            :func:`~auth.token_manager.store_tokens`. When ``None``, the
            default storage path is used.
    """
    if state["tokens"] is not None:
        store_tokens(state["tokens"], storage_path=storage_path)

    _notify_listeners(state)


def subscribe_to_auth_changes(
    callback: Callable[[AuthState], None],
) -> Callable[[], None]:
    """Subscribe to auth-state changes.

    The *callback* is invoked every time :func:`set_auth_state` is called,
    receiving the new :class:`AuthState` as its sole argument.

    Args:
        callback: A callable ``(AuthState) -> None`` to be invoked on
            each state change.

    Returns:
        An *unsubscribe* function. Calling it removes *callback* from
        the listener list. The unsubscribe function is idempotent — calling
        it multiple times is safe.
    """
    _listeners.append(callback)

    def unsubscribe() -> None:
        try:
            _listeners.remove(callback)
        except ValueError:
            # Already removed — idempotent
            pass

    return unsubscribe


def _notify_listeners(state: AuthState) -> None:
    """Invoke all registered listeners with the given state.

    Iterates over a *snapshot* of the listener list so that listeners
    may safely add or remove entries during iteration. Exceptions raised
    by individual listeners are caught and logged so that a failing
    listener does not prevent others from being notified.

    Args:
        state: The :class:`AuthState` to broadcast.
    """
    for listener in list(_listeners):
        try:
            listener(state)
        except Exception:
            logger.exception("Auth-state listener raised an exception")
