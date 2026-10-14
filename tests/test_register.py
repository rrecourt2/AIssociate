import datetime
import json

import openpyxl  # dev-only independent reader; the tool itself uses the standard library
import pytest

import register as reg_tool


@pytest.fixture
def folder(tmp_path):
    reg_tool.save(tmp_path, reg_tool.new_register("Cedar"))
    return tmp_path


def change(base, op, *changes, **extra):
    return {"base_revision": base, "op_id": op, "actor": "test", "summary": op, "changes": list(changes), **extra}


RISK = {"sheet": "risks", "add": {"title": "FX mismatch", "raised_by": "E&S specialist", "rating": "high",
                                  "destination": "main", "reason": "affects repayment", "status": "open"}}


def test_ids_are_assigned_and_revision_advances(folder):
    r = reg_tool.apply(folder, change(0, "a", RISK, {"sheet": "risks", "add": dict(RISK["add"], title="Customer")}))
    assert r == {"status": "applied", "revision": 1, "ids": ["R-001", "R-002"], "warnings": []}
    assert reg_tool.load(folder)["log"][-1]["op_id"] == "a"


def test_stale_and_duplicate_change_sets(folder):
    reg_tool.apply(folder, change(0, "a", RISK))
    with pytest.raises(reg_tool.ChangeError, match="stale"):
        reg_tool.apply(folder, change(0, "b", RISK))
    assert reg_tool.apply(folder, change(0, "a", RISK))["status"] == "already-applied"
    assert len(reg_tool.load(folder)["risks"]) == 1


@pytest.mark.parametrize("bad, message", [
    ({"sheet": "mitigants", "add": {"risk": "R-009", "raised_by": "x"}}, "unknown risk"),
    ({"sheet": "mitigants", "add": {"risk": "R-001", "raised_by": "x", "verified": "yes"}}, "needs a source"),
    ({"sheet": "open_items", "add": {"text": "q", "raised_by": "x", "status": "answered"}}, "answer source"),
    ({"sheet": "risks", "add": {"title": "t", "rating": "high"}}, "who raised"),
    ({"sheet": "risks", "add": {"title": "t", "raised_by": "x", "rating": "huge"}}, "rating"),
    ({"sheet": "risks", "update": "R-001", "set": {"destination": "background"}}, "officer's decision"),
    ({"sheet": "open_items", "add": {"text": "q", "raised_by": "x", "link": "R-001", "criticality": "later"}},
     "officer_ok"),
    ({"sheet": "nonsense", "add": {}}, "unknown sheet"),
    ({"sheet": "risks", "add": {"colour": "red"}}, "no field"),
])
def test_rule_violations_reject_the_whole_change_set(folder, bad, message):
    reg_tool.apply(folder, change(0, "a", RISK))
    with pytest.raises(reg_tool.ChangeError, match=message):
        reg_tool.apply(folder, change(1, "b", {"sheet": "sources", "add": {"title": "kept?"}}, bad))
    assert reg_tool.load(folder)["sources"] == []   # nothing from the rejected set was saved


def test_downgrade_needs_officer_decision(folder):
    reg_tool.apply(folder, change(0, "a", RISK))
    with pytest.raises(reg_tool.ChangeError, match="downgrading high to medium"):
        reg_tool.apply(folder, change(1, "b", {"sheet": "risks", "update": "R-001", "set": {"rating": "medium"}}))
    ok = {"sheet": "risks", "update": "R-001",
          "set": {"rating": "medium", "officer_decision": "Officer, 2 Oct: hedge confirmed"}}
    assert reg_tool.apply(folder, change(1, "c", ok))["status"] == "applied"


def test_officer_ok_allows_later_diligence(folder):
    reg_tool.apply(folder, change(0, "a", RISK))
    item = {"text": "Check FX hedging policy", "raised_by": "credit", "link": "R-001", "criticality": "later",
            "officer_ok": "yes", "status": "open"}
    assert reg_tool.apply(folder, change(1, "b", {"sheet": "open_items", "add": item}))["status"] == "applied"


def test_ready_gate_blocks_and_word_change_invalidates(folder, tmp_path):
    word = tmp_path / "FP-v01.docx"
    word.write_bytes(b"v1")
    reg_tool.apply(folder, change(0, "a", RISK, {"sheet": "open_items", "add": {
        "text": "Borrower cash flow", "raised_by": "officer", "criticality": "blocker", "status": "open",
        "addressee": "client"}}, {"sheet": "control", "set": {"word": word.name, "word_sha256": reg_tool.sha256(word)}}))
    with pytest.raises(reg_tool.ChangeError, match="cannot record ready"):
        reg_tool.apply(folder, change(1, "b", {"sheet": "control", "set": {"status": "ready"}}))
    reg_tool.apply(folder, change(1, "c", {"sheet": "sources", "add": {
        "title": "Cash flow answer", "impact": "assessed"}}, {"sheet": "open_items", "update": "O-001",
        "set": {"status": "closed", "answer_source": "S-001 p.2", "assessment": "Reconciled to accounts",
                "assessed_by": "Analyst"}}))
    reg = reg_tool.load(folder)
    assert reg_tool.open_checks(reg, word) == []
    word.write_bytes(b"v1 edited by officer")
    assert reg_tool.open_checks(reg, word) == ["the Word file changed since it was last recorded"]


def test_new_source_with_pending_impact_blocks_ready(folder):
    reg_tool.apply(folder, change(0, "a", {"sheet": "sources", "add": {"title": "Lender email: covenant breach",
                                                                       "impact": "pending", "tier": "A"}}))
    reasons = reg_tool.open_checks(reg_tool.load(folder))
    assert reasons == ["source impact not assessed: S-001", "critical sources not fully read: S-001"]


