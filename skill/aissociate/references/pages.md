# Pages

The wiki gives the work its depth: what the business is, how it works, how its parts relate and what is particular about it. It describes and relates. The CIP and the FP conclude, and are condensed from it. Write it so that an assistant who has never seen this deal can pick it up.

## How the wiki is read

- **Every page starts with a lead that can stand alone.** The contents page, `Internal/wiki/index.md`, prints the first sentence of each page, and a reader opens the page only when that line says so.
- **The tool writes the contents page**, folder by folder, and puts what matters most first in each folder. First comes the page of a party or a project with a main role in the deal. Then come the pages that cite the most facts behind a marked check or behind an answer that goes against a claim, then the pages that cite the most of the record. The menu of the browser view has the same order, and it moves as the record and the marks do. The tool also writes `sources.md`, which lists every source, and `checks.md`: see [standard](standard.md). `timeline.md` lists, newest first, what was recorded, when and by whom, from the log of the record.
- **Say each thing once**, on the page it belongs to, and link to it from elsewhere.
- **A draft is not part of the wiki.** The analyst asks for a scan, a CIP or an FP, and you write it from the wiki and the record. It is the analyst's document, saved in `Internal/outputs`: see [drafting](drafting.md). A page may link to it as to any file.
- **A person reads the same pages in a browser**, in `wiki.html`, which `Wiki.html` at the top of the deal folder opens. A click on a citation shows the record with every field. So write a source's `note`, a link's `why` and a decision's `reason` for a reader.

## Which pages

The wiki has eight folders, each with a heading on the contents page.

- `opportunity/`, "Opportunity": one page, `opportunity/opportunity.md`, with `about: DEAL`. It is the way in.
- `assets/`, "Assets and projects": plants, lines, projects, contracts, and the loan where it needs a page of its own.
- `parties/`, "Parties": a company, a group or a person, or several that share a page, such as the lenders.
- `people/`, "People": a group of people, such as the board and management, the owners, our side.
- `context/`, "Context": the history, the market and competitors, the products and how they are made, the country and its rules.
- `topics/`, "Topics": analysis that runs across parties, such as working capital or currency.
- `deal/`, "Deal": the terms once they are on paper, such as the term sheet, the security and the covenants.
- `work/`, "Work": the working notes, and a piece of work such as a site visit.

`pages` creates an empty page for the opportunity, a page under `parties/` for each borrower, repayment source, guarantor and sponsor that has a name, and a page under `assets/` for a financed project. Those you write. To make any other page, write a file in the right folder with the form below, then run `pages`. `check` reports a page outside `work/` that no other page links to.

- **A page for each subject a reader would look up**: a plant, a project, a product, the market, a customer that matters, the family that owns the company. A subject earns a page when two or more sources bear on it, or when other pages keep mentioning it. If a long document changed only the page of the opportunity, it has not been taken in. A wiki ends up with about as many pages as the deal has sources. A page written to raise the count is filler.
- **Not a page:** a check, a claim or a list of checks; a single figure; a document retold; a subject with nothing to say beyond its line on the contents page; an account of what was done.
- **The history has a page of its own**, in `context/`: the founding, each plant and line, each change of owner or of capital, each with its date and its source. Where two sources differ, give both. Dated events belong here: a page under `topics/` analyses, and links here for what happened when.
- **Go beyond the company's own documents** for the market, the competitors, the country and the technology. A page in `context/` says who says so.
- **A project or an asset gets a real page**: what it is, where, how big, at what cost, by when, who pays for which part, how far it has come, and what it adds to the business.
- **A table across several subjects**, such as the plants with their capacity, goes on the page of the company or the group that holds them.
- **One page for several subjects.** Name them all in `about`: `about: P-004, P-005, P-006` for a page on the three banks. On a page under `parties/` or `assets/`, a borrower or a guarantor named second needs no page of its own.
- **To merge, remove or rename a page**, move what is worth keeping, add the subject's ID to the `about` of the page that now describes it, delete the old file, run `pages` and `check`, and repoint the links that `check` reports.

