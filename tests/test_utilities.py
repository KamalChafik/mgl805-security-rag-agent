"""Offline regression tests for utility scripts; no internet or Docker needed."""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))


def load(name):
    src = ROOT / 'scripts' / f'{name}.py'
    spec = importlib.util.spec_from_file_location(f'utility_{name}', src)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_validate_zap_report():
    report = json.loads((ROOT / 'tests/fixtures/synthetic-zap.json').read_text())
    assert load('import_zap_report').validate(report) == 2


def test_reject_invalid_report():
    importer = load('import_zap_report')
    try:
        importer.validate({'not_site': []})
    except ValueError as exc:
        assert 'site' in str(exc)
    else:
        raise AssertionError('Invalid report must fail validation')


def test_env_reader_parses_blank_values_and_comments(tmp_path, monkeypatch):
    common = load('_common')
    monkeypatch.setattr(common, 'ROOT', tmp_path)
    (tmp_path / '.env').write_text('# comment\nBIND_IP=192.168.2.20\nWEBUI_PORT=3000\nOPENWEBUI_API_KEY=\n')
    env = common.load_env()
    assert env['BIND_IP'] == '192.168.2.20'
    assert common.webui_url(env) == 'http://192.168.2.20:3000'