def test_stale_sources_warning(folder):
    old = (datetime.date.today() - datetime.timedelta(days=500)).isoformat()
    reg_tool.apply(folder, change(0, "a", {"sheet": "sources", "add": {"title": "AR 2023", "event_date": old}},
                                  {"sheet": "fp_map", "add": {"version": "v01", "section": "summary", "ids": "S-001"}}))
    assert any(p[1] == "stale-sources" for p in reg_tool.problems(reg_tool.load(folder)))


def test_analysis_upsert_and_markdown_view(folder):
    reg_tool.apply(folder, change(0, "a", {"sheet": "analysis", "update": "timeline",
                                           "set": {"title": "Last two years", "text": "2025: new plant."}}))
    reg_tool.apply(folder, change(1, "b", {"sheet": "analysis", "update": "timeline", "set": {"text": "2026: CFO left."}}))
    md = (folder / "Analysis.md").read_text()
    assert "2026: CFO left." in md and "2025: new plant." not in md and "revision 2" in md


def test_excel_view_opens_in_an_independent_reader(folder):
    reg_tool.apply(folder, change(0, "a", RISK))
    wb = openpyxl.load_workbook(folder / "register.xlsx")
    assert wb.sheetnames[:3] == ["Control", "Sources", "Risks"]
    assert wb["Risks"]["A2"].value == "R-001" and wb["Risks"]["B2"].value == "FX mismatch"
    assert wb["Control"]["B2"].value == "Cedar"


def test_summary_lists_show_and_cli(folder, tmp_path, capsys):
    reg_tool.apply(folder, change(0, "a", RISK, {"sheet": "open_items", "add": {
        "text": "Revenue split by currency", "raised_by": "officer", "link": "R-001", "criticality": "blocker",
        "status": "open", "addressee": "client", "due": "2026-10-10"}},
        {"sheet": "mitigants", "add": {"risk": "R-001", "text": "Hedging covenant", "type": "proposed-condition",
                                       "raised_by": "credit"}}, next_step="Grill v01 in a new task"))
    reg = reg_tool.load(folder)
    text = reg_tool.summary(reg)
    assert "Next: Grill v01 in a new task" in text and "O-001 [blocker] client" in text
    assert len(text.splitlines()) <= 40
    assert "Revenue split by currency" in reg_tool.lists(reg) and "M-001 (R-001)" in reg_tool.lists(reg)
    assert "mitigant M-001" in reg_tool.show(reg, ["R-001"])
    changes = tmp_path / "c.json"
    changes.write_text(json.dumps(change(1, "cli", {"sheet": "control", "set": {"officer": "Rik"}})))
    assert reg_tool.main(["apply", str(folder), str(changes)]) == 0
    assert reg_tool.main(["apply", str(folder), str(changes)]) == 0   # retry is a no-op
    assert reg_tool.load(folder)["revision"] == 2


def test_new_questions_default_open_and_new_sources_pending(folder):
    reg_tool.apply(folder, change(0, "a", {"sheet": "open_items", "add": {"text": "Borrower forecast", "raised_by": "officer"}},
                                  {"sheet": "sources", "add": {"title": "Email from CFO"}}))
    reg = reg_tool.load(folder)
    assert reg["open_items"][0]["status"] == "open" and reg["sources"][0]["impact"] == "pending"
    assert "O-001" in reg_tool.lists(reg)


def test_promised_and_answered_items_stay_visible_until_closed(folder):
    reg_tool.apply(folder, change(0, "a", {"sheet": "open_items", "add": {
        "text": "Monthly borrower forecast", "raised_by": "officer", "criticality": "blocker", "addressee": "client",
        "audience": "client"}}))
    # "We will send the forecast on Friday" is a promise, not the forecast.
    reg_tool.apply(folder, change(1, "b", {"sheet": "open_items", "update": "O-001", "set": {
        "status": "promised", "answer": "CFO: will send Friday", "due": "2026-10-09"}}))
    reg = reg_tool.load(folder)
    assert "O-001" in reg_tool.lists(reg) and any("O-001" in r for r in reg_tool.gates(reg))
    reg_tool.apply(folder, change(2, "c", {"sheet": "sources", "add": {"title": "Forecast", "impact": "assessed"}},
        {"sheet": "open_items", "update": "O-001", "set": {"status": "answered", "answer_source": "S-001 tab Cash flow"}}))
    reg = reg_tool.load(folder)
    assert "awaiting assessment" in reg_tool.lists(reg) and any("O-001" in r for r in reg_tool.gates(reg))
    client_requests, internal = reg_tool.lists(reg).split('## Internal open points')
    assert 'O-001' not in client_requests and 'O-001' in internal
    assert 'O-001' not in reg_tool.ddq(reg)
    reg_tool.apply(folder, change(3, "d", {"sheet": "open_items", "update": "O-001", "set": {
        "status": "closed", "assessment": "Forecast reviewed against accounts", "assessed_by": "Analyst"}}))
    reg = reg_tool.load(folder)
    assert len(reg['open_items']) == 1
    assert "O-001" not in reg_tool.lists(reg) and reg_tool.gates(reg) == []


