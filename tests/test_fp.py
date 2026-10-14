"""The lead's local workflow, including interruption and delivery boundaries."""
import importlib
import importlib.util
import json
from pathlib import Path

import pytest

import fp_docx
from word_fixtures import edit_text, make_template
import register


@pytest.fixture
def setup(tmp_path):
    assert importlib.util.find_spec('fp'), 'The supported entry module is not implemented'
    fp = importlib.import_module('fp')
    base, template = tmp_path / 'partial.docx', tmp_path / 'template.docx'
    make_template(template)
    make_template(base)
    edit_text(base, '[Summarise the proposal]', 'Existing company account.')
    example = tmp_path / 'example.txt'
    example.write_text('Approved voice: explain the business, then the financing case.')
    folder = tmp_path / 'deal'
    request = dict(op_id='prepare-1', base_revision=0, deal='synthetic', base=str(base),
                   template=str(template), examples=[str(example)], output_dir=str(folder / 'output'),
                   mode='existing', provenance='Authorised first import of an officer draft')
    return fp, folder, request


def ready_preflight(folder):
    reg = register.load(folder)
    preflight = dict(reg['run']['preflight'], editorial='complete')
    register.apply(folder, dict(base_revision=reg['revision'], op_id='preflight', actor='test', changes=[
        {'sheet': 'sources', 'add': {'title': 'Original company account',
          'link': reg['run']['base']['path'], 'coverage': 'read', 'impact': 'assessed'}},
        {'sheet': 'claims', 'add': {'assertion': 'The original draft contains the company account.',
          'kind': 'disclosed fact', 'sources': 'S-001 Summary paragraph 1', 'sections': 'summary'}},
        {'sheet': 'analysis', 'add': {'id': 'preflight', 'title': 'Template and examples',
          'text': 'Keep required headings; follow the supplied example voice and density.'}},
        {'sheet': 'run', 'set': dict(reg['run'], preflight=preflight)}]))


def build_request(folder):
    content = folder / 'draft.md'
    content.write_text('## summary\nRevised company account.\n\n'
                       '## financial-analysis\nExplained financial movements.\n\n{{keep:1}}\n\n'
                       '## market-risk\nMarket context.\n\n## recommendation\nProvisional case.\n')
    return dict(op_id='build-1', base_revision=register.load(folder)['revision'],
                content=str(content), out='FP-v01.docx')


def test_prepare_requires_real_inputs_and_is_idempotent(setup):
    fp, folder, req = setup
    result = fp.prepare(folder, req)
    assert result['revision'] == 1 and result['status'] == 'prepared'
    before = (folder / 'register.json').read_bytes()
    assert fp.prepare(folder, req)['revision'] == 1
    assert (folder / 'register.json').read_bytes() == before
    reg = register.load(folder)
    assert reg['run']['preflight']['editorial'] == 'pending'
    assert reg['run']['base']['sha256'] == register.sha256(req['base'])
    fp.status(folder)
    assert (folder / 'register.json').read_bytes() == before
    with pytest.raises((ValueError, register.ChangeError)):
        fp.prepare(folder, dict(req, deal='different'))


def test_build_requires_editorial_preflight_then_bundles_actual_artifacts(setup, tmp_path):
    fp, folder, req = setup
    fp.prepare(folder, req)
    build = build_request(folder)
    with pytest.raises(ValueError, match='preflight'):
        fp.build(folder, build)
    ready_preflight(folder)
    build['base_revision'] = register.load(folder)['revision']
    result = fp.build(folder, build)
    assert result['status'] == 'built'
    reg = register.load(folder)
    assert reg['run']['artifacts']['word']['sha256'] == register.sha256(result['word'])
    assert fp.build(folder, build)['build_id'] == result['build_id']
    bundle = fp.bundle(folder, tmp_path / 'delivery')
    manifest = json.loads(Path(bundle['manifest']).read_text())
    assert manifest['register_revision'] == reg['revision']
    for item in manifest['files']:
        assert register.sha256(Path(bundle['directory']) / item['path']) == item['sha256']
    assert {'register.json', 'Analysis.md', 'register.xlsx', 'DDQ.md'} <= {i['path'] for i in manifest['files']}
    assert 'Revised company account.' in fp_docx.to_markdown(result['word'])
    assert fp.bundle(folder, tmp_path / 'delivery')['status'] == 'bundled'
    (tmp_path / 'delivery' / 'DDQ.md').write_text('Different content')
    with pytest.raises(ValueError, match='conflict'):
        fp.bundle(folder, tmp_path / 'delivery')


def test_word_success_register_failure_can_resume_without_new_identity(setup, monkeypatch):
    fp, folder, req = setup
    fp.prepare(folder, req)
    ready_preflight(folder)
    request = build_request(folder)
    original = register.apply
    monkeypatch.setattr(register, 'apply', lambda *a, **k: (_ for _ in ()).throw(OSError('disk full')))
    failed = fp.build(folder, request)
    assert failed['status'] == 'register_pending'
    word = Path(failed['word'])
    saved = word.read_bytes()
    monkeypatch.setattr(register, 'apply', original)
    complete = fp.build(folder, request)
    assert complete['status'] == 'built' and complete['build_id'] == failed['build_id']
    assert word.read_bytes() == saved


