#!/usr/bin/env bash
# Apply the static Meridian observatory data blocks into a Finexhaust checkout.
# Usage (from Finexhaust repo root):
#   BOCG_ROOT=/path/to/bankingops-coverage-grid bash path/to/apply-to-finexhaust.sh
# Or with Finexhaust and bankingops-coverage-grid as siblings:
#   bash ../bankingops-coverage-grid/integrations/ficta-meridian/apply-to-finexhaust.sh
set -euo pipefail

FINE_ROOT=$(pwd)
if [[ ! -d ficta-meridian-site ]]; then
  echo "Run from Finexhaust repo root (expected ./ficta-meridian-site)" >&2
  exit 2
fi

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
BOCG_ROOT=${BOCG_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}
PACK="$BOCG_ROOT/integrations/ficta-meridian"
if [[ ! -f "$PACK/scripts/sync-observatory.py" ]]; then
  echo "BOCG pack not found at $PACK (set BOCG_ROOT)" >&2
  exit 2
fi

MANIFEST="$FINE_ROOT/ficta-meridian-site/manifests/latest.json"
if [[ ! -f "$MANIFEST" ]]; then
  echo "Consumer manifest not found at $MANIFEST" >&2
  exit 2
fi

python3 "$PACK/scripts/sync-observatory.py" --apply-manifest "$MANIFEST"

echo "Applied Meridian observatory pack from $PACK"
echo "Only cleanroom_eval and public_eval in manifests/latest.json were updated."
