"""Synthetic tool integration; does not evaluate model writing or tenant persistence."""
import json

import docx

import fin_table
import fp_docx
from word_fixtures import edit_text, make_template
import register


def test_partial_fp_financial_table_register_and_later_update(tmp_path):
    template, partial = (tmp_path / name for name in ('template.docx', 'partial.docx'))
    make_template(template)
    make_template(partial)
    edit_text(partial, '[Summarise the proposal]', 'Existing company account.')
    original = partial.read_bytes()
    spread = tmp_path / 'checked-export.xlsx'
    register.write_xlsx(spread, [('Spread', ['EUR m', 'FY2024', 'FY2025'],
                                [['Revenue', 100, 120], ['EBITDA', 20, 18]])])
    table = fin_table.build_table(spread, {
        'sheet': 'Spread', 'label_column': 'A', 'header_row': 1, 'unit': 'EUR m',
        'identity': {'entity': {'value': 'Synthetic borrower', 'basis': 'Synthetic fixture', 'reviewed_by': 'test'},
                     'perimeter': {'value': 'Consolidated', 'basis': 'Synthetic fixture', 'reviewed_by': 'test'},
                     'unit': {'value': 'EUR m', 'cell': 'A1'}},
        'expect': {'A1': 'EUR m', 'B1': 'FY2024', 'C1': 'FY2025'},
        'periods': ['FY2024', 'FY2025'], 'rows': [
            {'label': 'Revenue', 'source': 'Revenue'}, {'label': 'EBITDA', 'source': 'EBITDA'},
            {'label': 'EBITDA margin', 'formula': '{EBITDA} / {Revenue}', 'format': 'pct'}]})
    assert table['export']['sha256'] == register.sha256(spread)
    assert table['rows'][1]['source'] == ['Spread!B3', 'Spread!C3']
    draft = ('## summary\nRevised company account.\n\n## financial-analysis\n'
             'Revenue rose while EBITDA fell. [S-001 Spread!B2:C3]\n\n'
             + fin_table.markdown(table) + '\n\n{{keep:1}}\n\n'
             '## market-risk\nMarket description.\n\n## recommendation\nProvisional case.\n')
    content = tmp_path / 'draft.md'
    content.write_text(draft)
    v1, v2 = (tmp_path / f'FP-v0{n}.docx' for n in (1, 2))
    built = fp_docx.build(partial, content, v1, mode='existing', template=template)
    assert built['complete'] and partial.read_bytes() == original
    cells = [cell.text for t in docx.Document(v1).tables for row in t.rows for cell in row.cells]
    assert '15.0%' in cells and 'FY2025 (template)' in cells

    register.save(tmp_path, register.new_register('Synthetic pilot'))

    def apply(op, *changes):
        return register.apply(tmp_path, {'base_revision': register.load(tmp_path)['revision'],
                              'op_id': op, 'actor': 'synthetic test', 'changes': list(changes)})

    apply('draft', {'sheet': 'sources', 'add': {'title': 'Checked export', 'link': spread.name,
        'coverage': 'read', 'impact': 'assessed'}},
        {'sheet': 'analysis', 'add': {'id': 'located-draft', 'text': draft}},
        {'sheet': 'control', 'set': {'word': v1.name, 'word_sha256': built['sha256']}})
    assert 'Spread!B2:C3' in (tmp_path / 'Analysis.md').read_text()
    apply('record-synthetic-decision', {'sheet': 'control', 'set': {
        'status': 'ready', 'ready_by': 'Synthetic officer'}})
    edit_text(v1, 'Provisional case.', 'Officer wording: condition still required.')
    assert 'Status: draft' in register.summary(register.load(tmp_path), v1)
    apply('new-email', {'sheet': 'sources', 'add': {'title': 'Later CFO email', 'type': 'email'}},
        {'sheet': 'open_items', 'add': {'text': 'Deliver the updated forecast', 'raised_by': 'CFO email',
            'addressee': 'client', 'status': 'promised', 'criticality': 'blocker'}})
    assert register.load(tmp_path)['control']['status'] == 'draft'
    content.write_text('## summary\nRevised for the later email.\n\n## recommendation\nApprove.\n')
    result = fp_docx.build(v1, content, v2, template=template)
    assert result['written'] == ['summary'] and 'recommendation' in result['frozen']
    assert 'Officer wording: condition still required.' in fp_docx.to_markdown(v2)
    assert 'Approve.' in v2.with_suffix('.proposals.md').read_text()
    apply('revision', {'sheet': 'control', 'set': {'word': v2.name, 'word_sha256': result['sha256']}})
    assert 'O-001' in register.lists(register.load(tmp_path))
    assert 'S-002' in '; '.join(register.open_checks(register.load(tmp_path), v2))
    assert json.loads(v2.with_suffix('.sections.json').read_text())['sections']['recommendation']['owner'] == 'other'
