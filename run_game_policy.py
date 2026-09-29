from __future__ import annotations

import asyncio
import json

from game_routing.infrai_routing import InfraiRoutingClient
from game_routing.workload_service import GameOperationsSnapshot


EXAMPLE = {
    "player_assets": [
        {"asset_id": "skin_204", "creator_id": "player_17", "media_kind": "skin"}
    ],
    "live_events": [
        {"event_id": "arena_finals", "region": "ap-southeast", "concurrent_players": 8400}
    ],
    "moderation": {
        "queue_id": "ugc_priority",
        "pending_items": 38,
        "oldest_item_seconds": 91,
        "provider_to_exclude": "vendor-legacy",
    },
}


async def main() -> None:
    snapshot = GameOperationsSnapshot.model_validate(EXAMPLE)
    client = InfraiRoutingClient.from_environment()
    try:
        await client.exclude_provider(
            "content.moderation",
            snapshot.moderation.provider_to_exclude,
        )
    finally:
        await client.close()

    print(
        json.dumps(
            {
                "queue_id": snapshot.moderation.queue_id,
                "capability": "content.moderation",
                "excluded_provider": snapshot.moderation.provider_to_exclude,
                "applied": True,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())

