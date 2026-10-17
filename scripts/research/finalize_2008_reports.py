"""Register completed 2008 studies and preserve prior research history."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    note = ('## Completed update: clean 2008 reference and harmonized evidence\n\n'
            'ATH33 and ATH34 are completed. The current portfolio reference starts with cash and zero holdings in 2008; '
            'the older ATH32 table remains a historical inherited-position slice. Net CAGR for SMA200 drift/monthly is '
            '9.88/8.88%, versus SPY 11.24%; all eight net variants lag SPY. '
            'Existing filter definitions have now been harmonized to 2008 onward: 111 ordinary variants on the same '
            '15,853-event reference population, plus momentum, industry, ranking and combination diagnostics. '
            'No positive ordinary family-level improvement is established. Earlier pending-step statements below are historical. '
            'These inspected data remain development evidence.\n\n'
            'Results: [ATH33](ATH_CLEAN_2008_REFERENCE_RESULTS.md) and '
            '[ATH34](ATH_2008_EVIDENCE_SYNTHESIS_RESULTS.md). '
            'Next unresolved work is risk/exposure/concentration assessment and independent validation of a frozen rule; '
            'no additional parameter search is authorized by this update.\n\n')
    for name in ['RESEARCH_MAP.md', 'RESEARCH_STATUS_20261016.md', 'ATH_RESEARCH_OVERVIEW_2008.md']:
        p = ROOT / 'research/ath' / name
        old = p.read_text(encoding='utf-8')
        if '## Completed update: clean 2008 reference' not in old:
            p.write_text(note + old, encoding='utf-8')
    configs = [
        ('ath_33_clean_2008_reference_v001', 'outputs/backtests/ath_33_clean_2008_reference_v001/20261017T175657998145Z',
         'ATH_CLEAN_2008_REFERENCE', 'https://www.notion.so/3fc40ecdb26681f88120cc18e6a32dac',
         ['backtest_ath_clean_2008.py', 'verify_ath_clean_2008.py', 'verify_ath_clean_2008_features.py'],
         {'focused_tests_passed': 13, 'portfolio_variants_verified': 10, 'raw_sma200_cells': 9201656, 'summary_rows': 250}),
        ('ath_34_2008_evidence_synthesis_v001', 'outputs/research/ath/ath_34_2008_evidence_synthesis_v001/20261017T180449698337Z',
         'ATH_2008_EVIDENCE_SYNTHESIS', 'https://www.notion.so/3fc40ecdb2668122a504dd12f5720bf5',
         ['harmonize_ath_2008_evidence.py', 'bootstrap_ath_2008_evidence.py', 'verify_ath_2008_evidence.py'],
         {'focused_tests_passed': 2, 'source_hashes_verified': 34, 'masks_verified': 226, 'summary_rows': 1808, 'interval_rows': 904})]
    registry = ROOT / 'research/ath/experiments.csv'
    with registry.open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames
        existing = {row['study_id'] for row in reader}
    for study, directory, stem, url, scripts, checks in configs:
        run = ROOT / directory
        target = run / 'manifest.json'
        base = target if target.exists() else run / 'preparation.json'
        manifest = json.loads(base.read_text(encoding='utf-8'))
        manifest.update(study_id=study, status='completed_exploratory', verification=checks, notion_url=url)
        manifest['final_code_sha256'] = {s: digest(ROOT / 'scripts/research' / s) for s in scripts}
        manifest['documents_sha256'] = {str(p.relative_to(ROOT)): digest(p) for p in
            [ROOT / 'research/ath' / (stem + '_PLAN.md'), ROOT / 'research/ath' / (stem + '_RESULTS.md')]}
        manifest['final_artifacts_sha256'] = {str(p.relative_to(run)): digest(p) for p in run.rglob('*')
            if p.is_file() and p != target}
        target.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        if study not in existing:
            values = [study, 'completed_exploratory',
                      'Evaluate existing ATH research since 2008',
                      'Clean cash initialization' if '33_' in study else 'Same saved definitions; harmonized modern cohorts and new uncertainty',
                      'research/ath/' + stem + '_PLAN.md', directory + '/manifest.json',
                      'All eight net portfolios lag SPY' if '33_' in study else 'No ordinary family establishes positive simultaneous improvement',
                      'Preserve development evidence; no optimality or confirmed alpha; no new parameter search']
            with registry.open('a', encoding='utf-8', newline='') as handle:
                csv.DictWriter(handle, fieldnames=fields).writerow(dict(zip(fields, values)))
        print(study + ': finalized')


if __name__ == '__main__':
    main()
