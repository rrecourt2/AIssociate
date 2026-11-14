# Changes from the first Bankability's standard

Version 3.0.0 was copied from version 2.0.0 in the `bankability` repository (`bankability-protocol/`) by a script, `docs/aissociate/convert_standard.py` in that repository. The script holds every table mentioned below. IDs of indicators, checks, slots and document types are unchanged.

Version 3.0.1 corrects the copy after a review. Those corrections are marked.

## Repaired

1. **One list for evidence.** The checks named 160 kinds of evidence, and 24 of them existed in the list of 64 document types. There is now one list of 79 kinds of source: the 64 document types and 15 new ones, among them calls, notes by the officer and internal memos. The other names were mapped onto that list.
2. **Who an indicator applies to.** Each indicator now says so in `applies_to`. Indicators about a party follow how far the old standard reached from the borrower: borrower only, borrower and guarantor, or borrower, guarantor and sponsor. Five were moved by judgement, because their questions are about the company and not about the facility or the transaction: debt, liquidity, projections, working capital and tax.
3. **Bank indicators.** The four indicators for financial institutions apply only when the borrower is one.
4. **Dead references removed.** Two pointers to indicators that do not exist, three conditions on a check that does not exist, one hint on an answer that is not an option, and 16 references to six data-room slots that do not exist. The three checks behind those conditions were never asked. They are asked now.
5. **Placeholders filled.** Seven questions contained `{asset}`.
6. **Addressee.** Four questions about the lender itself are marked `ask_whom: lender`.
7. **A choice without options** became a text answer (the country of the transaction).
8. **Conditions that could never hold** (3.0.1). 35 follow-up checks carried the condition that an earlier check is answered yes, where that earlier check asks for a number or a choice. The old engine read any answer as a yes. The copy took the condition literally, so these checks would have been marked not relevant. The condition is gone. They still wait for the earlier answer.
9. **Checks hidden in the normal case** (3.0.1). Fifteen checks were asked only when another check had an answer that has little to do with them, so they were hidden in the normal case. Fourteen are now always asked:
   - seasonality of revenue and contracted revenue (`OBS_REV_005`, `OBS_REV_006`, asked only when revenue was concentrated);
   - pending regulation (`OBS_REG_004`, only when the industry was not regulated);
   - disclosure of related-party transactions (`OBS_RP_005`, only when they were not at arm's length);
   - the share of imported inputs (`OBS_FX_INPUT_001`, only when debt was in another currency);
   - independent validation of feasibility (`OBS_FEAS_003`, only when technical risks were found);
   - cash flow shortfalls (`OBS_LIQ_004`, only when there were no cash reserves);
   - regulatory investigations (`OBS_LIT_004`, only when there was no litigation);
   - environmental liabilities, emissions reporting and climate risk (`OBS_ENV_002`, `OBS_ENV_004`, `OBS_ENV_005`, only when an impact assessment existed);
   - board minutes (`OBS_BOARD_005`, only when there were independent directors);
   - curtailment risk (`OBS_EGEN_005`, only when there was no grid connection);
   - whether the articles permit the transaction (`OBS_AUTH_004`, only when it was within signing limits).

   One was turned round: the debt-to-equity ratio (`OBS_DEBT_006`) was asked only of a company without debt, and is now asked of one with debt.
10. **Power checks** (3.0.1). The four indicators for power projects were asked about any project. They now apply only when the sector is renewable energy or conventional power.

## Restated

1. **Branching.** The old `depends_on`, `on_true`, `on_false` and `on_answer` became `after` and `when` on the check that follows. The meaning is the same, apart from repairs 8 and 9.
2. **Assumptions.** The old "why this matters" is now `assumption` where it states something a check can disprove (220 checks), and `why` where it explains the question (20 checks).
3. **Reference points.** The 16 thresholds are now `flag_when`, in the unit of the answer. Percentages are written as 20, not 0.20. One was widened in 3.0.1: `OBS_FX_PASSTHROUGH_001` now flags every answer but full pass-through.
4. **Strength of evidence.** Primary, secondary and fallback are now `best`, `supporting` and `stated`.
5. **Links.** The 22 relationship types became 19 kinds of link. A role is the end of a link: whoever `borrows` is the borrower.

## Added

- **`disproved_by`** on 162 yes/no checks: whether a yes or a no disproves the assumption. It was set by hand from the wording of each check. Two reviewers then judged all 165 again without seeing the values, and agreed with 162 (3.0.1). The other three lost the field, because the answer only casts doubt on the assumption or the question asks two things: `OBS_AUTH_003`, `OBS_CONT_003` and `OBS_SECPKG_002`. A review by someone who does credit work is still worthwhile.

## Left out

- **Five indicators that asked how the deal is structured**, with 10 checks, and one check on group membership. The graph of parties and links holds those answers.
- **Everything the old engine used to rank and weight:** weights and weight shifts, trust levels, minimum evidence quality, reliability damping, effort, and the report sections an indicator feeds. The reasons that came with the weights are kept as `matters_more_when` and `matters_less_when`.
- **Parts of the old standard that Bankability 2 does not use yet:** data-room profiles, sector lexicons, the ISIC list, financing types, entity types, ratios, document templates and the schemas for financial spreading.

## Licence

The first Bankability's standard was under Apache 2.0. Its licence holder released this version under MIT.

## Known gaps

- No check is due after due diligence.
- Only two indicators state a risk and a mitigant: currency risk and input concentration.
- Two reference points are doubtful. `OBS_FX_003` flags revenue in several currencies, which need not be unstable ones. `OBS_RP_DEMAND_001` does not flag loans without terms.
- The questions speak to "your company". They were written for a client who answers them directly.
