# Integration setup

Default launcher: `scripts/start_app.py`; `DEMO_MODE=false`, no seeded users. Create your own patient account in the UI. `scripts/create_admin.py` privately provisions the first staff administrator.

## Groq

Local `.env`: `GROQ_API_KEY`, `GROQ_MODEL=openai/gpt-oss-120b`, `ENABLE_LLM=true`. The supplied key/model have produced a real structured response. Each case must also set `allow_llm_processing=true` via its UI consent checkbox. Measurements, symptoms, model outputs and follow-up context are de-identified; names, patient IDs, phones and precise coordinates are excluded. Only known clinical symptom labels are sent; arbitrary symptom free text is withheld to prevent embedded identifiers/instructions. AI text is supplementary; schema/urgency mismatch or provider failure leaves canonical care actions intact.

## Real OpenStreetMap search

No key required. `OVERPASS_URL=https://overpass.private.coffee/api/interpreter` is configurable. The service caches results and serializes requests. Public providers may fail. One bounded official map request at `OSM_MAP_FALLBACK_URL=https://api.openstreetmap.org/api/0.6/map.json` then covers only the nearest 2 km, clearly labelled partial coverage. It never bulk-downloads the editing API. Returned hospital geometry/tags are real; reported capabilities are explicitly unverified.

References: [Overpass instances](https://wiki.openstreetmap.org/wiki/Overpass_API), [OSM read API](https://wiki.openstreetmap.org/wiki/API_v0.6). Location permission and provider-sharing consent are separate. Public test coordinates returned eight hospitals through the bounded fallback.

## Optional verified facility directory

Set `FACILITY_DIRECTORY_PATH` to your JSON file. Verified services take precedence over map candidates. Unknown availability always requires confirmation.

```json
{"facilities": [
  {
    "facility_id": "local-directory-id",
    "name": "Verified local facility",
    "type": "hospital",
    "latitude": 34.0,
    "longitude": 71.5,
    "has_emergency": true,
    "has_maternity": true,
    "has_nicu": false,
    "phone": "locally verified telephone",
    "source": "District authority directory, URL or identifier",
    "verified_at": "2026-10-10",
    "availability": "unknown",
    "availability_checked_at": null,
    "simulated": false
  }
]}
```

Use actual verified values; this example is a schema, not a real facility. Capability verification defaults to a 365-day freshness limit. Availability defaults to unknown; a checked status older than 24 hours becomes unknown. Stale/unverified capabilities and explicitly simulated entries are excluded from real cases. Unknown availability requires a call, not an inferred free bed. Update this file from your directory/API; a live bed feed is not implemented.

## Roads

Set `OPENROUTESERVICE_API_KEY` in local `.env`. It has been verified live. Separate coordinate-sharing consent is required. Only coordinate pairs go to the routing provider. Missing consent, timeout or unavailable route gives labelled straight-line distance and no ETA. The closest five displayed candidates receive road estimates; others retain explicit straight-line distance. Provider quotas and road accessibility apply.

Reference: [openrouteservice API](https://api.openrouteservice.org/).

## SMS, WhatsApp, calls and reminders

Persistent follow-up tasks and app-open reminders work locally. `sms:`, `tel:` and `wa.me` links open the user's messaging/call apps with a prepared message after explicit sharing consent. They do not automatically send, and they do not produce a false delivery receipt. No API key is required for these buttons; mobile/network charges may apply.

Automatic background delivery needs a provider account, credentials, recipient consent, templates if required, delivery callbacks, opt-out handling and retry/idempotency. No universal free automatic SMS/call service is configured. These requirements are separate from working manual contact actions.

## Deployment

`requirements-app.txt` pins the artifact runtime. Local data persists in `data/local-app.db` by default. Production requires `APP_ENV=production`, `DEMO_MODE=false`, a 32+ character explicit JWT secret, persistent PostgreSQL and its driver, HTTPS, backups and scoped staff accounts. GPS needs HTTPS outside localhost. Clinical external validation and live bed feeds are not supplied by API connectivity.