def test_tool_reports_checks_and_readiness_is_recorded_for_a_version(folder, tmp_path):
    word = tmp_path / "FP-v05.docx"
    word.write_bytes(b"v5")
    reg_tool.apply(folder, change(0, "a", {"sheet": "control", "set": {"word": word.name, "word_sha256": reg_tool.sha256(word)}}))
    assert "Register checks: passed" in reg_tool.summary(reg_tool.load(folder), word)
    reg_tool.apply(folder, change(1, "b", {"sheet": "control", "set": {"status": "ready", "ready_by": "Officer"}}))
    reg = reg_tool.load(folder)
    assert reg["control"]["ready_for"] == f"{word.name} at register revision 2"
    assert "Status: ready (FP-v05.docx at register revision 2, recorded by Officer)" in reg_tool.summary(reg, word)
    word.write_bytes(b"v5 edited")
    assert "changed since readiness was recorded" in reg_tool.summary(reg, word)


def test_retry_repairs_views_left_stale_by_an_interrupted_run(folder, monkeypatch):
    real = reg_tool.write_views
    monkeypatch.setattr(reg_tool, "write_views", lambda *a: (_ for _ in ()).throw(OSError("disk full")))
    with pytest.raises(OSError):
        reg_tool.apply(folder, change(0, "a", RISK))
    monkeypatch.setattr(reg_tool, "write_views", real)
    assert "revision 0" in (folder / "Analysis.md").read_text()      # views are stale, the record is not
    assert reg_tool.apply(folder, change(0, "a", RISK))["status"] == "already-applied"
    assert "revision 1" in (folder / "Analysis.md").read_text()


def test_new_evidence_after_ready_withdraws_readiness_instead_of_blocking(folder):
    record_word(folder)
    reg_tool.apply(folder, change(1, "a", {"sheet": "control", "set": {"status": "ready", "ready_by": "FP Lead"}}))
    r = reg_tool.apply(folder, change(2, "b", {"sheet": "sources", "add": {"title": "Lender email: covenant breach"}}))
    assert r["status"] == "applied" and r["warnings"][0].startswith("readiness withdrawn")
    assert reg_tool.load(folder)["control"]["status"] == "draft"


def record_word(folder, revision=0):
    word = folder / 'FP.docx'
    word.write_bytes(b'current synthetic Word version')
    reg_tool.apply(folder, change(revision, 'word', {'sheet': 'control', 'set': {
        'word': word.name, 'word_sha256': reg_tool.sha256(word)}}))
    return word


def test_findings_default_open_and_block_readiness(folder):
    reg_tool.apply(folder, change(0, 'finding', {'sheet': 'findings', 'add': {
        'by': 'grill', 'issue': 'Unsupported conclusion', 'priority': 'blocker'}}))
    reg = reg_tool.load(folder)
    assert reg['findings'][0]['status'] == 'open'
    assert reg_tool.gates(reg) == ['open blockers: G-001']


@pytest.mark.parametrize('sheet, fields, field', [
    ('sources', {'title': 'Evidence'}, 'impact'),
    ('sources', {'title': 'Evidence'}, 'coverage'),
    ('risks', RISK['add'], 'status'),
    ('open_items', {'text': 'Question', 'raised_by': 'officer', 'criticality': 'blocker'}, 'status'),
    ('open_items', {'text': 'Question', 'raised_by': 'officer', 'criticality': 'blocker'}, 'criticality'),
    ('findings', {'by': 'grill', 'priority': 'blocker'}, 'status'),
    ('findings', {'by': 'grill', 'priority': 'blocker'}, 'priority'),
])
def test_lifecycle_or_blocker_fields_cannot_be_cleared(folder, sheet, fields, field):
    result = reg_tool.apply(folder, change(0, 'add', {'sheet': sheet, 'add': fields}))
    with pytest.raises(reg_tool.ChangeError, match=field):
        reg_tool.apply(folder, change(1, 'clear', {'sheet': sheet, 'update': result['ids'][0], 'set': {field: ''}}))
    assert reg_tool.load(folder)['revision'] == 1


@pytest.mark.parametrize('fields', [
    {'status': 'ready'},
    {'status': 'ready', 'ready_by': '  '},
    {'status': 'ready', 'ready_by': 'Officer', 'word': '', 'word_sha256': ''},
    {'status': 'ready', 'ready_by': 'Officer', 'word_sha256': 'old'},
    {'status': 'ready', 'ready_by': 'Officer', 'word': 'missing.docx'},
])
def test_ready_requires_explicit_officer_and_current_word(folder, fields):
    record_word(folder)
    with pytest.raises(reg_tool.ChangeError, match='cannot record ready'):
        reg_tool.apply(folder, change(1, 'ready', {'sheet': 'control', 'set': fields}, actor='Automation'))
    assert reg_tool.load(folder)['control']['status'] == 'draft'


@pytest.mark.parametrize('edit', ['evidence', 'word_metadata', 'word_bytes'])
def test_ready_invalidated_on_assessed_evidence_or_word_changes(folder, edit):
    word = record_word(folder)
    reg_tool.apply(folder, change(1, 'ready', {'sheet': 'control', 'set': {'status': 'ready', 'ready_by': 'Officer'}}))
    changes = []
    if edit == 'evidence':
        changes = [{'sheet': 'sources', 'add': {'title': 'New facts', 'impact': 'assessed'}}]
    else:
        word.write_bytes(b'changed Word')
        if edit == 'word_metadata':
            changes = [{'sheet': 'control', 'set': {'word_sha256': reg_tool.sha256(word)}}]
        else:
            text = reg_tool.summary(reg_tool.load(folder), word)
            assert 'Status: ready' not in text
            assert 'changed since readiness was recorded' in text
    result = reg_tool.apply(folder, change(2, 'changed', *changes))
    assert result['warnings'][0].startswith('readiness withdrawn')
    assert reg_tool.load(folder)['control']['status'] == 'draft'


