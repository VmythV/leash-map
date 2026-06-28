#!/usr/bin/env bash
# Firmware <-> cloud end-to-end: the real C firmware core (lm_app) drives the
# live server over HTTP and trips a geofence exit alert.
set -euo pipefail

PORT=8080
BASE="http://localhost:${PORT}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEVICE="dev_bridge_001"
export PATH="$HOME/.local/bin:$PATH"

jqpy() { python3 -c "import sys,json;print(json.load(sys.stdin)$1)"; }

echo ">>> building firmware bridge..."
make -C "$ROOT/firmware" bridge >/dev/null

echo ">>> starting cloud (sqlite)..."
( cd "$ROOT/server" && rm -f leashmap.db && exec uv run uvicorn leashmap.main:app --port "$PORT" --log-level warning ) &
SRV=$!
trap 'kill $SRV 2>/dev/null || true; rm -f "$ROOT/server/leashmap.db"' EXIT

for _ in $(seq 1 40); do curl -fs "$BASE/health" >/dev/null 2>&1 && break; sleep 0.5; done
curl -fs "$BASE/health" >/dev/null || { echo "server failed to start"; exit 1; }

AUTH() { curl -s -H "authorization: Bearer $TOKEN" -H 'content-type: application/json' "$@"; }
TOKEN=$(curl -s -X POST "$BASE/v1/auth/demo-session" -H 'content-type: application/json' -d '{"display_name":"May"}' | jqpy "['token']")
PET=$(AUTH -X POST "$BASE/v1/pets" -d '{"name":"Buddy"}' | jqpy "['id']")
AUTH -X POST "$BASE/v1/devices/bind" -d "{\"device_id\":\"$DEVICE\",\"pet_id\":\"$PET\"}" >/dev/null
AUTH -X POST "$BASE/v1/pets/$PET/geofences" -d '{"name":"家","center_lat":31.2304,"center_lng":121.4737,"radius_m":120}' >/dev/null
echo ">>> app ready: pet=$PET, device=$DEVICE, safe zone '家' (r=120m)"
echo

echo ">>> running firmware bridge (C core -> live cloud)..."
"$ROOT/firmware/build/lm_bridge" "$DEVICE" "$PORT"
echo

echo ">>> latest location (from the C firmware):"
AUTH "$BASE/v1/pets/$PET/location/latest" \
  | python3 -c "import sys,json;d=json.load(sys.stdin)['location'];print('  ',d['lat'],d['lng'],'acc',d['accuracy_m']) if d else print('  none')"
echo ">>> alerts:"
AUTH "$BASE/v1/alerts" | python3 -c "import sys,json
data=json.load(sys.stdin)['data']
print('\n'.join('  - %s %s %s | %s'%(a['type'],a['severity'],a['status'],a['message']) for a in data) or '  (none)')"
echo
echo ">>> done."
