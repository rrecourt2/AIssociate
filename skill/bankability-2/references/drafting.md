# Drafting the scan, the CIP and the FP

The tool gives you the material: the claims, the facts and the pages. You write the document.

**The institution's own template and style come first.** Ask the officer for them if you do not have them. Follow their headings, their order and their wording. Use the outline below only where the institution has none.

## Before you draft

1. Run `status`, `show <deal> claims` and `check`. Repair what `check` reports until it says "No problems found."
2. For each claim the document leans on, read its open tests with `show <deal> <indicator>`, and answer those that the record already decides.
3. Read the contents page and the page of the deal, then the pages the document covers.
4. Look up the facts you will lean on with `show <deal> facts <ID>` for each main subject.

## What each document is

- **A scan** says what the deal is and whether it fits. It may rest on what the client said. Say so.
- **A CIP** describes the deal and lists the claims that still need testing. Take them from `show claims` (the claims that are not tested, or that rest on someone's own word), from "Assumptions and open points" on the pages, and from the checks that are open or thin.
- **An FP** is driven by conclusions on risk. Go through the pillars. For each claim that matters: what the lender relies on, what tested it, what the evidence is and how strong, and for a claim that is challenged what mitigates it or which action is agreed. A claim that is challenged, contested or thinly supported is said to be so, in the words the tool uses: "Currency risk is challenged: the loan is in euros and all sales are in shillings [F-007, F-010]. No hedge is in place [D-002]."

## The nine pillars

`show claims` lists the claims under these headings, in this order.

| | Pillar | What it covers |
|---|---|---|
| 0 | The deal | The request, the two ways out, who is in the deal, the kind of business |
| 1 | Environment | The country, the sector and its market, licences and regulation. Not the natural environment: that is pillar 6. |
| 2 | Business | Customers, inputs and suppliers, operations and assets, the project |
| 3 | People and governance | Owners and control, integrity, board and controls, management |
| 4 | Cash flow and debt | The accounts, profitability, cash flow against debt service, existing debt |
| 5 | Liquidity and financial risks | Liquidity and working capital, currency, interest rate and price risk |
| 6 | Environmental, social and impact | E&S risk and its management, land and supply chain, impact |
| 7 | Links | Guarantee, owner and group, key customer, key supplier, builder and operator, other lenders |
| 8 | The facility | Terms, covenants, security, legal standing, conditions |

## A default outline

For an FP, where the institution has no template:

1. **Summary.** What is asked, by whom and for what. The recommendation, or the preliminary view. The three to five points the decision turns on.
2. **The deal and its structure.** The loan and its terms. Who borrows, where the cash is earned and how it reaches the lender. Owners, guarantor, security.
3. **The business.** What it does, how it earns its money and what is particular about it, from the wiki.
4. **What the loan pays for.** The project or the asset: what, where, cost, timetable, who pays, status. Leave this out where the money goes into the business as a whole.
5. **Financial position.** The figures of the last three years and the latest period, each with its fact. Existing debt lender by lender, with security and ranking. Where the borrower is not the whole perimeter: the borrower on its own, with the debt it owes itself and the cash it receives from the companies it owns.
6. **Risks, pillar by pillar.** Only the claims that matter, as described above.
7. **Terms, conditions and agreed actions.** The gaps with an agreed action, each with its owner and date.
8. **What is missing.** Questions without an answer, documents not received, claims not tested.

A scan takes 1 to 3 in a page or two, the fatal flaws (exclusion list, sanctions, country) and what to do next. A CIP takes 1 to 5 in short, then the claims to test and the plan for due diligence.

## When no terms exist

If the amount, the currency, the tenor, the security or the borrower is not yet known, the document cannot ask for a decision.

- Write a **preliminary view** and say on the first page which terms are missing.
- Make **no recommendation**.
- End with **the list of what is missing**, in the order in which it should be obtained.
- Say what is decided already. A test that speaks of "after this loan" can go against the claim on today's debt alone.

## Rules

- **Condense.** The wiki holds the wider analysis. The document holds what the reader needs to decide.
- **Take every number from a fact**, with its unit, its date and the company it belongs to, and cite the fact: `[F-008]`. Do not retype a number from what you remember.
- **A figure you work out** from facts, such as a ratio, a sum or a change, is allowed when the facts it comes from are cited beside it. `check` knows only the numbers that the cited records hold, so it reports the new figure. For a figure the document leans on, record it as a fact marked `inference`, with the working in its statement, and cite that fact. See [recording](recording.md).
- **Say who said what.** "The CFO said" is not "the accounts show".
- **State what is not known.**
- **Do not quote the tool's counts** of claims or checks. They change with the next answer, and no fact holds them. Name the claims that matter and say where each stands.
- **Save the draft as Markdown in `Internal/outputs`**, named for the document, the borrower and the version: `FP Cedar Foods v2 draft.md`. `check` reads the Markdown files there the same way as the pages: paragraph by paragraph, every number against the records cited beside it. Put the title, the date and the version in top lines between two `---`, as on a page: `check` does not read those. Make the Word file from the draft with your own tools once `check` is clean. Take the citations out of the final version only if the officer asks. Move a draft that was sent, or that a newer version replaced, to a sub-folder such as `Internal/outputs/sent`. It says what was said then, and `check` reads only the drafts directly in `Internal/outputs`.
- **When the officer corrects the draft**, correct the fact and the page as well.