def test_views_have_revision_and_partial_save_is_honest(folder, monkeypatch, capsys):
    changes = folder / 'changes.json'
    changes.write_text(json.dumps(change(0, 'save', RISK)))
    original = reg_tool.write_views
    monkeypatch.setattr(reg_tool, 'write_views', lambda *a: (_ for _ in ()).throw(OSError('disk full')))
    assert reg_tool.main(['apply', str(folder), str(changes)]) == 4
    err = capsys.readouterr().err
    assert 'saved' in err.lower() and 'views incomplete' in err.lower() and 'REFUSED' not in err
    monkeypatch.setattr(reg_tool, 'write_views', original)
    assert reg_tool.main(['apply', str(folder), str(changes)]) == 0
    wb = openpyxl.load_workbook(folder / 'register.xlsx')
    control = dict(wb['Control'].values)
    assert control['register_revision'] == 1
    assert 'revision 1' in (folder / 'Analysis.md').read_text()


@pytest.mark.parametrize('bad, message', [
    ({'sheet': 'risks', 'add': {'title': 'risk', 'raised_by': '  '}}, 'who raised'),
    ({'sheet': 'mitigants', 'add': {'risk': 'R-001', 'raised_by': 'x', 'verified': 'yes', 'source': '  '}}, 'needs a source'),
    ({'sheet': 'open_items', 'add': {'text': 'q', 'raised_by': 'x', 'status': 'closed', 'answer_source': '  '}}, 'answer source'),
    ({'sheet': 'risks', 'update': 'R-001', 'set': {'rating': 'medium', 'officer_decision': '  '}}, "officer's decision"),
])
def test_blank_required_evidence_and_decisions_are_refused(folder, bad, message):
    reg_tool.apply(folder, change(0, 'risk', RISK))
    with pytest.raises(reg_tool.ChangeError, match=message):
        reg_tool.apply(folder, change(1, 'bad', bad))
    assert reg_tool.load(folder)['revision'] == 1


def test_blocker_awaiting_officer_judgment_still_blocks_readiness(folder):
    record_word(folder)
    reg_tool.apply(folder, change(1, 'finding', {'sheet': 'findings', 'add': {
        'by': 'grill', 'issue': 'Repayment depends on unsigned refinancing',
        'priority': 'blocker', 'status': 'officer-judgment'}}))
    assert 'G-001' in '; '.join(reg_tool.gates(reg_tool.load(folder)))
    assert 'Findings: 1 unresolved' in reg_tool.summary(reg_tool.load(folder))
    with pytest.raises(reg_tool.ChangeError, match='open blockers: G-001'):
        reg_tool.apply(folder, change(2, 'ready', {'sheet': 'control', 'set': {
            'status': 'ready', 'ready_by': 'Officer'}}))


@pytest.mark.parametrize('payload', [[], {'changes': None}, {'changes': [None]},
    {'changes': [{'sheet': 'sources', 'add': None}]},
    {'changes': [{'sheet': 'sources', 'add': {'title': None}}]}])
def test_malformed_change_sets_are_refused_without_writing(folder, payload):
    if isinstance(payload, dict):
        payload = dict(base_revision=0, op_id='bad', **payload)
    with pytest.raises(reg_tool.ChangeError):
        reg_tool.apply(folder, payload)
    assert reg_tool.load(folder)['revision'] == 0


def test_risk_analysis_does_not_hide_risk_and_linked_items(folder):
    reg_tool.apply(folder, change(0, 'linked', RISK,
        {'sheet': 'analysis', 'add': {'id': 'R-001', 'text': 'Detailed FX exposure.'}},
        {'sheet': 'open_items', 'add': {'text': 'Confirm hedge', 'link': 'R-001', 'raised_by': 'officer'}}))
    shown = reg_tool.show(reg_tool.load(folder), ['R-001'])
    assert 'R-001 (risks)' in shown
    assert 'Confirm hedge' in shown and 'Detailed FX exposure.' in shown


def test_retry_rejects_reused_id_with_changed_payload(folder):
    reg_tool.apply(folder, change(0, 'same', RISK))
    with pytest.raises(reg_tool.ChangeError, match='different payload'):
        reg_tool.apply(folder, change(0, 'same', dict(RISK, add=dict(RISK['add'], title='Other risk'))))
    assert reg_tool.load(folder)['revision'] == 1


def test_ddq_uses_explicit_audience_and_never_recipient_keywords(folder):
    for i, audience in enumerate(['unknown', 'internal', 'restricted', 'client']):
        reg_tool.apply(folder, change(i, str(i), {'sheet': 'open_items', 'add': {
            'text': audience + ' request', 'raised_by': 'officer', 'addressee': 'client team',
            'audience': audience, 'purpose': 'Diligence'}}))
    exported = reg_tool.ddq(reg_tool.load(folder))
    assert 'client request' in exported
    assert all(a + ' request' not in exported for a in ['unknown', 'internal', 'restricted'])
    assert 'client request' in (folder / 'Client-DDQ.md').read_text()


