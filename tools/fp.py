#!/usr/bin/env python3
"""Document Lead's local Word workflow: prepare, status, build and bundle. No cloud access."""
import argparse
import json
import shutil
import sys
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from xml.parsers import expat
from pathlib import Path

import fp_docx
import register


def file_ref(path):
    if not isinstance(path, (str, Path)) or not str(path).strip():
        raise ValueError("file path must be a nonempty string")
    path = Path(path).resolve(strict=True)
    if not path.is_file():
        raise ValueError(f'not a file: {path}')
    return {'path': str(path), 'sha256': register.sha256(path)}


def unchanged(ref):
    if file_ref(ref['path']) != ref:
        raise ValueError(f"file changed; prepare again with the current version: {ref['path']}")
    return ref['path']


def request_fields(request, required, optional=()):
    allowed = set(required) | set(optional)
    if not isinstance(request, dict) or set(request) - allowed or set(required) - set(request):
        raise ValueError(f'request requires {sorted(required)}; optional {sorted(optional)}')
    if not isinstance(request['op_id'], str) or not request['op_id'].strip():
        raise ValueError('op_id must be a nonempty string')
    if type(request['base_revision']) is not int or request['base_revision'] < 0:
        raise ValueError('base_revision must be a nonnegative integer')


def prepare(folder, request):
    request_fields(request, ('op_id', 'base_revision', 'deal', 'base', 'template', 'examples',
                             'output_dir', 'mode', 'provenance'), ('record',))
    if any(not isinstance(request[k], str) or not request[k].strip()
           for k in ('deal', 'base', 'template', 'output_dir', 'provenance')):
        raise ValueError('deal, paths and provenance must be nonempty strings')
    if request['mode'] not in ('existing', 'first', 'normal'):
        raise ValueError('mode must be existing, first or normal')
    if not isinstance(request['examples'], list) or not request['examples']:
        raise ValueError('provide at least one approved example')
    base, template = file_ref(request['base']), file_ref(request['template'])
    examples = [file_ref(p) for p in request['examples']]
    record = file_ref(request['record']) if 'record' in request else (
        file_ref(fp_docx.sidecar_path(base['path'])) if request['mode'] == 'normal' else None)
    doc = fp_docx.Doc(base['path'])
    fp_docx.check_mode(doc, base['path'], request['mode'], template['path'], request.get('record'))
    if request['mode'] == 'normal':
        fp_docx.read_record(record['path'] if record else fp_docx.sidecar_path(base['path']), doc)
    run = dict(base=base, template=template, examples=examples,
               output_dir=str(Path(request['output_dir']).resolve()), mode=request['mode'],
               provenance=request['provenance'], status='prepared',
               preflight={'word': dict(fp_docx.inspect(base['path']), **fp_docx.check(base['path'], template['path'])),
                          'template': fp_docx.inspect(template['path']), 'editorial': 'pending'})
    if record:
        run['record'] = record
    folder = Path(folder).resolve()
    if (folder / 'register.json').exists():
        reg = register.load(folder)
        if reg['control']['deal'] != request['deal']:
            raise ValueError('deal differs from this register')
    else:
        if request['base_revision'] != 0:
            raise ValueError('a new register starts at revision 0')
        folder.mkdir(parents=True, exist_ok=True)
        register.save(folder, register.new_register(request['deal']))
    # Full run replacement clears an old explicit record and old delivery artifacts.
    result = register.apply(folder, dict(base_revision=request['base_revision'], op_id=request['op_id'],
        actor='Document Lead', summary='Prepare the current input versions', changes=[
            {'sheet': 'run', 'set': run}]))
    return dict(status='prepared', revision=result['revision'], folder=str(folder),
                preflight=run['preflight'], next_action='Read template/examples and record editorial preflight')


def status(folder):
    reg = register.load(folder)
    run = reg.get('run', {})
    files = []
    for kind, ref in run.get('artifacts', {}).items():
        path = Path(ref['path'])
        files.append(dict(kind=kind, **ref, matches=path.is_file() and register.sha256(path) == ref['sha256']))
    return dict(status=run.get('status', 'unprepared'), revision=reg['revision'],
                preflight=run.get('preflight', {}), files=files,
                checks=register.open_checks(reg, Path(run['artifacts']['word']['path'])
                    if run.get('artifacts', {}).get('word') else None))


