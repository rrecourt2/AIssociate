# Drafting the scan, the CIP and the FP

**The institution's own template and style come first.** Ask the analyst for them. Use the outline below only where the institution has none.

## Before you draft

1. Run `status`, `show <deal> claims` and `check`. Repair what `check` reports until it says "No problems found."
2. For each claim the document leans on, read its open tests with `show <deal> <indicator>`, and answer those the record already decides.
3. Read the contents page and the page of the opportunity, then the pages the document covers.
4. Look up the facts you will lean on: `show <deal> facts <ID>`.

## What each document is

- **A scan** says what the opportunity is and whether it fits. It may rest on what the client said. Say so.
- **A CIP**, the concept note, describes the opportunity and lists what still needs testing: the claims that `show claims` gives as not tested, the "Assumptions and open points" of the pages, and the checks that are open or thin.
- **An FP**, the financial proposal, concludes. It holds what is material for the decision, and leaves the wider context to the wiki. Lead each part with the conclusion, then the two or three facts it rests on. Go through the pillars in the order of `show claims`. For each claim that matters: what tested it, how strong the evidence is, and for a challenged claim what mitigates it or which action is agreed. Say where a claim stands in the tool's words: "Currency risk is challenged: the loan is in euros and all sales are in shillings [F-007, F-010]. No hedge is in place [D-002]."

## A default outline

For an FP:

1. **Summary.** What is asked, by whom and for what. The recommendation, or the preliminary view. The three to five points the decision turns on.
2. **The opportunity and its structure.** The loan and its terms. Who borrows, where the cash is earned and how it reaches the lender. Owners, guarantor, security.
3. **The business**, and what is particular about it.
4. **What the loan pays for**, where that is a project or an asset.
5. **Financial position.** Three years and the latest period. Existing debt lender by lender. Where the borrower is not the whole perimeter (see [recording](recording.md)): the borrower on its own, with the debt it owes itself and the cash it receives from the companies it owns.
6. **Risks, pillar by pillar.** Only the claims that matter.
7. **Terms, conditions and agreed actions.**
8. **What is missing.**

A scan takes 1 to 3 in a page or two, the fatal flaws (exclusion list, sanctions, country) and what to do next. A CIP takes 1 to 5 in short, then the claims to test.

## When no terms exist

If the amount, the currency, the tenor, the security or the borrower is not yet known, the document cannot ask for a decision.

- Write a **preliminary view**, and say on the first page which terms are missing. Make no recommendation.
- **A preliminary view still concludes.** Say what is decided already, what the decision turns on and what would change it. A test that speaks of "after this loan" can go against the claim on today's debt alone.
- End with **the list of what is missing**, in the order in which it should be obtained.

## Rules

- **Take every number from a fact**, and cite it: `[F-008]`. Do not retype a number from what you remember.
- **A figure you work out**, such as a ratio or a change, is recorded as a fact marked `inference` and cited: see [recording](recording.md).
- **Say who said what.** "The CFO said" is not "the accounts show". State what is not known.
- **Do not quote the tool's counts** of claims or checks: they change with the next answer. Name the claims that matter and say where each stands. What an FP calls material and what the page of checks lists under "What matters most" are the same list. Before you finish, read the two side by side: every point the FP calls material has a marked check, and every marked check appears in the FP.
- **Tell the analyst what the saved draft says.** Quote its lines. Do not write them again from what you remember.
- **Save the draft as Markdown in `Internal/outputs`**, named for the document, the borrower and the version: `FP Cedar Foods v2 draft.md`. Put the title, the date and the version in top lines between two `---`, as on a page. `check` reads the draft as it reads the pages: the rules under "Citing" and "Writing" in [pages](pages.md) hold for a draft. The browser view shows it under "Drafts": link to a page from it as `../wiki/parties/cedar-foods-ltd.md`. Make the Word file with your own tools once `check` is clean. Take the citations out only if the analyst asks.
- **Before a draft goes out, run `show <deal> sample`.** It prints ten facts that are not inferences, spread over the record, each whole with its quote. Compare each with the page of the source it names, and correct what differs: the fact first, then the pages and the draft. The ten change with every revision. Compare in the same way each fact that `status` lists under "Quotations to compare with the page".
- **Move a draft that was sent**, or that a newer version replaced, to a sub-folder such as `Internal/outputs/sent`. `check` reads only the drafts directly in `Internal/outputs`.