@pytest.mark.parametrize('fields,match', [
    ({'answer_source': 'S-999 p.4', 'assessment': 'Checked', 'assessed_by': 'Analyst'}, 'unknown source'),
    ({'answer_source': 'S-001', 'assessment': 'Checked', 'assessed_by': 'Analyst'}, 'locator'),
    ({'answer_source': 'S-001 p.4'}, 'assessment'),
    ({'answer_source': 'S-001 p.4', 'assessment': 'Checked'}, 'assessor'),
])
def test_closure_requires_located_existing_evidence_and_assessment(folder, fields, match):
    reg_tool.apply(folder, change(0, 'source', {'sheet': 'sources', 'add': {'title': 'Answer'}}))
    with pytest.raises(reg_tool.ChangeError, match=match):
        reg_tool.apply(folder, change(1, 'close', {'sheet': 'open_items', 'add': {
            'text': 'Confirm forecast', 'raised_by': 'Officer', 'status': 'closed', **fields}}))


def test_accepted_gap_is_closed_by_attributed_decision_without_invented_answer(folder):
    reg_tool.apply(folder, change(0, 'gap', {'sheet': 'open_items', 'add': {
        'text': 'Forecast unavailable', 'raised_by': 'Officer', 'status': 'closed',
        'assessment': 'Forecast remains unavailable; proceeding with downside case',
        'assessed_by': 'Analyst', 'officer_decision': 'Rik, 2026-10-14: accept remaining gap'}}))
    row = reg_tool.load(folder)['open_items'][0]
    assert row['answer_source'] == '' and row['status'] == 'closed'
    assert row['officer_decision'] in reg_tool.show(reg_tool.load(folder), ['O-001'])


def test_proposed_verified_condition_is_not_implemented_protection(folder):
    reg_tool.apply(folder, change(0, 'risk', RISK, {'sheet': 'sources', 'add': {'title': 'Term sheet'}}))
    with pytest.raises(reg_tool.ChangeError, match='existing verified mitigant'):
        reg_tool.apply(folder, change(1, 'condition', {'sheet': 'mitigants', 'add': {
            'risk': 'R-001', 'type': 'proposed-condition', 'verified': 'yes', 'raised_by': 'officer',
            'source': 'S-001 p.2'}}, {'sheet': 'open_items', 'add': {
            'text': 'Check hedge', 'link': 'R-001', 'criticality': 'later', 'raised_by': 'officer'}}))


def test_unread_critical_evidence_allows_draft_but_blocks_readiness(folder):
    reg_tool.apply(folder, change(0, 'draft', {'sheet': 'sources', 'add': {
        'title': 'Accounts', 'tier': 'A', 'impact': 'assessed'}}))
    assert reg_tool.load(folder)['revision'] == 1
    assert 'critical sources not fully read: S-001' in reg_tool.gates(reg_tool.load(folder))


def test_analysis_export_retains_provenance_and_update_metadata(folder):
    reg_tool.apply(folder, change(0, 'analysis', {'sheet': 'sources', 'add': {'title': 'Accounts'}},
        {'sheet': 'analysis', 'add': {'id': 'liquidity', 'text': 'Cash is constrained.', 'sources': 'S-001 p.8'}}))
    row = reg_tool.load(folder)['analysis'][0]
    assert row['updated']
    md = (folder / 'Analysis.md').read_text()
    assert 'S-001 p.8' in md and row['updated'] in md and 'Cash is constrained.' in md


def test_explicit_migration_preserves_bytes_ids_history_and_refuses_legacy_replay(folder):
    reg_tool.apply(folder, change(0, 'legacy', RISK))
    legacy = reg_tool.load(folder)
    legacy.pop('schema_version', None)
    legacy.pop('claims', None)
    legacy.pop('run', None)
    legacy['log'][0].pop('request_sha256', None)
    raw = json.dumps(legacy, separators=(',', ':')).encode()
    (folder / 'register.json').write_bytes(raw)
    with pytest.raises(reg_tool.ChangeError, match='migrate'):
        reg_tool.load(folder)
    result = reg_tool.migrate(folder)
    assert (folder / 'register.schema-0.backup.json').read_bytes() == raw
    migrated = reg_tool.load(folder)
    assert migrated['schema_version'] == 1 and migrated['revision'] == legacy['revision']
    assert migrated['risks'][0]['id'] == 'R-001' and migrated['log'] == legacy['log']
    assert result['status'] == 'migrated'
    assert reg_tool.migrate(folder)['status'] == 'already-migrated'
    with pytest.raises(reg_tool.ChangeError, match='legacy.*refresh'):
        reg_tool.apply(folder, change(0, 'legacy', RISK))
    (folder / 'Analysis.md').unlink()
    assert reg_tool.refresh(folder)['status'] == 'refreshed'
    assert (folder / 'Analysis.md').exists()


def test_run_update_is_typed_and_uses_normal_revision_and_digest(folder):
    payload = {'base': {'path': '/base.docx', 'sha256': 'a' * 64}, 'mode': 'existing',
               'provenance': 'Officer authorised this imported draft', 'examples': [], 'output_dir': '/out'}
    req = change(0, 'prepare', {'sheet': 'run', 'set': payload})
    reg_tool.apply(folder, req)
    assert reg_tool.load(folder)['run']['base'] == payload['base']
    assert reg_tool.apply(folder, req)['status'] == 'already-applied'
    for fields in [{'mode': 'reset'}, {'arbitrary': {}}, {'examples': ['wrong']}, {'base': {'path': 4}}]:
        with pytest.raises(reg_tool.ChangeError):
            reg_tool.apply(folder, change(1, 'bad', {'sheet': 'run', 'set': fields}))