def build(folder, request):
    request_fields(request, ('op_id', 'base_revision', 'content', 'out'), ('fields', 'protect', 'support'))
    for key in ('protect', 'support'):
        if key in request and (not isinstance(request[key], list) or
                any(not isinstance(v, str) or not v.strip() for v in request[key])):
            raise ValueError(f'{key} must be a list of nonempty strings')
    folder = Path(folder).resolve()
    reg = register.load(folder)
    run = reg.get('run', {})
    digest = register.request_sha256(request)
    existing = next((entry for entry in reg['log'] if entry['op_id'] == request['op_id']), None)
    if existing:
        if run.get('build_request_sha256') != digest:
            raise ValueError('operation ID belongs to a different request or run')
        for ref in list(run['artifacts'].values()) + [run['draft']] + run.get('support', []) + [
                run['base'], run['template']] + run['examples'] + ([run['record']] if run.get('record') else []):
            unchanged(ref)
        register.refresh(folder)
        return dict(status=run['status'], revision=reg['revision'], build_id=run['build_id'],
                    word=run['artifacts']['word']['path'], artifacts=run['artifacts'], resumed=True)
    if run.get('preflight', {}).get('editorial') != 'complete' or not any(
            a['id'] == 'preflight' and a['text'].strip() for a in reg['analysis']):
        raise ValueError('record template/example editorial preflight before building')
    source_ids = {s['id'] for s in reg['sources']}
    if not any(not register.source_errors(c['sources'] + ' ' + c['inputs'], source_ids)
               for c in reg['claims']):
        raise ValueError('save the located material claims in the evidence index before drafting Word')
    for ref in [run['base'], run['template']] + run['examples'] + ([run['record']] if run.get('record') else []):
        unchanged(ref)
    name = request['out']
    if not isinstance(name, str) or Path(name).name != name or Path(name).suffix.lower() != '.docx':
        raise ValueError('out must be a new .docx filename inside the prepared output directory')
    draft = file_ref(request['content'])
    support = [file_ref(p) for p in request.get('support', [])]
    out = Path(run['output_dir']) / name
    # A prior publication may need its register commit; a stale request may not create a new Word file.
    if reg['revision'] != request['base_revision'] and not fp_docx.receipt_path(out).exists():
        raise register.ChangeError('stale build request; read status before retrying')
    out.parent.mkdir(parents=True, exist_ok=True)
    result = fp_docx.build(run['base']['path'], draft['path'], out, mode=run['mode'],
        template=run['template']['path'], fields=request.get('fields'), protect=request.get('protect', []),
        record=(run['record']['path'] if run.get('record') and Path(run['record']['path']) !=
                fp_docx.sidecar_path(run['base']['path']) else None), deal_id=reg['control']['deal'])
    if result['status'] != 'published':
        return result
    artifacts = {'word': file_ref(out), 'record': file_ref(result['sidecar'])}
    if result.get('proposals'):
        artifacts['proposals'] = file_ref(result['proposals'])
    checks = fp_docx.check(out, run['template']['path'])
    state = 'built' if result['complete'] and not checks['problems'] else 'partial'
    run_update = dict(artifacts=artifacts, draft=draft, support=support,
                      build_id=result['build_id'], parent_build_id=result['parent_build_id'] or '',
                      build_request_sha256=digest, status=state)
    changes = dict(base_revision=request['base_revision'], op_id=request['op_id'], actor='Document Lead',
        summary=f'Build {name}', changes=[{'sheet': 'run', 'set': dict(run, **run_update)},
            {'sheet': 'control', 'set': {'word': str(out), 'word_sha256': artifacts['word']['sha256']}}])
    try:
        applied = register.apply(folder, changes)
    except (register.ChangeError, OSError) as exc:
        return dict(status='register_conflict' if isinstance(exc, register.ChangeError) else 'register_pending',
                    word=str(out), build_id=result['build_id'], artifacts=artifacts, error=str(exc),
                    recovery=('Read the current register and reconcile changes before retrying with its revision and a new operation ID; retain published files'
                              if isinstance(exc, register.ChangeError) else
                              'Retry the identical build after resolving the storage error; retain published files'))
    return dict(status=state, revision=applied['revision'], word=str(out), build_id=result['build_id'],
                artifacts=artifacts, checks=checks, complete=result['complete'], resumed=result['resumed'])


