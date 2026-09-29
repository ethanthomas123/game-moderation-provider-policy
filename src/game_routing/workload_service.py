from __future__ import annotations

from typing import Annotated, Literal

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from .infrai_routing import InfraiError, InfraiRoutingClient, RoutingTransportError


class PlayerAsset(BaseModel):
    asset_id: str
    creator_id: str
    media_kind: Literal["skin", "emblem", "voice_line"]


class LiveEvent(BaseModel):
    event_id: str
    region: str
    concurrent_players: Annotated[int, Field(ge=0)]


class ModerationQueue(BaseModel):
    queue_id: str
    pending_items: Annotated[int, Field(ge=0)]
    oldest_item_seconds: Annotated[int, Field(ge=0)]
    provider_to_exclude: str


class GameOperationsSnapshot(BaseModel):
    player_assets: list[PlayerAsset]
    live_events: list[LiveEvent]
    moderation: ModerationQueue


class AppliedModerationRoute(BaseModel):
    capability: str
    excluded_provider: str
    queue_id: str
    pending_items: int
    player_asset_count: int
    live_event_count: int
    applied: bool


def get_routing_client() -> InfraiRoutingClient:
    return InfraiRoutingClient.from_environment()


app = FastAPI(title="Game moderation provider policy")


@app.put("/game-operations/moderation-route", response_model=AppliedModerationRoute)
async def apply_moderation_route(
    snapshot: GameOperationsSnapshot,
    routing: InfraiRoutingClient = Depends(get_routing_client),
) -> AppliedModerationRoute:
    capability = "content.moderation"
    try:
        await routing.exclude_provider(
            capability,
            snapshot.moderation.provider_to_exclude,
        )
    except InfraiError as error:
        caller_status = error.status_code if 400 <= error.status_code < 500 else 502
        raise HTTPException(status_code=caller_status, detail=error.detail) from error
    except RoutingTransportError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    return AppliedModerationRoute(
        capability=capability,
        excluded_provider=snapshot.moderation.provider_to_exclude,
        queue_id=snapshot.moderation.queue_id,
        pending_items=snapshot.moderation.pending_items,
        player_asset_count=len(snapshot.player_assets),
        live_event_count=len(snapshot.live_events),
        applied=True,
    )