def test_source_hash_change_requires_a_new_source_id(folder):
    source = folder / 'accounts.txt'
    source.write_text('Revenue: 100')
    fields = {'title': 'Accounts', 'link': source.name, 'sha256': reg_tool.sha256(source),
              'reviewed_scope': 'whole report', 'extract_path': 'accounts-extract.txt', 'coverage': 'read'}
    reg_tool.apply(folder, change(0, 'source', {'sheet': 'sources', 'add': fields}))
    source.write_text('Revenue: 80')
    with pytest.raises(reg_tool.ChangeError, match='new source ID'):
        reg_tool.apply(folder, change(1, 'overwrite', {'sheet': 'sources', 'update': 'S-001',
                                                   'set': {'sha256': reg_tool.sha256(source)}}))


def test_correction_retains_conflicts_and_marks_explicit_links_for_recheck(folder):
    reg_tool.apply(folder, change(0, 'original', {'sheet': 'sources', 'add': {'title': 'Accounts', 'version': '2025'}},
        {'sheet': 'claims', 'add': {'assertion': 'Revenue grew', 'kind': 'fact', 'sources': 'S-001 p.4',
                                  'sections': 'financial-analysis', 'support': 'supported'}},
        {'sheet': 'analysis', 'add': {'id': 'earnings', 'text': 'Growth supports debt service', 'claims': 'C-001'}},
        {'sheet': 'fp_map', 'add': {'version': 'v01', 'section': 'financial-analysis', 'ids': 'C-001'}}))
    reg_tool.apply(folder, change(1, 'correction', {'sheet': 'sources', 'add': {
        'title': 'Corrected accounts', 'version': '2025 corrected', 'supersedes': 'S-001'}},
        {'sheet': 'claims', 'add': {'assertion': 'Revenue fell', 'kind': 'fact', 'sources': 'S-002 p.4',
            'sections': 'financial-analysis', 'support': 'contested', 'qualifications': 'Conflicts with C-001'}}))
    reg = reg_tool.load(folder)
    assert len(reg['claims']) == 2 and len(reg['sources']) == 2
    assert reg['claims'][0]['recheck'] == reg['analysis'][0]['recheck'] == reg['fp_map'][0]['recheck'] == 'yes'
    selected = reg_tool.show(reg, [], section='financial-analysis')
    assert all(text in selected for text in ['Revenue grew', 'Revenue fell', 'S-001 p.4', 'S-002 p.4',
                                             'Growth supports debt service', 'contested', 'not a complete'])
    assert 'source impact not assessed: S-001, S-002' in reg_tool.gates(reg)


def test_new_unlinked_adverse_source_still_has_pending_whole_case_impact(folder):
    reg_tool.apply(folder, change(0, 'adverse', {'sheet': 'sources', 'add': {'title': 'Covenant breach email'}}))
    assert 'source impact not assessed: S-001' in reg_tool.gates(reg_tool.load(folder))


@pytest.mark.parametrize('fields,match', [
    ({'assertion': 'Cash', 'kind': 'fact', 'sources': 'S-999 p.2'}, 'unknown source'),
    ({'assertion': 'Cash', 'kind': 'fact', 'sources': 'S-001'}, 'locator'),
    ({'assertion': 'EBITDA', 'kind': 'calculation', 'sources': 'S-001 p.2', 'value': '20'}, 'unit'),
])
def test_claims_validate_sources_and_applicable_numeric_provenance(folder, fields, match):
    reg_tool.apply(folder, change(0, 'source', {'sheet': 'sources', 'add': {'title': 'Accounts'}}))
    with pytest.raises(reg_tool.ChangeError, match=match):
        reg_tool.apply(folder, change(1, 'claim', {'sheet': 'claims', 'add': fields}))


def test_run_record_reference_and_bad_nested_preflight_are_validated(folder):
    record = {'path': 'FP-v01.sections.json', 'sha256': 'b' * 64}
    reg_tool.apply(folder, change(0, 'record', {'sheet': 'run', 'set': {'record': record}}))
    assert reg_tool.load(folder)['run']['record'] == record
    with pytest.raises(reg_tool.ChangeError):
        reg_tool.apply(folder, change(1, 'bad', {'sheet': 'run', 'set': {'preflight': {'editorial': {}}}}))


def test_section_selection_follows_analysis_and_retains_explicit_contradiction(folder):
    reg_tool.apply(folder, change(0, 'case',
        {'sheet': 'sources', 'add': {'title': 'Original'}},
        {'sheet': 'sources', 'add': {'title': 'Contrary evidence'}},
        {'sheet': 'claims', 'add': {'assertion': 'Demand is strong', 'kind': 'fact', 'sources': 'S-001 p.1'}},
        {'sheet': 'claims', 'add': {'assertion': 'Orders cancelled', 'kind': 'fact', 'sources': 'S-002 p.7',
                                  'qualifications': 'Contradicts C-001'}},
        {'sheet': 'analysis', 'add': {'id': 'market', 'text': 'Market case', 'claims': 'C-001'}},
        {'sheet': 'fp_map', 'add': {'version': 'v1', 'section': 'market-risk', 'ids': 'market'}}))
    selected = reg_tool.show(reg_tool.load(folder), [], section='market-risk')
    assert 'Demand is strong' in selected and 'Orders cancelled' in selected and 'S-002 p.7' in selected


def test_invalid_fp_map_analysis_reference_is_rejected(folder):
    with pytest.raises(reg_tool.ChangeError, match='unknown ids'):
        reg_tool.apply(folder, change(0, 'bad', {'sheet': 'fp_map', 'add': {
            'version': 'v1', 'section': 'summary', 'ids': 'nonexistent-analysis'}}))