def bundle(folder, out):
    folder, out = Path(folder).resolve(), Path(out).resolve()
    reg = register.load(folder)
    run = reg.get('run', {})
    artifacts = run.get('artifacts', {})
    if artifacts and not {'word', 'record'} <= set(artifacts):
        raise ValueError('Word and its record must be delivered together')
    if out == folder or out in folder.parents:
        raise ValueError('bundle must not replace the register directory or its parent')
    for ref in artifacts.values():
        unchanged(ref)
    word = artifacts.get('word', {}).get('path')
    if word:
        fp_docx.read_record(artifacts['record']['path'], fp_docx.Doc(word))
        if reg['control']['word_sha256'] != artifacts['word']['sha256']:
            raise ValueError('register and Word hash differ')
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=out.parent, prefix='.fp-bundle-') as temp:
        stage = Path(temp)
        register.save(stage, reg)
        (stage / 'Client-DDQ.md').rename(stage / 'DDQ.md')
        refs = list(artifacts.values()) + ([run['draft']] if run.get('draft') else []) + run.get('support', [])
        for ref in refs:
            source = Path(unchanged(ref))
            if source.name == 'manifest.json':
                raise ValueError('manifest.json is reserved for the delivery manifest; rename the support file')
            target = stage / source.name
            if target.exists() and register.sha256(target) != ref['sha256']:
                raise ValueError(f'bundle filename conflict: {source.name}')
            shutil.copyfile(source, target)
        files = [{'path': p.name, 'sha256': register.sha256(p)} for p in sorted(stage.iterdir())]
        manifest = dict(version=version()['version'], register_revision=reg['revision'],
            build_id=run.get('build_id'), kind='paper' if word else 'evidence', delivery='local-only', files=files,
            checks=register.open_checks(reg, Path(word) if word else None),
            word_checks=fp_docx.check(word, run['template']['path']) if word else None,
            editorial=run.get('preflight', {}).get('editorial', 'pending'),
            layout='not-verified-by-tool' if word else 'not-applicable')
        (stage / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        if out.exists():
            for target in out.iterdir():
                source = stage / target.name
                if not target.is_file() or not source.is_file() or target.read_bytes() != source.read_bytes():
                    raise ValueError(f'bundle conflict: {target}')
        out.mkdir(exist_ok=True)
        try:
            for source in stage.iterdir():
                target = out / source.name
                if not target.exists():
                    fp_docx.publish(target, lambda temporary, p=source: shutil.copyfile(p, temporary))
        except OSError as exc:
            return dict(status='partial_bundle', directory=str(out), error=str(exc),
                        published=sorted(p.name for p in out.iterdir()),
                        recovery='Keep these files; retry bundle with the same register and inputs')
    return dict(status='bundled', directory=str(out), manifest=str(out / 'manifest.json'), delivery='local-only')


def version():
    here = Path(__file__).resolve().parent
    metadata = here / 'plugin.json'
    if not metadata.exists():
        metadata = here.parent / '.claude-plugin' / 'plugin.json'
    manifest = json.loads(metadata.read_text())
    return dict(name=manifest['name'], version=manifest['version'],
                scripts={p.name: register.sha256(p) for p in [here / n for n in
                    ('fp.py', 'register.py', 'fp_docx.py', 'fin_table.py')]})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', action='store_true')
    sub = parser.add_subparsers(dest='command')
    for name in ('prepare', 'build'):
        command = sub.add_parser(name)
        command.add_argument('folder')
        command.add_argument('request', help='JSON request file; see workflow-contract.md')
    sub.add_parser('status').add_argument('folder')
    command = sub.add_parser('bundle')
    command.add_argument('folder')
    command.add_argument('--out', required=True)
    args = parser.parse_args(argv)
    try:
        if args.version:
            result = version()
        elif args.command in ('prepare', 'build'):
            request = json.loads(Path(args.request).read_text(encoding='utf-8'))
            result = globals()[args.command](args.folder, request)
        elif args.command == 'status':
            result = status(args.folder)
        elif args.command == 'bundle':
            result = bundle(args.folder, args.out)
        else:
            parser.print_help()
            return 0
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if args.version or args.command == 'status' or result['status'] in ('prepared', 'built', 'bundled') else 2
    except (ValueError, KeyError, OSError, zipfile.BadZipFile, expat.ExpatError, ET.ParseError,
            register.ChangeError, fp_docx.Refuse) as exc:
        print(json.dumps({'status': 'error', 'error': str(exc)}))
        return 1


if __name__ == '__main__':
    sys.exit(main())