## The form

```markdown
---
title: Cedar Foods Ltd
about: P-001
checked:
---

# Cedar Foods Ltd

## What it is

## At a glance

<!-- tool:begin glance -->
<!-- tool:end -->

## What we know

## Assumptions and open points

## Sources

<!-- tool:begin sources -->
<!-- tool:end -->
```

- **`about`** names what the page is about: a subject (`P-001`), a link (`R-004`), an indicator (`CAS_REVENUE_001`), `DEAL`, or several separated by commas. The first one decides whose page it is. A page under `people/`, `context/`, `topics/`, `deal/` or `work/` is nobody's own page: name there what it bears on, such as the company or `DEAL`.
- **Leave the marked parts to the tool**: "At a glance", "Sources" and "Key values", which it adds at the end with the latest value under each `label` of the facts about the subject. "At a glance" lists the open questions and the decisions about a subject. So keep no such list on a page: cite a question, as `[Q-004]`.
- **`checked`** is for a person. Leave it empty.

## What to write, in this order

1. **What it is.** The lead, in one to three plain sentences: what the thing is and where it sits in the deal. No conclusion.
2. **How it works.** A business: what it buys and from whom, what it does with it, whom it sells to, where it earns its margin, who owns and runs it. A project: the plan. A contract or a loan: who owes what to whom, until when, on which terms.
3. **How it relates to the rest.** Who depends on whom, and for what: the owner who is also the landlord. Link to the other page.
4. **What is particular**, against others of its kind.
5. **How the context shows in the figures.** "The gross margin is thin because more than half of revenue is goods bought and sold on [F-031]."
6. **Assumptions and open points**, only now: each assumption with what it rests on and what would test it, then what is unknown, then what was looked for and not found.

Parts 2 to 5 go under "What we know". On the page of the opportunity, write the request, how the loan is to be repaid, who borrows, where the cash is earned and how it reaches the lender.

## The working notes

`work/working-notes.md`, with `about: DEAL`, says how to work on this deal. It has three parts and stays short, about 800 words as `pages` counts them, which leaves out the top lines, the headings, the citations and the parts the tool writes. Take out what is done, also where a colleague wrote it:

1. The analyst's standing instructions, in their words, with dates. An instruction on how to write goes here only, never into the record.
2. Which page is the place for what.
3. What is left to do.

What was done is in the log, not here. `check` does not ask this page for citations, nor for the source of a figure. A citation it does carry is read like any other: one of a replaced or a disputed record is reported.

```markdown
- 12 November 2026, analyst: "Write more about the second line. The committee will ask what it adds."
- The supply contracts belong on the page of Cedar Foods Ltd, not on a page of their own.
- Left to do: the page of the guarantor, once it is named.
```

## The details that show understanding

Three to five details on a page are plenty. A detail earns its place when all three hold:

1. It would not be true of the next company in the same sector.
2. It changes how a figure or a risk is read.
3. A fact or a source bears it out.

This paragraph describes, says what is particular and ties it to a figure:

> Cedar's margin follows the price of raw milk. It buys all its milk from three cooperatives under contracts that fix the volumes and leave the price open [F-013], so a dry year reaches its costs at once. The CFO put the fall of the gross margin in 2025 down to an 18% rise in milk prices during the drought [F-012]. That is his account, given on one call: no document that shows the margin has been read. Whether Cedar can pass a higher milk price on to Bluegate, which buys 31% of what it sells [F-009], is not known.

Filler is: praise, words about importance, what is true of every business of its kind, a figure put into words with no reason beside it, a list of everything a document holds, and a summary of what was just said.

## Citing

Put the ID of the fact or the source in square brackets after the sentence it supports: `[F-008]`, `[S-003]`, `[F-001, F-006]`. Cite a fact for a figure, a name, a date or a term, and the source itself for description that no fact holds. A decision or a question is cited the same way. Name each ID: of a range such as `F-267 to F-271`, only the two ends are read.

`check` reads a page paragraph by paragraph. A list item and a table row each count as one. It reports:

