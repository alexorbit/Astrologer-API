# Astros · Railway PoC (isolated, no GIROO changes)

Source: branch `poc/railway-astrologer-20261115`. This is **not** a production deployment.

## Operations

1. Create a **new isolated Railway project**, no shared variables.
2. Set Python 3.12 in `RAILPACK_PYTHON_VERSION`.
3. Require `PRIVATE_ASTROLOGER_API_SECRET_KEY` and `ASTROLOGER_DEBUG=false`. Never set `ASTROLOGER_ALLOW_NO_AUTH`.
4. Build with Railpack using `pyproject.toml`, start with:
   `sh -c 'libephemeris download leb2-base && exec uvicorn poc_app:app --host 0.0.0.0 --port "${PORT:-8000}"'`
5. Use the **base tier only** for the proof of concept. Do not set `LIBEPHEMERIS_DATA_DIR` without a provisioner and verified `.initialized` marker; otherwise calculations are correctly blocked. Default unmanaged local mode requires verifying actual ephemeris inventory before trusting results.
6. Only expose a domain to provide the PoC console. All calculation routes require `X-API-Key`. `/poc` is public but has no secrets or persistent state.
7. Test `/health`, `/ready`, natal data, SVG, Moon, calendar, transits, and an unauthenticated rejection. Use synthetic 1990-11-10 and São Paulo coordinates, never user data.
8. For CLI tests: `ASTROLOGER_TEST_API_KEY=... python poc/smoke.py https://<poc-domain>`.
9. Do not connect GIROO public or production services.

### Known limits

- `leb2-base` offers an abbreviated timespan compared with `extended`; errors or unsupported features must be reported, not inferred.
- The GitHub project and its libephemeris dependency use AGPL-3.0; this PoC does not settle commercial reuse.
- In unmanaged mode, readiness may reflect `local-unmanaged`, not an independently verified sealed inventory; inspect the library's actual source, checksum and coverage.
- If Python package builds or downloaded LEB2 objects fail, inspect Railway build/deploy logs. Avoid hiding errors behind a fallback.
- No Docker, database, volume or production cutover is required for the initial 33 MB-class base test. On later scale tests, move to provisioned volume and sealed mode.
