"""Synthetic Word fixtures for the development tests."""
import zipfile

from fp_docx import W


def make_template(path, comment_on=None):
    """A small but realistic FP template: cover table, headings, guidance, a fixed table."""
    w = f'xmlns:w="{W}"'
    style = lambda sid, name, lvl=None: (  # noqa: E731
        f'<w:style w:type="paragraph" w:styleId="{sid}"><w:name w:val="{name}"/>'
        + (f'<w:pPr><w:outlineLvl w:val="{lvl}"/></w:pPr>' if lvl is not None else "") + "</w:style>")
    styles = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles {w}>'
              + style("Normal", "Normal") + style("Heading1", "heading 1", 0) + style("Heading2", "heading 2", 1)
              + style("ListBullet", "List Bullet")
              + '<w:style w:type="table" w:styleId="TableGrid"><w:name w:val="Table Grid"/></w:style></w:styles>')
    p = lambda text, sid="Normal": (  # noqa: E731
        f'<w:p><w:pPr><w:pStyle w:val="{sid}"/></w:pPr><w:r><w:t xml:space="preserve">{text}</w:t></w:r></w:p>')
    cell = lambda text: f"<w:tc><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:tc>"  # noqa: E731
    cover = ("<w:tbl><w:tblPr><w:tblW w:w=\"0\" w:type=\"auto\"/></w:tblPr><w:tblGrid><w:gridCol w:w=\"3000\"/>"
             "<w:gridCol w:w=\"6000\"/></w:tblGrid>"
             f"<w:tr>{cell('Borrower:')}{cell('[name]')}</w:tr><w:tr>{cell('Amount:')}{cell('[amount]')}</w:tr></w:tbl>")
    fin = ("<w:tbl><w:tblPr><w:tblW w:w=\"0\" w:type=\"auto\"/></w:tblPr><w:tblGrid><w:gridCol w:w=\"4500\"/>"
           f"<w:gridCol w:w=\"4500\"/></w:tblGrid><w:tr>{cell('EUR m')}{cell('FY2025 (template)')}</w:tr></w:tbl>")
    risk_guidance = p("[Describe market risks]")
    if comment_on == "market-risk":
        risk_guidance = ('<w:p><w:commentRangeStart w:id="1"/><w:r><w:t>[Describe market risks]</w:t></w:r>'
                         '<w:commentRangeEnd w:id="1"/><w:r><w:commentReference w:id="1"/></w:r></w:p>')
    body = (cover + p("1. Summary", "Heading1") + p("[Summarise the proposal]")
            + p("2. Financial analysis", "Heading1") + p("[Explain the figures]") + fin
            + p("2.1 Market risk", "Heading2") + risk_guidance
            + p("3. Recommendation", "Heading1") + p("[State the recommendation]")
            + '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/></w:sectPr>')
    document = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document {w}>'
                f"<w:body>{body}</w:body></w:document>")
    rels = ('<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/'
            'package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/'
            'officeDocument/2006/relationships/styles" Target="styles.xml"/>'
            + ('<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
               'relationships/comments" Target="comments.xml"/>' if comment_on else "") + "</Relationships>")
    types = ('<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/'
             '2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.'
             'relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'
             '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.'
             'wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/'
             'vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
             + ('<Override PartName="/word/comments.xml" ContentType="application/vnd.openxmlformats-officedocument.'
                'wordprocessingml.comments+xml"/>' if comment_on else "") + "</Types>")
    root_rels = ('<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/'
                 'package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/'
                 'officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", types)
        z.writestr("_rels/.rels", root_rels)
        z.writestr("word/document.xml", document)
        z.writestr("word/styles.xml", styles)
        z.writestr("word/_rels/document.xml.rels", rels)
        if comment_on:
            z.writestr("word/comments.xml", f'<?xml version="1.0" encoding="UTF-8"?><w:comments {w}>'
                       '<w:comment w:id="1" w:author="Officer" w:date="2026-10-01T09:00:00Z"><w:p><w:r>'
                       "<w:t>Check the FX exposure</w:t></w:r></w:p></w:comment></w:comments>")


def edit_text(path, old, new):
    """Simulate an officer editing text in Word (test helper)."""
    with zipfile.ZipFile(path) as z:
        parts = {i.filename: z.read(i.filename) for i in z.infolist()}
    if old.encode() not in parts["word/document.xml"]:
        raise ValueError(f"not in word/document.xml: {old}")
    parts["word/document.xml"] = parts["word/document.xml"].replace(old.encode(), new.encode(), 1)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in parts.items():
            z.writestr(name, data)
