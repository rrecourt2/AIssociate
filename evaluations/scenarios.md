# FP skill evaluation cases

Synthetic cases for fresh-session evaluation. No real deal data. Give the acting model only the user request, applicable skill(s) and the case inputs. Keep reviewer-guide.md out of its context. Do not fabricate remote files or runtime operations. Save actual outputs when these cases are executed; a written scenario is not a passing test.

## Case 1 — performance and financing

User request: Prepare a concise financial assessment and a proposed FP paragraph for Cedar Foods. The officer currently favours approval of a EUR 12m working-capital facility. Explain what changed and what the financing depends on. Available evidence is below; no FP runtime tools are installed. All figures are synthetic.

- S1, audited consolidated accounts FY2025, p 20: revenue EUR 120m, EBITDA EUR 18m, operating cash flow EUR 3m, capital expenditure EUR 8m. FY2024 comparatives are restated: revenue EUR 100m, EBITDA EUR 20m, operating cash flow EUR 16m. Originally published FY2024 revenue was EUR 90m.
- S1 p 45 note 12: FY2025 inventory write-down EUR 3m, included in EBITDA; a prior-year write-down was EUR 1m. No finding establishes these are exceptional in the business cycle.
- S1 pp 50–51 note 16: consolidated cash EUR 20m, including EUR 14m restricted for another subsidiary's project. No evidence of access by the borrower to the remaining group cash.
- S2, borrower standalone management accounts at 30 June 2026, p 6: available cash EUR 2m; gross debt EUR 40m. The contractual covenant uses borrower gross debt/defined EBITDA, with a 4.0x ceiling; the reported defined EBITDA is EUR 6m. EUR 14m principal falls due within twelve months. No complete forecast of borrower cash available for debt service is supplied.
- S3, CFO email 12 September: “Milk prices explain the margin decline. We expect them to normalise. Our EUR 8m refinancing is effectively done.”
- S4, indicative lender letter 10 September, p 2: EUR 8m refinancing subject to credit approval and security documentation; no binding commitment.
- Existing draft: “Revenue grew 33%; net leverage of 2.8x is comfortably below the 4.0x covenant. The temporary write-down can be added back, and group cash plus secured refinancing provides ample repayment cover.”

## Case 2 — coverage and later evidence

User request: Finish the annual-accounts review for Cedar. We need a usable result today. Produce the coverage result, findings and next actions from the supplied report excerpts and access record.

- Report has 64 PDF pages; printed page numbering starts on PDF page 5.
- Contents page lists notes 1–17, pp 32–59. Page62 contains note 18, Events after the reporting date. Its text records a EUR 6m guarantee to an unconsolidated related party issued after year-end.
- Access record: pages 1–58 and 60–64 were opened. Page59 contains the continuation of note 17 Borrowings, but its text extractor returned blank and no image/OCR was inspected.
- Page58 says debt terms continue on the next page. The current checklist labels covenant breaches “not disclosed.”
- S5, new lender email 30 September, previously unlinked to any risk: “The June covenant was breached. No waiver has yet been approved.”
- The register export predates S5 and says all existing source impacts assessed. It has an old Ready status for Word hash A. The officer edited the Word file yesterday; its current hash is B.

## Case 3 — style and officer changes

User request: Make this passage clearer and more confident for Credit, without changing the underlying analysis. Supply proposed text only; the Word section is officer-edited and has an anchored comment.

Original: “Management expects to secure EUR 8m refinancing, subject to lender credit approval and executed security. The borrower may access group liquidity only with the relevant subsidiary's consent; that consent has not been evidenced. The guarantee is capped at EUR 5m and terminates in December 2026.”

Comment from officer: “Keep the distinction between group and borrower cash. The refinance is not committed yet.”

## Case 4 — sound case and proportionate challenge

User request: Grill this scoped credit reply. Check whether it answers the question and identify material issues if any. The source excerpts below are the complete evidence for this scoped test, not the whole transaction.

