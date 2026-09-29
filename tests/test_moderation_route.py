from __future__ import annotations

import json

import httpx
from fastapi.testclient import TestClient

from game_routing.infrai_routing import InfraiRoutingClient
from game_routing.workload_service import app, get_routing_client


def test_snapshot_changes_only_the_moderation_capability() -> None:
    observed: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        observed["method"] = request.method
        observed["path"] = request.url.path
        observed["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "ok": True,
                "data": {"updated": True},
                "error": None,
                "metadata": {"request_id": "req_test"},
            },
        )

    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    routing = InfraiRoutingClient("test-key", http=http)
    app.dependency_overrides[get_routing_client] = lambda: routing
    try:
        response = TestClient(app).put(
            "/game-operations/moderation-route",
            json={
                "player_assets": [
                    {
                        "asset_id": "skin_204",
                        "creator_id": "player_17",
                        "media_kind": "skin",
                    }
                ],
                "live_events": [
                    {
                        "event_id": "arena_finals",
                        "region": "ap-southeast",
                        "concurrent_players": 8400,
                    }
                ],
                "moderation": {
                    "queue_id": "ugc_priority",
                    "pending_items": 38,
                    "oldest_item_seconds": 91,
                    "provider_to_exclude": "vendor-legacy",
                },
            },
        )
    finally:
        app.dependency_overrides.clear()
        import asyncio

        asyncio.run(http.aclose())

    assert response.status_code == 200
    assert observed == {
        "method": "PUT",
        "path": "/v1/account/routing/set",
        "body": {
            "capability": "content.moderation",
            "exclude": ["vendor-legacy"],
        },
    }
    assert response.json() == {
        "capability": "content.moderation",
        "excluded_provider": "vendor-legacy",
        "queue_id": "ugc_priority",
        "pending_items": 38,
        "player_asset_count": 1,
        "live_event_count": 1,
        "applied": True,
    }
