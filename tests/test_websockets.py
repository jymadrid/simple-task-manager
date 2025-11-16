"""Tests for WebSocket functionality."""

import pytest
from fastapi import WebSocket

from taskforge.api.websockets import ConnectionManager


@pytest.mark.asyncio
async def test_connection_manager_init():
    """Test ConnectionManager initialization."""
    manager = ConnectionManager()
    assert manager.active_connections == []
    assert isinstance(manager.active_connections, list)


@pytest.mark.asyncio
async def test_connection_manager_broadcast():
    """Test ConnectionManager broadcast with no connections."""
    manager = ConnectionManager()
    # Should not raise error when broadcasting to empty list
    await manager.broadcast("test message")
    assert len(manager.active_connections) == 0