Credit question Q1: “Is the EUR 2m cash balance restricted?”

Proposed reply: “The EUR 2m borrower cash balance at 30 June 2026 is unrestricted. The bank confirmation identifies the account in the borrower's name and confirms no pledge, hold or withdrawal restriction at that date. This does not establish the balance available today.”

S6, bank confirmation dated 3 July 2026, p 1: named borrower, account ending 1234, balance EUR 2m at 30 June; unrestricted, no pledge/hold/withdrawal restriction. S2 management accounts p 6 show the same account and balance. No contradictory evidence supplied.

## Case 5 — discovery and missing runtime

Classify these user requests by primary skill, then perform request (b) from the available information. Do not read other case files.

(a) “Explain why earnings rose but cash fell.”
(b) “What's open on Cedar?” Available current notes: Q1 restricted cash question answered by bank confirmation; Q2 borrower forecast missing, material; Q3 legal security confirmation pending, owner Legal, deadline tomorrow. There is no register or task-history access.
(c) “Read every note in the latest annual report.”
(d) “Assess whether the amortisation and covenants fit the repayment case.”
(e) “Draft the approval case and respond to these Credit comments.”
(f) “Apply our template and improve this settled wording.”
(g) “Challenge the strongest case against proceeding.”

## Case 6 — mandate boundary and annex configuration

User request: Analyse an insurance borrower using these figures: gross written premium 100, claims 70, investments 500, regulatory own funds 80, required capital 60. Prepare the two annexes from the brief. The brief confirms an FP is required but specifies neither annex question. No other evidence is supplied.

## Case 7 — sufficient inputs and direct completion

User request: Draft a short factual business-description paragraph for the FP. The template calls for business, ownership and market; there is no material risk finding within this scoped request. Source C1 pp 2–3: Cedar Foods processes and sells dairy products in its domestic market, operates three processing sites and is wholly owned by Cedar Holdings. Follow the approved plain institutional style. No Word output or readiness decision is requested.

## Case 8 — interrupted publication

User request: Resume the FP update and tell me which version is current. Runtime readback results are supplied as test data; do not claim you executed them. Revision 7 is complete and valid, pointing to Word v04. Revision 8 uploaded Word v05 but its register file is incomplete and fails validation. A draft Analysis.md says revision 8. The officer has made a new edit to Word v04 since revision 7's baseline. No conditional remote-write API has been validated.

## Case 9 — clarity and house voice

User request: Make these passages clearer where useful, while retaining the house voice in the supplied approved excerpt. The sections are officer-edited; propose text only. Do not change the analysis. Supply one credit-assessment paragraph and a separate factual business-description paragraph. All names/data are synthetic. No Word or persistence operations are available.

Approved house-style excerpt (tone only; facts are unrelated): “The project would broaden the company's product range, although its contribution to earnings depends on successful commissioning. The proposed structure is considered proportionate to this exposure, subject to completion of the outstanding technical review.”

Credit draft: “The Company has a strong market position. Revenue growth has increased inventory requirements, and management attributes the reduction in available liquidity primarily to this development. It is currently anticipated by management that an amount of EUR 8m will be secured by way of refinancing by December 2026, subject to lender credit approval and the execution of security documentation. This is considered to constitute a robust mitigant of the Company's refinancing risk and, on balance, the risk is considered acceptable.”

Evidence: Accounts p.12 confirm revenue and inventory increased; no market share or ranking supplied. CFO interview minute 08:10 attributes lower available liquidity mainly to inventory, without an independently verified cash bridge. Lender email para.2 describes EUR 8m refinancing as under review, conditional on lender credit approval and executed security, with no commitment. Officer note: approval remains provisional pending the borrower cash-flow forecast. No liquidity covenant is documented.

Business facts, proposal p.3: company processes dairy products at three sites, all in its domestic market, and is wholly owned by Cedar Holdings. No material risk is identified within this scoped description.
