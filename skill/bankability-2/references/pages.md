# Pages

The standard and the record give the work its rigour. The wiki gives it depth: what the business is, how it works, how its parts relate, what is particular about it, and how its context shows in its figures. It is a wiki, not the financial proposal. It describes and relates, objectively and in context. The CIP and the FP conclude, and are condensed from it later.

Write it so that you, or another assistant who has never seen this deal, can pick the deal up from it.

## How the wiki is read

An assistant reads the contents page, `Internal/wiki/index.md`, and the page of the deal first. It opens another page only when the task needs it. So:

- **Every page starts with a lead that can stand alone.** The contents page prints the first sentence of each page. That line decides whether the page is opened.
- **The contents page is the map.** The tool writes it on every `pages`, shelf by shelf, with the pages of a shelf in the order of their file names. So name the files so that what belongs together sorts together: `lender-…`, `customer-…`. It also lists each subject that no page describes, in one line: its kind, its roles and its note. Beside it the tool writes `sources.md`: every source of the record, how far it was read, how many facts rest on it, and links to its original and its extract.
- **A page is about one subject.** It may be long when the subject needs it. Keep it workable: headings or bold lead-ins that name what follows, and each thing said once, on the page it belongs to. Link to it from elsewhere. A figure that sits on five pages has to be changed on five pages.

A person reads the same pages in a browser: `pages` writes `Internal/wiki/wiki.html`, one file that opens by double click. It lists the pages by shelf, searches them, follows the links between them, and shows the fact behind a citation when it is clicked: its value, its date, its source and the place in the source, with a link that opens the original at that page. The reader sees every field of the record there, also a source's note and a decision's reason, so write those as text for a reader. A record that was replaced or has ended is in the view only where a page cites it. A long part that the tool fills in is folded away under "From the record", so that your text comes first. The view also shows the sources and the index of the client's documents. Do not edit it: the tool writes it again each time. The pages themselves are plain Markdown with ordinary links, so the folder also opens in any Markdown reader, or as a vault in Obsidian.

## Which pages

The wiki holds the larger context of the deal: what a reader would want to know about this company, also where no check asks for it. The financial proposal condenses. The wiki does not have to.

| Folder | One page per |
|---|---|
| `deal` | the deal, and each plant, line, project, facility or contract that has a name |
| `parties` | company, group or person that needs one, or several that share a page, such as the lenders |
| `people` | group of people: the board and management, the owners, our side, other lenders and advisers |
| `context` | what surrounds the company: its history, its market and competitors, its products and how they are made, the country and the rules it works under |
| `topics` | subject of analysis that runs across parties, such as cash and working capital, or currency |
| `terms` | term under negotiation |
| `work` | piece of work, such as a consultant to hire or a site visit, and the working notes |

**A page for each subject a reader would look up.** One subject to a page: a plant, a machine, a project, a product, the history, the market, a customer that matters, the family that owns the company. A subject earns a page when two or more sources bear on it, or when other pages keep mentioning it. Write the page once and link to it from the others.

**How many.** There is no right number, and a page written to raise the count is filler. As a rough guide, a wiki of this kind ends up with about as many pages as the deal has sources, or somewhat more. Far fewer usually means that subjects share a page. If a long document changed only the page of the deal, it has not been taken in.

**Not a page:** a check, a claim or a list of checks; a single figure; a document retold from front to back; a subject with nothing to say beyond its line on the contents page; an account of what was done.

**The history has a page of its own**, in `context`. How the company came to be what it is: its founding, each plant and line, each change of owner or of capital, each listing, with the date and the source of each. Where two sources differ, give both. Other pages link to it and do not repeat it.

**Go beyond the company's own documents where you can.** The market, the competitors, the country and the technology are described by others: an industry association, a rating agency, a manufacturer of the machines. A page in `context` says who says so.

`pages` creates an empty page for the deal, for each borrower, repayment source, guarantor and sponsor, and for each project the loan finances, once it has a name. Those you write. To make any other page, write a file in the right folder with the form below, then run `pages`. `check` reports a page that no other page links to.

**One page for several subjects.** Name them all in `about`: `about: P-004, P-005, P-006` for a page on the three banks. Each then counts as described there. Its name links to that page from the other pages, and it leaves the list of subjects without a page. Name subjects only: a page that names a link or an indicator gets one line from the tool and no key values.

**To merge or remove a page**, move what is worth keeping to the page that now describes the subject, add the subject's ID to that page's `about`, delete the old file, and run `pages` and `check`. `check` reports each link that still points at the page that is gone. `pages` writes a new empty page only for the deal, a main party or a financed project that no page names in `about`. To rename a page, write the new file, delete the old one and repoint the links that `check` reports.

