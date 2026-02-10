#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
TOKEN="${TOKEN:-}"

if [[ -z "$TOKEN" ]]; then
  echo "ERROR: set TOKEN before running"
  echo "Example: TOKEN='tok__...:...123456' BASE_URL='http://127.0.0.1:8000' bash scripts/token_auth_smoke.sh"
  exit 1
fi

AUTH_HEADER="X-KEYSMITH-TOKEN: ${TOKEN}"

echo "== Plain Django endpoints =="
echo "-- without token (expect 401)"
curl -sS -i "${BASE_URL}/token-check/plain/status/" | sed -n '1,20p'

echo

echo "-- with token (expect 200)"
curl -sS -i -H "$AUTH_HEADER" "${BASE_URL}/token-check/plain/status/" | sed -n '1,30p'

echo

echo "== DRF endpoints =="
echo "-- without token (expect 401)"
curl -sS -i "${BASE_URL}/token-check/drf/status/" | sed -n '1,25p'

echo

echo "-- with token (expect 200)"
curl -sS -i -H "$AUTH_HEADER" "${BASE_URL}/token-check/drf/status/" | sed -n '1,30p'

echo

echo "== DRF CRUD =="
CREATE_JSON='{"title":"curl note","content":"from smoke script"}'
CREATE_RESP=$(curl -sS -H "$AUTH_HEADER" -H 'Content-Type: application/json' -d "$CREATE_JSON" "${BASE_URL}/token-check/drf/notes/")
echo "Create: $CREATE_RESP"
NOTE_ID=$(printf '%s' "$CREATE_RESP" | python -c 'import sys,json; print(json.load(sys.stdin)["id"])')

echo "List:"
curl -sS -H "$AUTH_HEADER" "${BASE_URL}/token-check/drf/notes/" && echo

echo "Patch:"
curl -sS -X PATCH -H "$AUTH_HEADER" -H 'Content-Type: application/json' -d '{"content":"updated by curl"}' "${BASE_URL}/token-check/drf/notes/${NOTE_ID}/" && echo

echo "Delete (expect empty body with 204):"
curl -sS -o /dev/null -w 'HTTP %{http_code}\n' -X DELETE -H "$AUTH_HEADER" "${BASE_URL}/token-check/drf/notes/${NOTE_ID}/"

echo

echo "Done. Check admin audit logs for auth_failed (missing_token) and auth_success entries."
