# Pages

The wiki is your working draft of the deal: the wider analysis that the CIP and the FP are later condensed from. It describes. The CIP and the FP conclude. Write it so that you, or another assistant, can pick the deal up again from it.

## Shelves

| Folder | One page per |
|---|---|
| `deal` | the deal, and each facility, contract, asset and project |
| `parties` | company or group |
| `people` | group of people: the client's side, our side, other lenders and advisers |
| `topics` | subject of analysis, such as revenue and customers, or currency risk |
| `terms` | term under negotiation |
| `work` | piece of work, such as a consultant to hire or a site visit |

`pages` creates the page for the deal and for each subject. You create the others when there is something to say: write a file in the right folder with the form below, then run `pages`.

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

- **`about`** names what the page is about: a subject (`P-001`), an indicator (`CAS_REVENUE_001`), `DEAL`, or several separated by commas. The tool fills "At a glance" from it: roles, links, key values, checks and what they rest on, open questions and decisions.
- **Leave the two marked parts to the tool.** Everything else is yours.
- **`checked`** is for a person. Leave it empty.

## The four parts

1. **What it is.** What the thing is and how it relates to the deal. No conclusion.
2. **At a glance.** The tool's.
3. **What we know.** Description, context and facts. Order it as the subject needs. Use short bold lead-ins rather than more headings.
4. **Assumptions and open points.** Each assumption with what it rests on and what would test it. Then what is unknown. Then what was looked for and not found.

## Citing

Put the ID of the fact or the source in square brackets after the sentence it supports: `[F-008]`, `[S-003]`. The tool lists the sources at the foot of the page. `check` reports a page whose numbers are in no fact or source it cites, and a page that cites a fact that was replaced.

## Writing

1. State a relationship exactly: who, what, since when, how much. Never "associated with" or "linked to".
2. Write no sentence about significance. Say what the fact changes for repayment, or leave it out.
3. Name who said it and where. One source is one source.
4. Write no summary at the end of a section or a page.
5. Use "is" and "has".
6. Give every number its unit, its date and the company it belongs to.

Also:

- One subject per page. Split a page that covers two.
- Merge new information into the page. Do not append a dated entry. Leave what it replaces visible under the claim, marked outdated or disputed.
- Write nothing when a source adds nothing.
- Mark what you inferred.
- On the people pages, record what people said, asked for and decided, with the source. No judgements of character.