**Projects and assets get real pages.** What it is, where, how big, at what cost, by when, who pays for which part, how far it has come, and what it adds to the business: capacity, products, revenue, debt. The answer to `OBS_FEAS_008` is its start.

## The form

```markdown
---
title: Cedar Foods Ltd
about: P-001
checked:
---

# Cedar Foods Ltd

## What it is

One to three plain sentences. The first one can stand alone.

## At a glance

<!-- tool:begin glance -->
<!-- tool:end -->

## What we know

## Assumptions and open points

## Sources

<!-- tool:begin sources -->
<!-- tool:end -->
```

- **`about`** names what the page is about: a subject (`P-001`), a link (`R-004`), an indicator (`CAS_REVENUE_001`), `DEAL`, or several separated by commas. The first one decides whose page it is. A page in `people`, `context`, `topics`, `terms` or `work` is nobody's own page: name there what it bears on, such as the company, the group or `DEAL`. The name of a company keeps linking to the company's own page. `show <deal> claims` gives the ID of each indicator.
- **Leave the three marked parts to the tool.** "At a glance" on the page of the deal shows the stage, the loan with the parties and the project at its centre, the claims by pillar and each claim that is challenged or contested. On the page of a subject it shows the roles, the links that have not ended, and the challenged claims, questions and decisions. On the shelves `people`, `context`, `topics`, `terms` and `work` it is one line that names what the page is about. "Sources" lists what the page cites, with a link to each document, and says where a source was not read in full. "Key values" is a table of the latest value under each label of the facts about the deal or the subject. The tool adds it at the end of the page once there is such a fact.
- **You may move a marked part**, with its heading, below "Assumptions and open points". The tool fills it where it finds it. There is rarely a need: in the browser a long part is folded away wherever it stands.
- **"At a glance" already lists the open questions and the decisions about a subject.** Cite a question on a page: `[Q-004]`. Do not keep a list of questions there.
- **`checked`** is for a person. Leave it empty.

## What to write, in this order

1. **What it is.** The lead: what the thing is and where it sits in the deal. No conclusion.
2. **How it works.** For a business: what it buys and from whom, what it does with it, whom it sells to, and on which step it earns its margin. Who owns it and who runs it. For a project: the plan. For a contract or a loan: who owes what to whom, until when, on which terms. The answer to `OBS_BUSINESS_MODEL_001` is the start for a business.
3. **How it relates to the rest.** Who depends on whom, and for what: the cash that is earned in one company and owed by another, the owner who is also the landlord, the customer who also supplies. State each tie exactly and link to the other page.
4. **What is particular.** The few things that set this business, project or party apart from others of its kind. See below.
5. **How the context shows in the figures.** Tie each to a figure: "The gross margin is thin because more than half of revenue is goods bought and sold on, which earn far less than what the plant makes [F-031]." A figure without its reason is a table. A reason without a figure is an opinion.
6. **Assumptions and open points**, under their own heading and only now. Each assumption with what it rests on and what would test it. Then what is unknown. Then what was looked for and not found.

Parts 2 to 5 go under "What we know". Use `###` headings or short bold lead-ins.

On the page of the deal, write the request, how the loan is to be repaid, and the structure in words: who borrows, where the cash is earned and how it reaches the lender. Link to the pages of the parties and the project.

**The working notes** have their own page, `work/working-notes.md`, with `about: DEAL`. They say how to work on this deal: what the officer asked for, in their words and with the date, which page is the place for what, and what is left to do. They hold no analysis and no account of what was done: `show <deal> log` has that. `check` does not ask this one page for citations. It still reports a citation of a replaced fact there.

```markdown
- 12 November 2026, officer: "Write more about the second line. The committee will ask what it adds."
- The supply contracts belong on the page of Cedar Foods Ltd, not on a page of their own.
- Left to do: the page of the guarantor, once it is named.
```

## The details that show understanding

A few well-chosen details show that the business is understood. Three to five on a page are plenty. A detail earns its place when all three hold:

1. **It would not be true of the next company in the same sector.** If the sentence fits any dairy, any bank or any solar plant, cut it.
2. **It changes how a figure or a risk is read.**
3. **A fact or a source bears it out.**

Where to look for them:

