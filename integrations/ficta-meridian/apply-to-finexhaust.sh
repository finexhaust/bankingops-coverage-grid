#!/usr/bin/env bash
# Apply BOCG Meridian eval-observatory pack into a Finexhaust checkout.
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
if [[ ! -f "$PACK/scripts/gen-release-observatory.py" ]]; then
  echo "BOCG pack not found at $PACK (set BOCG_ROOT)" >&2
  exit 2
fi

PAGE=ficta-meridian-site/app/page.tsx
for source in \
  "$PACK/scripts/gen-release-observatory.py" \
  "$PACK/app/components/PublicEvalObservatory.tsx" \
  "$PACK/app/data/public-eval-observatory.ts"; do
  [[ -f "$source" ]] || { echo "Pack file missing: $source" >&2; exit 2; }
done
[[ -f "$PAGE" ]] || { echo "Consumer page not found: $PAGE" >&2; exit 2; }
for destination in \
  ficta-meridian-site/scripts \
  ficta-meridian-site/app/components \
  ficta-meridian-site/app/data; do
  [[ -d "$destination" && -w "$destination" ]] || {
    echo "Consumer destination is missing or not writable: $destination" >&2
    exit 2
  }
done

STAGE_DIR=$(mktemp -d)
trap 'rm -rf "$STAGE_DIR"' EXIT
python3 - "$PAGE" "$STAGE_DIR/page.tsx" <<'PY'
from pathlib import Path
import sys
path, staged = map(Path, sys.argv[1:])
text = path.read_text(encoding="utf-8")
import_anchor = "import ReferenceExplorer from './components/ReferenceExplorer';\n"
section_anchor = "      <ReferenceExplorer />\n"
import_lines = (
    "import PublicEvalObservatory from './components/PublicEvalObservatory';\n"
    "import { CLEANROOM_EVAL_PIN } from './data/public-eval-observatory';\n"
)
if "import PublicEvalObservatory from" not in text:
    if import_anchor not in text:
        raise SystemExit("import anchor not found in page.tsx; no files were changed")
    text = text.replace(import_anchor, import_anchor + import_lines, 1)
if "<PublicEvalObservatory" not in text:
    if section_anchor not in text:
        raise SystemExit("section anchor not found in page.tsx; no files were changed")
    text = text.replace(section_anchor, section_anchor + "\n      <PublicEvalObservatory />\n", 1)
old = "· harness: thefazzer/cleanroom-eval · 2026-09</footer>"
new = "· harness: finexhaust/cleanroom-eval · {CLEANROOM_EVAL_PIN.version} · {RELEASE_OBSERVATORY.built_at.slice(0, 7)}</footer>"
if "CLEANROOM_EVAL_PIN.version" not in text:
    if old not in text:
        raise SystemExit("footer anchor not found in page.tsx; no files were changed")
    text = text.replace(old, new, 1)
staged.write_text(text, encoding="utf-8")
PY

install -m 0644 "$PACK/scripts/gen-release-observatory.py" \
  ficta-meridian-site/scripts/gen-release-observatory.py
install -m 0644 "$PACK/app/components/PublicEvalObservatory.tsx" \
  ficta-meridian-site/app/components/PublicEvalObservatory.tsx
install -m 0644 "$PACK/app/data/public-eval-observatory.ts" \
  ficta-meridian-site/app/data/public-eval-observatory.ts
if ! cmp -s "$STAGE_DIR/page.tsx" "$PAGE"; then
  install -m 0644 "$STAGE_DIR/page.tsx" "$PAGE"
fi

echo "Applied Meridian observatory pack from $PACK"
echo "Next: commit, then: gh workflow run 'Ficta Meridian daily manifest release'"