def test_schema_migration_can_repair_views_after_master_commit(folder, monkeypatch):
    reg = reg_tool.load(folder)
    reg.pop('schema_version')
    raw = json.dumps(reg).encode()
    (folder / 'register.json').write_bytes(raw)
    original = reg_tool.write_views
    monkeypatch.setattr(reg_tool, 'write_views', lambda *a: (_ for _ in ()).throw(OSError('disk full')))
    with pytest.raises(reg_tool.ViewsIncompleteError):
        reg_tool.migrate(folder)
    assert reg_tool.load(folder)['schema_version'] == 1
    monkeypatch.setattr(reg_tool, 'write_views', original)
    assert reg_tool.migrate(folder)['status'] == 'already-migrated'
    assert (folder / 'register.schema-0.backup.json').read_bytes() == raw


def test_source_supersession_cannot_rewrite_an_older_version_to_point_forward(folder):
    reg_tool.apply(folder, change(0, 'sources', {'sheet': 'sources', 'add': {'title': 'Original'}},
                                 {'sheet': 'sources', 'add': {'title': 'Correction', 'supersedes': 'S-001'}}))
    with pytest.raises(reg_tool.ChangeError, match='earlier source'):
        reg_tool.apply(folder, change(1, 'cycle', {'sheet': 'sources', 'update': 'S-001',
                                               'set': {'supersedes': 'S-002'}}))


def test_recheck_can_be_completed_in_one_assessment_without_reopening_links(folder):
    reg_tool.apply(folder, change(0, 'original', {'sheet': 'sources', 'add': {'title': 'Accounts'}},
        {'sheet': 'claims', 'add': {'assertion': 'Stable revenue', 'kind': 'fact', 'sources': 'S-001 p.1'}},
        {'sheet': 'analysis', 'add': {'id': 'earnings', 'text': 'Initial view', 'claims': 'C-001'}},
        {'sheet': 'fp_map', 'add': {'version': 'v1', 'section': 'summary', 'ids': 'earnings'}}))
    reg_tool.apply(folder, change(1, 'correction', {'sheet': 'sources', 'add': {
        'title': 'Correction', 'supersedes': 'S-001'}}))
    reg_tool.apply(folder, change(2, 'reviewed',
        {'sheet': 'sources', 'update': 'S-001', 'set': {'impact': 'assessed'}},
        {'sheet': 'sources', 'update': 'S-002', 'set': {'impact': 'assessed'}},
        {'sheet': 'claims', 'update': 'C-001', 'set': {'recheck': 'no'}},
        {'sheet': 'analysis', 'update': 'earnings', 'set': {'recheck': 'no'}},
        {'sheet': 'fp_map', 'update': 'v1/summary', 'set': {'recheck': 'no'}}))
    assert reg_tool.gates(reg_tool.load(folder)) == []


def test_calculation_source_inputs_and_analysis_edits_mark_sections_for_recheck(folder):
    reg_tool.apply(folder, change(0, 'original', {'sheet': 'sources', 'add': {'title': 'Accounts'}},
        {'sheet': 'claims', 'add': {'assertion': 'Margin', 'kind': 'calculation', 'value': '20',
            'unit': '%', 'entity': 'Cedar', 'period': '2025', 'definition': 'EBITDA margin',
            'inputs': 'S-001 p.3: EBITDA 20 / revenue 100', 'method': 'EBITDA / revenue * 100'}},
        {'sheet': 'analysis', 'add': {'id': 'earnings', 'text': 'Initial view', 'claims': 'C-001'}},
        {'sheet': 'fp_map', 'add': {'version': 'v1', 'section': 'summary', 'ids': 'earnings'}}))
    reg_tool.apply(folder, change(1, 'correction', {'sheet': 'sources', 'add': {
        'title': 'Correction', 'supersedes': 'S-001'}}))
    reg = reg_tool.load(folder)
    assert reg['claims'][0]['recheck'] == reg['analysis'][0]['recheck'] == reg['fp_map'][0]['recheck'] == 'yes'
    reg_tool.apply(folder, change(2, 'analysis-edit',
        {'sheet': 'analysis', 'update': 'earnings', 'set': {'text': 'Materially revised view'}},
        {'sheet': 'fp_map', 'update': 'v1/summary', 'set': {'recheck': 'no'}}))
    assert reg_tool.load(folder)['fp_map'][0]['recheck'] == 'yes'


def test_calculation_claim_inputs_recheck_and_select_their_located_evidence(folder):
    reg_tool.apply(folder, change(0, 'original', {'sheet': 'sources', 'add': {'title': 'Accounts'}},
        {'sheet': 'claims', 'add': {'assertion': 'Revenue is 100', 'kind': 'fact', 'sources': 'S-001 p.3'}},
        {'sheet': 'claims', 'add': {'assertion': 'Debt service coverage', 'kind': 'calculation', 'value': '2',
            'unit': 'x', 'entity': 'Cedar', 'period': '2025', 'definition': 'DSCR',
            'inputs': 'C-001 / 50', 'method': 'Cash flow / debt service', 'sections': 'repayment'}},
        {'sheet': 'analysis', 'add': {'id': 'repayment-case', 'text': 'Repayment analysis', 'claims': 'C-002'}},
        {'sheet': 'fp_map', 'add': {'version': 'v1', 'section': 'repayment', 'ids': 'repayment-case'}}))
    reg_tool.apply(folder, change(1, 'correction', {'sheet': 'sources', 'add': {
        'title': 'Correction', 'supersedes': 'S-001'}}))
    reg = reg_tool.load(folder)
    assert all(r['recheck'] == 'yes' for name in ['claims', 'analysis', 'fp_map'] for r in reg[name])
    selected = reg_tool.show(reg, [], section='repayment')
    assert 'Revenue is 100' in selected and 'S-001 p.3' in selected


