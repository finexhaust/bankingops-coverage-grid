# Finexhaust → Ficta Meridian static observatory sync

Updates the two BOCG-owned data blocks in the consumer's existing static manifest:

1. Pin **cleanroom-eval 2.1.3** in `manifests/latest.json` (`cleanroom_eval`).
2. Surface all four live LLMAJ case records, including primary/sensitivity outcomes (`public_eval`).

The consumer's release generator and all other manifest fields remain untouched.
The observatory JSON is the source of truth:

- `reference/cleanroom-eval-companion.v1.json` (`release_status: github_release_published`)
- `reference/public-eval-observatory.v1.json`
- `tools/public_eval_observatory.py` (S9-G6)
- `integrations/ficta-meridian/app/data/public-eval-observatory.ts` is generated from
  the observatory by `scripts/sync-observatory.py`.

cleanroom-eval **v2.1.3** is released (marked Latest; BankingEnv runtime 2.1.3,
dataset 3.1):
https://github.com/thefazzer/cleanroom-eval/releases/tag/v2.1.3
(The pin moved from 1.2.0 to 2.1.0 in BOCG v0.8.0, to 2.1.1 in v0.8.1,
to 2.1.2 in v0.8.2 and to 2.1.3 in v0.8.5.)

## One-shot apply (from Finexhaust repo root)

```bash
# Finexhaust and bankingops-coverage-grid as siblings:
bash ../bankingops-coverage-grid/integrations/ficta-meridian/apply-to-finexhaust.sh

# Or:
BOCG_ROOT=/path/to/bankingops-coverage-grid \
  bash /path/to/bankingops-coverage-grid/integrations/ficta-meridian/apply-to-finexhaust.sh

git diff -- ficta-meridian-site/manifests/latest.json
```

The script validates the consumer manifest and both source data blocks before it
writes. It atomically replaces `manifests/latest.json`, changing only
`cleanroom_eval` and `public_eval`; no React component, page anchor, or consumer
generator is overwritten.

## Verify

```bash
python3 "$BOCG_ROOT/integrations/ficta-meridian/scripts/sync-observatory.py" --check
python3 -m pytest "$BOCG_ROOT/bocg/tests/test_ficta_meridian_pack.py" -q
```

Acceptance: `cleanroom_eval.version == "2.1.3"`, zero paint-eligible LLMAJ
cases, and the same four complete case records as the observatory.
