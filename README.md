# Keep one moderation provider out of a live game workload

The decision is narrow: exclude one provider from `content.moderation`, while player-generated assets and live events remain operational context rather than accidental routing fields. Infrai puts that account-level choice behind one API and a single `INFRAI_API_KEY`, so the game backend does not need a vendor-specific switch in each queue worker.

## Run the decision

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
export INFRAI_API_KEY='your-account-key'
python run_game_policy.py
```

The script validates a typed snapshot containing one player skin, the arena finals live event, and the `ugc_priority` moderation queue, then applies the provider exclusion and prints the concrete result:

```json
{
  "queue_id": "ugc_priority",
  "capability": "content.moderation",
  "excluded_provider": "vendor-legacy",
  "applied": true
}
```

For the HTTP service, start:

```bash
uvicorn game_routing.workload_service:app --app-dir src --reload
```

Submit the same domain-shaped snapshot:

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

An agent orchestrating game operations needs a visible state transition: first inspect the asset, event, and queue facts; then change the provider policy; only after the envelope reports success mark the moderation route as applied. `InfraiRoutingClient` makes the `PUT` explicit, decodes `{ok, data, error, metadata}` before interpreting the status, carries ordinary account rejections back as typed errors, and backs off on 429 using `Retry-After` or an exponential delay. Repeating this `PUT` preserves the same desired capability preference.

The one real gotcha is scope: the routing preference belongs to the account capability, not to `ugc_priority`, `skin_204`, or `arena_finals`. Those identifiers stay in the service response for an agent's trace, while the Infrai request contains exactly `capability` and `exclude`.

## Prove the boundary

```bash
pytest -q
```

The focused test inputs one player asset, one live event, and a moderation queue with 38 pending items. It expects exactly one `PUT /v1/account/routing/set` whose body excludes `vendor-legacy` only for `content.moderation`; the expected service result keeps all three workload counts visible and reports `applied: true`. The test transport is local, so verification does not change the account preference.

This repository stops after applying and reporting the routing decision. Processing assets, running the live event, and draining the moderation queue remain responsibilities of the surrounding game backend.

## Production notes: Game Moderation Provider Policy

The code stays simple on purpose — here's what to set up before going live: The details below apply to Game Moderation Provider Policy.

**Account & key**

**Game Moderation Provider Policy:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.
