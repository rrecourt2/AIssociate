# Changes from the first Bankability's standard

Version 3.0.0 was copied from version 2.0.0 in the `bankability` repository (`bankability-protocol/`) by a script, `docs/aissociate/convert_standard.py` in that repository. The script holds every table mentioned below. IDs of indicators, checks, slots and document types are unchanged.

## Repaired

1. **One list for evidence.** The checks named 160 kinds of evidence, and 24 of them existed in the list of 64 document types. There is now one list of 79 kinds of source: the 64 document types and 15 new ones, among them calls, notes by the officer and internal memos. The other names were mapped onto that list.
2. **Who an indicator applies to.** Each indicator now says so in `applies_to`. Indicators about a party follow how far the old standard reached from the borrower: borrower only, borrower and guarantor, or borrower, guarantor and sponsor. Five were moved by judgement, because their questions are about the company and not about the facility or the transaction: debt, liquidity, projections, working capital and tax.
3. **Bank indicators.** The four indicators for financial institutions apply only when the borrower is one.
4. **Dead references removed.** Two pointers to indicators that do not exist, three conditions on a check that does not exist, one hint on an answer that is not an option, and 16 references to six data-room slots that do not exist. The three checks behind those conditions were never asked. They are asked now.
5. **Placeholders filled.** Seven questions contained `{asset}`.
6. **Addressee.** Four questions about the lender itself are marked `ask_whom: lender`.
7. **A choice without options** became a text answer (the country of the transaction).

## Restated

1. **Branching.** The old `depends_on`, `on_true`, `on_false` and `on_answer` became `after` and `when` on the check that follows. The meaning is the same.
2. **Assumptions.** The old "why this matters" is now `assumption` where it states something a check can disprove (220 checks), and `why` where it explains the question (20 checks).
3. **Reference points.** The 16 thresholds are now `flag_when`, in the unit of the answer. Percentages are written as 20, not 0.20.
4. **Strength of evidence.** Primary, secondary and fallback are now `best`, `supporting` and `stated`.
5. **Links.** The 22 relationship types became 19 kinds of link. A role is the end of a link: whoever `borrows` is the borrower.

## Added

- **`disproved_by`** on 165 yes/no checks: whether a yes or a no disproves the assumption. It was set by hand from the wording of each check. It should be reviewed by someone who does credit work.

## Left out

- **Five indicators that asked how the deal is structured**, with 10 checks, and one check on group membership. The graph of parties and links holds those answers.
- **Everything the old engine used to rank and weight:** weights and weight shifts, trust levels, minimum evidence quality, reliability damping, effort, and the report sections an indicator feeds. The reasons that came with the weights are kept as `matters_more_when` and `matters_less_when`.
- **Parts of the old standard that Bankability 2 does not use yet:** data-room profiles, sector lexicons, the ISIC list, financing types, entity types, ratios, document templates and the schemas for financial spreading.

## Known gaps

- No check is due after due diligence.
- Only two indicators state a risk and a mitigant: currency risk and input concentration.
- The questions speak to "your company". They were written for a client who answers them directly.
