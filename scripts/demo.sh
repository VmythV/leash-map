#!/usr/bin/env bash
# End-to-end MVP demo: boot the cloud, set up an App account + safe zone,
# then run the device simulator and show the resulting trail and alerts.
#
# Usage: scripts/demo.sh [mode]    # mode: exit_zone (default) | low_battery | offline | normal | drift | lost
set -euo pipefail

MODE="${1:-exit_zone}"
PORT=8080
BASE="http://localhost:${PORT}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PATH="$HOME/.local/bin:$PATH"

jqpy() { python3 -c "import sys,json;print(json.load(sys.stdin)$1)"; }

echo ">>> starting cloud (sqlite)..."
( cd "$ROOT/server" && rm -f leashmap.db && exec uv run uvicorn leashmap.main:app --port "$PORT" --log-level warning ) &
SRV=$!
trap 'kill $SRV 2>/dev/null || true; rm -f "$ROOT/server/leashmap.db"' EXIT

# wait for readiness
for _ in $(seq 1 40); do
  curl -fs "$BASE/health" >/dev/null 2>&1 && break
  sleep 0.5
done
curl -fs "$BASE/health" >/dev/null || { echo "server failed to start"; exit 1; }
echo ">>> cloud is up: $(curl -s $BASE/health)"

AUTH() { curl -s -H "authorization: Bearer $TOKEN" -H 'content-type: application/json' "$@"; }

TOKEN=$(curl -s -X POST "$BASE/v1/auth/demo-session" -H 'content-type: application/json' -d '{"display_name":"May"}' | jqpy "['token']")
PET=$(AUTH -X POST "$BASE/v1/pets" -d '{"name":"Buddy"}' | jqpy "['id']")
AUTH -X POST "$BASE/v1/devices/bind" -d "{\"device_id\":\"dev_mvp_001\",\"pet_id\":\"$PET\"}" >/dev/null
AUTH -X POST "$BASE/v1/pets/$PET/geofences" -d '{"name":"家","center_lat":31.2304,"center_lng":121.4737,"radius_m":100}' >/dev/null
echo ">>> app ready: pet=$PET, safe zone '家' (r=100m)"
echo

echo ">>> running simulator (mode=$MODE)..."
( cd "$ROOT/simulator" && uv run python -m leashmap_sim --mode "$MODE" --count 8 --interval 0.1 \
    --device-id dev_mvp_001 --endpoint "$BASE" --token dev-token )
echo

echo ">>> trail:"
AUTH "$BASE/v1/pets/$PET/trail?from=2026-01-01T00:00:00Z&to=2026-12-31T00:00:00Z" \
  | python3 -c "import sys,json;d=json.load(sys.stdin);print('  points=%d distance_m=%s'%(d['point_count'],d['distance_m']))"

echo ">>> alerts:"
AUTH "$BASE/v1/alerts" | python3 -c "import sys,json
data=json.load(sys.stdin)['data']
print('\n'.join('  - %s %s %s | %s'%(a['type'],a['severity'],a['status'],a['message']) for a in data) or '  (none)')"
echo
echo ">>> demo complete."
