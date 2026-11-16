# Astros Engine · Railway laboratory

**Repository/branch:** `alexorbit/Astrologer-API:poc/railway-astrologer-20261115`. All modifications are isolated from the upstream `v6` branch.

**Railway project:** `astros-engine-laboratorio`, environment `homologacao`, service `astrologer-api-poc`.

## Build and run

A first Railpack deploy detected Python but did not install dependencies. A second attempt installed all dependencies in its build stage but did not expose the `libephemeris` executable in runtime. The PoC therefore uses `Dockerfile.poc` to install **inside the actual runtime image**, making dependencies reproducible.

- Select Dockerfile path: `Dockerfile.poc`.
- Clear custom build command; start `sh poc/start.sh`.
- Base tier LEB2: downloaded during the Docker image build.
- Railway variables: `PRIVATE_ASTROLOGER_API_SECRET_KEY`, `ASTROLOGER_DEBUG=false`, `EPHEMERIS_REQUIRED_TIER=base`, `EPHEMERIS_TARGET_TIER=base`, `EPHEMERIS_REQUIRE_PREWARM=true`.
- Railway limits: 1 vCPU, 2 GB RAM, 1 replica. No database or persistent volume during the PoC.
- API auth: `X-API-Key`, never in a query parameter. Static `/poc` UI is public without a secret; it cannot execute calculations until a key is entered.
- Endpoint `/health` is liveness only; use `/ready` and actual computations to establish numerical readiness.

## Automated verification

The startup script performs **one** synthetic smoke test after the API starts. It validates readiness, health, invalid key rejection, natal JSON, natal SVG, Moon, weekly events and transits. Only test outcomes, status codes and timings are logged.

Use `POC_SMOKE` filter in Railway deployment logs. Any failure must remain visible; do not reinterpret missing ephemerides as valid results. Test input is fictitious and does not come from any reader.

The browser console at `/poc` offers the same tests interactively, with JSON result inspection and SVG preview. Secret input is kept only in browser memory, not persisted.

## Invariants

The GIROO portal and API are NOT connected to this project. No production configuration or databases modified. This is an experimental AGPL-3.0 proof of concept. The LEB2-base data coverage and the historical timezone policy must be checked before trusting predictions and before commercial use.