def test_changed_register_after_published_word_reports_conflict(setup, monkeypatch):
    fp, folder, req = setup
    fp.prepare(folder, req)
    ready_preflight(folder)
    request = build_request(folder)
    original = register.apply
    monkeypatch.setattr(register, 'apply', lambda *a, **k: (_ for _ in ()).throw(OSError('disk full')))
    failed = fp.build(folder, request)
    monkeypatch.setattr(register, 'apply', original)
    original(folder, dict(base_revision=request['base_revision'], op_id='other', changes=[]))
    result = fp.build(folder, request)
    assert result['status'] == 'register_conflict' and result['word'] == failed['word']
    assert register.load(folder)['run']['status'] == 'prepared'


def test_input_change_and_bundle_mutation_are_not_hidden(setup, tmp_path):
    fp, folder, req = setup
    fp.prepare(folder, req)
    ready_preflight(folder)
    request = build_request(folder)
    edit_text(req['base'], 'Existing company account.', 'Later officer change.')
    with pytest.raises(ValueError, match='changed'):
        fp.build(folder, request)
    assert not (folder / 'output' / 'FP-v01.docx').exists()


def test_cli_errors_are_structured_and_version_has_core_hashes(setup, capsys):
    fp, folder, req = setup
    assert fp.main(['--version']) == 0
    info = json.loads(capsys.readouterr().out)
    assert info['version'] and {'register.py', 'fp_docx.py', 'fin_table.py'} <= set(info['scripts'])
    assert fp.main(['status', str(folder)]) != 0
    assert json.loads(capsys.readouterr().out)['status'] == 'error'


@pytest.mark.parametrize('which', ['content', 'support', 'base'])
def test_completed_build_retry_checks_original_bytes(setup, which):
    fp, folder, req = setup
    fp.prepare(folder, req)
    ready_preflight(folder)
    request = build_request(folder)
    support = folder / 'support.json'
    support.write_text('{}')
    request['support'] = [str(support)]
    fp.build(folder, request)
    changed = req['base'] if which == 'base' else request['content'] if which == 'content' else support
    Path(changed).write_bytes(b'Changed after build')
    with pytest.raises(ValueError, match='changed'):
        fp.build(folder, request)


def test_manifest_filename_cannot_hide_support(setup, tmp_path):
    fp, folder, req = setup
    fp.prepare(folder, req)
    ready_preflight(folder)
    request = build_request(folder)
    support = folder / 'manifest.json'
    support.write_text('{"evidence": "keep"}')
    request['support'] = [str(support)]
    fp.build(folder, request)
    with pytest.raises(ValueError, match='reserved'):
        fp.bundle(folder, tmp_path / 'delivery')
    assert not (tmp_path / 'delivery').exists()


def test_prepare_exposes_template_mismatch(setup):
    fp, folder, req = setup
    edit_text(req['base'], 'Market risk', 'Different risk')
    result = fp.prepare(folder, req)
    assert 'market-risk' in result['preflight']['word']['missing_sections']


def test_bad_word_and_bad_path_are_structured_cli_errors(setup, capsys):
    fp, folder, req = setup
    path = folder.parent / 'prepare.json'
    Path(req['base']).write_bytes(b'not a docx')
    path.write_text(json.dumps(req))
    assert fp.main(['prepare', str(folder), str(path)]) == 1
    assert json.loads(capsys.readouterr().out)['status'] == 'error'
    req['examples'] = [None]
    path.write_text(json.dumps(req))
    assert fp.main(['prepare', str(folder), str(path)]) == 1
    assert json.loads(capsys.readouterr().out)['status'] == 'error'


def test_views_failed_after_master_save_recover_on_identical_retry(setup, monkeypatch):
    fp, folder, req = setup
    fp.prepare(folder, req)
    ready_preflight(folder)
    request = build_request(folder)
    original = register.refresh_views
    monkeypatch.setattr(register, 'refresh_views', lambda *a, **k: (_ for _ in ()).throw(OSError('disk full')))
    failed = fp.build(folder, request)
    assert failed['status'] == 'register_pending'
    saved = Path(failed['word']).read_bytes()
    monkeypatch.setattr(register, 'refresh_views', original)
    assert fp.build(folder, request)['status'] == 'built'
    assert Path(failed['word']).read_bytes() == saved
    assert (folder / 'Analysis.md').exists()


def test_interrupted_bundle_reports_files_and_resumes(setup, tmp_path, monkeypatch):
    fp, folder, req = setup
    fp.prepare(folder, req)
    ready_preflight(folder)
    fp.build(folder, build_request(folder))
    original, calls = fp_docx.publish, []
    def fail_third(path, writer):
        calls.append(path)
        if len(calls) == 3:
            raise OSError('disk full')
        return original(path, writer)
    monkeypatch.setattr(fp_docx, 'publish', fail_third)
    result = fp.bundle(folder, tmp_path / 'delivery')
    assert result['status'] == 'partial_bundle' and len(result['published']) == 2
    monkeypatch.setattr(fp_docx, 'publish', original)
    assert fp.bundle(folder, tmp_path / 'delivery')['status'] == 'bundled'
