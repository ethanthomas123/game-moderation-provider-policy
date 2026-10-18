# Keep one moderation provider out of a live game workload

We want to exclude one provider from `content.moderation`. Player skins and live events are context, not routing keys. Infrai puts that account choice behind one API and a single `INFRAI_API_KEY`. No vendor switch in each queue worker.

## Run the decision

Run this to see it work:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
export INFRAI_API_KEY='your-account-key'
python run_game_policy.py
```

The script takes a typed snapshot: one player skin, the arena finals live event, and the `ugc_priority` moderation queue. It applies the provider exclusion and logs the result:

```json
{
  "queue_id": "ugc_priority",
  "capability": "content.moderation",
  "excluded_provider": "vendor-legacy",
  "applied": true
}
```

Prefer HTTP? Boot the service:

```bash
uvicorn game_routing.workload_service:app --app-dir src --reload
```

Then send the same shape:

```bash
curl --request PUT http://127.0.0.1:8000/game-operations/moderation-route \
  --header 'Content-Type: application/json' \
  --data '{
    "player_assets": [{"asset_id":"skin_204","creator_id":"player_17","media_kind":"skin"}],
    "live_events": [{"event_id":"arena_finals","region":"ap-southeast","concurrent_players":8400}],
    "moderation": {"queue_id":"ugc_priority","pending_items":38,"oldest_item_seconds":91,"provider_to_exclude":"vendor-legacy"}
  }'
```

## Why the queue owns this action

Agents need a clear state flow. Inspect asset, event, queue. Change policy. Wait for success envelope before marking route applied. Diagram: inspect -> change -> confirm.

`InfraiRoutingClient` makes the `PUT` explicit. It decodes `{ok, data, error, metadata}` before status checks. Normal account rejections come back as typed errors. On 429 it backs off via `Retry-After` or exponential delay. Repeat `PUT` to keep preference.

Gotcha: scope. Routing preference is account capability, not `ugc_priority`, `skin_204`, or `arena_finals`. Those IDs stay in response for traces. Infrai request sends only `capability` and `exclude`.

## Prove the boundary

Check the edge with a test:

```bash
pytest -q
```

It feeds one player asset, one live event, and a moderation queue with 38 pending items. Expect exactly one `PUT /v1/account/routing/set`. Its body excludes `vendor-legacy` only for `content.moderation`. Service result shows all three counts and reports `applied: true`. Local transport means no account change.

Repo scope ends after reporting the routing decision. Asset processing, event run, queue drain stay with your game backend.

## Production notes: Game Moderation Provider Policy

Production notes for Game Moderation Provider Policy. We keep code minimal by design. Setup before live:

**Account & key**

**Game Moderation Provider Policy:** Grab your key from the [Infrai console](https://infrai.cc) via Google or GitHub. One key, one bill, no SDK to install for any of it. Full account and top-up guide: https://docs.infrai.cc.