def test_calculation_direct_source_input_needs_locator(folder):
    reg_tool.apply(folder, change(0, 'source', {'sheet': 'sources', 'add': {'title': 'Accounts'}}))
    with pytest.raises(reg_tool.ChangeError, match='locator'):
        reg_tool.apply(folder, change(1, 'bad', {'sheet': 'claims', 'add': {
            'assertion': 'Revenue', 'kind': 'calculation', 'value': '100', 'unit': 'EUR m',
            'entity': 'Cedar', 'period': '2025', 'definition': 'Revenue', 'inputs': 'S-001', 'method': 'Extract'}}))


def test_migrated_analysis_recheck_is_valid_unknown_and_blocks_readiness(folder):
    reg_tool.apply(folder, change(0, 'analysis', {'sheet': 'analysis', 'add': {'id': 'strategy', 'text': 'Case'}},
        {'sheet': 'fp_map', 'add': {'version': 'v1', 'section': 'summary', 'ids': 'strategy'}}))
    legacy = reg_tool.load(folder)
    legacy.pop('schema_version')
    legacy['analysis'][0].pop('recheck')
    legacy['fp_map'][0].pop('recheck')
    (folder / 'register.json').write_text(json.dumps(legacy))
    reg_tool.migrate(folder)
    reg = reg_tool.load(folder)
    assert reg['analysis'][0]['recheck'] == reg['fp_map'][0]['recheck'] == 'unknown'
    assert not [p for p in reg_tool.problems(reg) if p[0] == 'error']
    assert 'analysis to recheck: strategy' in reg_tool.gates(reg)
    assert 'fp_map to recheck: v1/summary' in reg_tool.gates(reg)


def test_run_set_replaces_prior_run_so_prepare_clears_stale_build_state(folder):
    reg_tool.apply(folder, change(0, 'old-build', {'sheet': 'run', 'set': {
        'mode': 'normal', 'build_id': 'old-build', 'draft': {'path': 'draft.md', 'sha256': 'a' * 64},
        'artifacts': {'word': {'path': 'old.docx', 'sha256': 'b' * 64}}}}))
    reg_tool.apply(folder, change(1, 'prepare', {'sheet': 'run', 'set': {'mode': 'existing', 'status': 'prepared'}}))
    assert reg_tool.load(folder)['run'] == {'mode': 'existing', 'status': 'prepared'}


def test_workbook_view_bytes_do_not_depend_on_zip_creation_time(tmp_path, monkeypatch):
    import zipfile
    sheets = [('Control', ['field', 'value'], [['deal', 'Synthetic']])]
    first, second = tmp_path / 'first.xlsx', tmp_path / 'second.xlsx'
    monkeypatch.setattr(zipfile.time, 'localtime', lambda *a: (2026, 10, 14, 10, 0, 0, 2, 287, 0))
    reg_tool.write_xlsx(first, sheets)
    monkeypatch.setattr(zipfile.time, 'localtime', lambda *a: (2026, 10, 14, 10, 0, 4, 2, 287, 0))
    reg_tool.write_xlsx(second, sheets)
    assert first.read_bytes() == second.read_bytes()
    assert openpyxl.load_workbook(second)['Control']['B2'].value == 'Synthetic'


def test_section_selection_keeps_risk_analysis_provenance_and_recheck(folder):
    reg_tool.apply(folder, change(0, 'risk-analysis', RISK,
        {'sheet': 'sources', 'add': {'title': 'Accounts', 'impact': 'assessed'}},
        {'sheet': 'analysis', 'add': {'id': 'R-001', 'text': 'Cash is constrained.',
                                    'sources': 'S-001 p.77', 'recheck': 'yes'}},
        {'sheet': 'fp_map', 'add': {'version': 'v1', 'section': 'liquidity', 'ids': 'R-001'}}))
    reg = reg_tool.load(folder)
    selected = reg_tool.show(reg, [], section='liquidity')
    assert all(text in selected for text in ['R-001 (risks)', 'Cash is constrained.', 'S-001 p.77',
                                            'recheck: yes', reg['analysis'][0]['updated']])


@pytest.mark.parametrize('coverage,expected_status', [('unread', 'draft'), ('read', 'ready')])
def test_migration_withdraws_invalid_readiness_but_keeps_historical_decision(folder, coverage, expected_status):
    word = record_word(folder)
    reg_tool.apply(folder, change(1, 'critical', {'sheet': 'sources', 'add': {
        'title': 'Critical accounts', 'tier': 'A', 'coverage': coverage, 'impact': 'assessed'}}))
    legacy = reg_tool.load(folder)
    legacy.pop('schema_version')
    legacy['control'].update(status='ready', ready_by='Historical officer',
                             ready_for='FP.docx at register revision 2')
    raw = json.dumps(legacy).encode()
    (folder / 'register.json').write_bytes(raw)
    reg_tool.migrate(folder)
    migrated = reg_tool.load(folder)
    assert migrated['control']['status'] == expected_status
    assert migrated['control']['ready_by'] == legacy['control']['ready_by']
    assert migrated['control']['ready_for'] == legacy['control']['ready_for']
    assert migrated['log'] == legacy['log'] and migrated['revision'] == legacy['revision']
    assert (folder / 'register.schema-0.backup.json').read_bytes() == raw
    if coverage == 'unread':
        assert 'Status: ready' not in reg_tool.summary(migrated, word)
