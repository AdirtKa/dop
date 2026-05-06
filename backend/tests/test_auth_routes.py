from __future__ import annotations

import pytest

from src.routes.auth.auth import get_me


@pytest.mark.asyncio
async def test_get_me_returns_current_user(active_user) -> None:
    result = await get_me(current_user=active_user)

    assert result is active_user
    assert result.id == active_user.id
    assert result.username == active_user.username
    assert result.role == active_user.role
    assert result.is_active is active_user.is_active