- A term of a contract that moves a figure: volumes fixed and the price left open.
- A step where the margin is made or lost: a trading arm that doubles revenue and adds little profit.
- A tie that is unusual: the plant belongs to the subsidiary and the loan is asked by the parent.
- A place, a season or a rule that applies to this business: milk that arrives in the rains, a tax holiday that ends in the third year of the loan.
- A mismatch: sales in shillings and a loan in euros.
- A year that is not like the others, and why.
- Two documents that give the same thing differently.

This paragraph describes, says what is particular and ties it to a figure:

> Cedar's margin follows the price of raw milk. It buys all its milk from three cooperatives under contracts that fix the volumes and leave the price open [F-013], so a dry year reaches its costs at once. The CFO put the fall of the gross margin in 2025 down to an 18% rise in milk prices during the drought [F-012]. That is his account, given on one call: no document that shows the margin has been read. Whether Cedar can pass a higher milk price on to Bluegate, which buys 31% of what it sells [F-009], is not known.

This one is filler. Every sentence fits a hundred companies and none can be checked:

> Cedar Foods is a leading dairy processor with a strong market position and a diversified customer base. It has shown robust growth, which underlines its resilience. However, it faces challenges from volatile input prices and currency risk, which may weigh on profitability going forward.

Filler is: praise, words about importance, what is true of every business of its kind, a figure put into words with no reason beside it, history retold away from its own page, a list of everything a document holds, and a summary of what was just said.

## Citing

Put the ID of the fact or the source in square brackets after the sentence it supports: `[F-008]`, `[S-003]`, `[F-001, F-006]`. Cite a fact for a figure, a name, a date or a term. Cite the source itself for description that no fact holds. A decision or a question can be cited the same way.

`check` reads the pages paragraph by paragraph. A paragraph, a list item and a table row each count as one. It reports:

- **A number that no record cited in the same paragraph holds.** Whole numbers below 10 are let through. Every other number counts: an amount, a percentage, a year, the day of a date, the number of a note. It is held when a cited record carries it: a fact in its statement, its value, its date or its place, a source in its title or its date. So cite a fact as of the date you name, write a period the way the fact does, and write a figure the way its fact gives it: KES 4,060m, not KES 4.06bn.
- **In a table, each row is read on its own.** Give a figure its citation in its own row: `| Revenue | KES 4,060m | KES 3,480m | [F-008] [F-019] |`. The head row is not read, so a year or a unit there needs no citation.
- **Only the record counts.** A number that is in a document and in no fact is reported even where you cite the source. Record the fact first, then cite it. A figure you worked out is a fact too: see [recording](recording.md).
- **A citation that leads nowhere**, a link to a page that is not there, and a page with text and no citation at all.
- **A citation of a fact that was replaced or is disputed**, unless it is marked as below.

## When something changes

- **Merge new information into the page.** Do not append a dated entry. Change the sentence, the figure and the citation.
- **Find every page that carries the old figure.** `show <ID>` lists the pages that cite a record, and `check` lists each page that still cites a replaced fact.
- **Keep a replaced claim visible only where it matters** that it was once held: a figure the client first gave, a date two documents give differently. Write it as one sentence that starts with `Outdated:` or `Disputed:`, and cite the old fact after that word:

  ```markdown
  Revenue was KES 4,060m in 2025 [F-008]. Outdated: the teaser gave about KES 4.1bn [F-005].
  ```

  `check` leaves alone every citation after the word, up to the end of that paragraph, list item or table row. So put the marked sentence last, or give it a list item of its own. The word also works as the first word of a table row, after a lead-in in bold, and inside a bracket. Each word covers its own kind: `Outdated:` a fact that was replaced, `Replaced:` a source that was replaced, `Disputed:` a fact that is disputed. Without the right word, `check` reports the citation.
- **A balance at an earlier date is not outdated.** Both facts are current and both may be cited without a marker.
- **Write nothing when a source adds nothing.**

## Writing

1. State a relationship exactly: who, what, since when, how much. Never "associated with" or "linked to".
2. Write no sentence about significance. Say what the fact changes for repayment, or leave it out.
3. Name who said it and where. One source is one source.
4. Write no summary at the end of a section or a page.
5. Use "is" and "has".
6. Give every number its unit, its date and the company it belongs to.
7. Mark what you inferred.
8. Write "not stated" or "not known" only for what you looked for in the original and did not find. Record that search as a fact with `nothing_found`, and cite it.
9. Link the first mention of another subject to its page, with an ordinary relative link: `[Cedar Foods Ltd](../parties/cedar-foods-ltd.md)`. Name a file you create in lower case with hyphens, as the tool does.

On the people pages, record what people said, asked for and decided, with the source. No judgements of character. Name the party they belong to in `about`.