- **A number that no record cited in the same paragraph holds.** A record holds the numbers in all its fields but its answers, and a fact also those of its source, except the source's map. The scale word of a fact's unit goes with its value: value 4060 with unit KES m holds 4,060m. A figure passes when a cited record holds the same figure, or one that rounds to it at the precision the page writes; either side may carry a scale word (thousand or k, million or m or mn, billion or bn, trillion or tn). The short k and m count only when they are written against the number, as in 4,060m or 50k, so 8 m tall and 3 M&A deals carry none, while the longer words count with or without a space, and so does the unit of a fact such as KES m. So KES 4.1bn passes against KES 4,060m, and 2.5 against 2.49. A figure cut short does not pass: KES 4.0bn against KES 4,060m is reported, and so is 3.2 against 3.26. A half rounds up: 2.55 backs 2.6, and 2.5 is reported. Where the page and the record both give a scale word and the two differ, the figure is reported unless the amounts are equal: KES 4,060bn against KES 4,060m is reported, and so is 50bn against 50 million, while KES 4.06bn against KES 4,060m passes. A figure with no scale word on one side passes on the same digits, because a table may give its unit in its heading: there the scale is yours to read. So do digits that a cited record holds only in a date: EUR 12bn passes beside a fact as of 12 November. Whole numbers below 10 are let through unless a scale word follows them: 8 customers is not checked, EUR 8bn is. Every other number counts, also a year and the day of a date: cite a fact as of the date you name. Where facts hold the number, `check` names up to three of them.
- **In a table**, give a figure its citation in its own row: `| Revenue | KES 4,060m | KES 3,480m | [F-008] [F-019] |`. The head row is not read.
- **Only the record counts.** A number that is in a document and not in the record is reported even where you cite the source. A number in a source's map or note passes beside that source, so `check` cannot tell you a fact is missing: take every figure from a fact, and record the fact first.
- **A citation that leads nowhere**, a link to a page that is not there, and a page with more than 40 words of text and no citation at all.
- **A citation of a record that was replaced or is disputed**, unless it is marked as below.

## When something changes

- **Merge new information into the page.** Do not append a dated entry. Change the sentence, the figure and the citation. The tool keeps no earlier text of a page or a draft: where the deal folder is in OneDrive or SharePoint, their version history has it.
- **Find every page that carries the old figure.** `show <ID>` lists the pages that cite a record.
- **Take in what is new.** `show <deal> uncited` lists, by source, the current facts that no page cites yet; a citation in a draft, or in a part the tool writes, does not count.
- **Keep a replaced claim only where it matters** that it was once held. Write it as one sentence that starts with `Outdated:` for a replaced fact, `Disputed:` for a disputed one or `Replaced:` for a replaced source, and cite the record after that word:

  ```markdown
  Revenue was KES 4,060m in 2025 [F-008]. Outdated: the teaser gave about KES 4.1bn [F-005].
  ```

  The word covers every citation of its kind after it in that paragraph, list item or table row: `Outdated:` and `Replaced:` what was replaced, `Disputed:` what is disputed. So put the marked sentence last.
- **A balance at an earlier date is not outdated.** Cite it without a marker.
- **Write nothing when a source adds nothing.**

## Writing

1. State a relationship exactly: who, what, since when, how much. Never "associated with" or "linked to".
2. Write no sentence about significance. Say what the fact changes for repayment, or leave it out.
3. Name who said it and where. One source is one source.
4. Write no summary at the end of a section or a page.
5. Use "is" and "has".
6. Give every number its unit, its date and the company it belongs to.
7. Mark what you inferred.
8. Write "not stated" or "not known" only for what you looked for in the original and did not find. Record that search as a fact with `nothing_found`, and cite it. What nobody has looked for yet is open: say that it is asked, and cite the question.
9. Link the first mention of another subject to its page: `[Cedar Foods Ltd](../parties/cedar-foods-ltd.md)`. Name a file in lower case with hyphens.
10. On a page about people: no judgements of character.
