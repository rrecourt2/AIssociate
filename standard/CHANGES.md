# Changes

## Version 4.0.0: a new framework

Version 4.0.0 rebuilds the checks on the framework in [FRAMEWORK.md](FRAMEWORK.md). The data room, the kinds of source and the stages are unchanged.

### What changed

- **Claims.** Every indicator is now one claim: what the lender relies on, in a sentence that can turn out false. There are 70 of them.
- **Three jobs.** A check is a question, a test or a mitigant. A test states its own assumption, and the assumption is always what the lender relies on, so an answer against it is bad news. The old standard tested assumptions nobody holds, such as "Entity is debt-free". Those are now plain questions, and the tests ask what matters: "The party has paid its lenders as agreed".
- **Nine pillars in four layers** replace the eight workstreams: the deal; then each party on its own (environment, business, people and governance, cash flow and debt, liquidity and financial risks, environmental, social and impact); then the links; then the facility. No pillar holds more than a sixth of the checks. In version 3 more than half were financial and commercial, and twelve were environmental and social.
- **Checks follow reliance.** A facility `relies_on` the party or group whose cash flow repays it, whoever signs the loan. That party gets the full view. A guarantor is asked whether it can pay and must pay, and no longer how it runs a factory.
- **Links have their own checks.** A guarantee, a support undertaking, an owner or a group, a key customer, a key supplier, a builder or an operator, another lender and an asset given as security are each examined where they exist.
- **Discovery opens what applies.** The kind of credit (`OBS_SECTOR_001`: corporate, project, financial institution or fund) decides which view of a party applies. The sector (`OBS_SECTOR_002`) switches on the checks for power and for agribusiness. Until discovery has answered, those checks wait.
- **Discovery calls for structure.** 62 answers mean that a party, a link, an asset, a project or a contract must be in the structure. The tool says so until it is there, or until a decision says why it is not needed.
- **Mitigants.** 66 checks are mitigants. Each is asked once a test it answers has gone against the claim. In version 3 two indicators had a mitigant.
- **Stages after due diligence.** 27 checks are due at approval, legal documentation, disbursement or monitoring. In version 3 none was.

### The numbers

| | Version 3.0.1 | Version 4.0.0 |
|---|---|---|
| Indicators | 50 | 70 |
| Checks | 267 | 570 |
| of which questions, tests, mitigants | | 129, 375, 66 |
| Checks due at screening, concept, due diligence, later | 76, 33, 158, 0 | 93, 159, 291, 27 |
| Reference points | 16 (11 on a number, 5 on a choice) | 52 (16 on a number, 36 on a choice), each with its reason |

250 of the 267 checks keep their ID. Most were reworded. 49 of the 50 indicators keep their ID: `CAS_DISCOVERY_ESG_MANDATE_001` is gone and its three checks are in `CAS_ES_SCREENING_001`. Titles changed.

### Checks that were dropped

An ID is never used again for another meaning. Where the question changed in substance, the check has a new ID.

| Dropped | Why | Now |
|---|---|---|
| `OBS_BORROWER_002` | Asked whether the borrower has employees | `OBS_BORROWER_004`: the borrower carries on the business itself |
| `OBS_SECTOR_CONFIRM_001`, `OBS_SECTOR_CONFIRM_002` | Cross-checked property businesses only | `OBS_SECTOR_CONFIRM_003`, `OBS_SECTOR_CONFIRM_004`: the accounts show the stated business |
| `OBS_INPUT_006` | "Remaining tenor below 5 years" means nothing without the loan | `OBS_INPUT_009`: supply is contracted until the loan is repaid |
| `OBS_CONT_004` | Asked about expiry within twelve months | `OBS_CONT_005`: before the loan is repaid |
| `OBS_ERES_003` | Asked for two numbers in one answer | `OBS_ERES_007`: the P90 yield as a share of the P50 |
| `OBS_LIQ_001` | Yes or no on "cash reserves" | `OBS_LIQ_006`: the amount of free cash |
| `OBS_WC_003` | "Is inventory management documented" cannot fail in a way that matters | `OBS_WC_006`: stock is counted and valued by someone independent |
| `OBS_SECPKG_005` | "Consistent with the risk profile" names nothing to measure against | `OBS_SECPKG_006`: forced-sale value against the most that can be owed |
| `OBS_TS_003` | "Appropriate for the risk profile", likewise | `OBS_TS_006`, `OBS_TS_007`, `OBS_TS_008`: tenor, timing of repayments, reliance on a refinancing |
| `OBS_COST_003` | Repeated `OBS_INPUT_001` | |
| `OBS_HEDGE_002` | Repeated `OBS_HEDGE_003` and `OBS_HEDGE_004` | |
| `OBS_FIG_005` | Repeated `OBS_ACC_001` and `OBS_ACC_003` | |
| `OBS_BO_003`, `OBS_OWN_002`, `OBS_LEGAL_004`, `OBS_INVESTOR_ROLE_004` | Each repeated a neighbour | |

### Answers that no longer fit

A deal that recorded answers under version 3 has to answer these again. The options changed:

- `OBS_SECTOR_001` (now the kind of credit), `OBS_SECTOR_002` (now eight sectors), `OBS_VALUE_CHAIN_001`, `OBS_LIFECYCLE_001`.
- `OBS_GUARANTEE_KIND_001`, `OBS_FX_003`, `OBS_INPUT_MIT_001`, `OBS_COV_001`, `OBS_COV_004`, `OBS_KYC_005`, `OBS_BO_006`.
- `OBS_ESG_MANDATE_003` is now a text answer.

### The format

- An indicator has `pillar` and `claim`. `workstream`, `why_it_matters` and the two statement blocks `risk` and `mitigant` are gone.
- A check may have `mitigant: true` and `calls_for`.
- A condition may say `against: true`: the answer to that check goes against its own assumption.
- A reference point may name several options: `is poor or end_of_life`. Every reference point has its reason in `why`.
- An assumption needs an answer that can go against it (`disproved_by` or `flag_when`), and the other way round. The build refuses anything else.
- `look_again_when` names a kind of source or a check. The tool now acts on it.
- Kinds of link: `relies_on` is new and gives the role `repayment_source`. `controls` gives the role `controller`. `supports` and `completion_support` give the role `guarantor`, so that whoever promises support is examined for whether it can keep the promise.

### How it was made and checked

1. The framework was written first, from the first Bankability's method, from how the rating agencies build a credit view and from development-bank practice.
2. Eleven writers each rewrote one part against the framework and one common brief. A checker refused output that broke the format or the rules it can test.
3. Every one of the 441 tests and mitigants was then judged blind: a judge saw the question and the assumption, not the answer the standard marks as going against it. No yes/no test and no test on a number had the wrong direction. Six tests on a choice differed on a middle option. Three were changed: `OBS_EREG_002` (a hybrid tariff now also goes against), `OBS_EGEN_007` (so does a shared curtailment risk) and `OBS_LIFECYCLE_CONFIRM_002` (the question now defines its options).

Nobody who does credit work for a living has reviewed it yet.

### For a credit reviewer

- **Reference points on a number.** `OBS_DS_003` debt service cover below 1.2. `OBS_ACC_005` accounts older than 18 months. `OBS_FX_002` foreign-currency revenue above 20 percent. `OBS_FX_INPUT_001` imported inputs above 25 percent. `OBS_HEDGE_003` hedged share at most 50 percent. `OBS_INPUT_002` largest input above 30 percent of cost. `OBS_INPUT_MIT_003` and `OBS_REC_SECURITY_001` below 50 percent. `OBS_REC_GOV_001` above 20 percent. `OBS_REV_004` revenue falling. `OBS_WC_005` overdue receivables above 10 percent. `OBS_RP_EXPOSURE_001` above 10 percent of equity. `OBS_RP_PEAK_001` above 1.5. `OBS_FIC_002` capital headroom below 2 points. `OBS_FIP_004` restructured loans above 5 percent. `OBS_SECPKG_006` cover below 100 percent. Each has its reason in `why`. An institution changes them in its own layer.
- **Tests that will go against the claim in many sound deals**, by design, so that the mitigant is asked: an unsecured loan (`OBS_COLLATERAL_001`), a refinancing (`OBS_USE_002`), a loan in a currency the party does not earn (`OBS_FX_008`, `OBS_TS_009`), a price-taker (`OBS_MARKET_003`), a single plant (`OBS_OPS_003`), a board that has never said no (`OBS_BOARD_007`), another loan that falls due earlier (`OBS_LENDER_004`), a subsidised tariff (`OBS_EREG_004`), a company without a compliance officer (`OBS_KYC_001`).
- **Sizes named in questions** ("about a tenth", "about a fifth", "three years") are guides and say so in their notes.
- **Words that carry a definition** in their note: `mixed` in `OBS_CASHFLOW_BASIS_001`, `blended` in `OBS_LIFECYCLE_CONFIRM_002`, the border between agribusiness and trade in `OBS_SECTOR_002`.

### Known gaps

- **No module for funds.** A fund gets the deal, the links and the facility, and little about itself.
- **Overlap between pillars has not been pruned.** The writers could not see each other's work. Known neighbours: a failing utility (`OBS_OPS_004`, `OBS_INPUT_005`); a rejected product (`OBS_OPS_006`, `OBS_AGRI_007`); cash conversion (`OBS_DS_006`, `OBS_CHG_005` and working capital); refinancing (`OBS_DS_007`, `OBS_DEBT_003`, `OBS_TS_008`); a customer's contract (`OBS_OFFTAKER_008`, `OBS_CONT_005`, `OBS_CONT_006`); a penalty for financial crime (`OBS_LIT_005`, `OBS_KYC_003`); charges on assets (`OBS_LENDER_002`, `OBS_SECPKG_003`, `OBS_SECASSET_006`, `OBS_SECLG_002`).
- **`lends_to` covers a loan received and a loan given.** The checks on another lender make no sense for a loan the party gave to an affiliate. The first check says so.
- **Kinds of source are missing** for a land title, a court search, an independent engineer's report, a certificate from a certification scheme and an impact report. The checks use the nearest kind.
- **A bank's own lending** is not examined for environmental and social risk.
- **A party that is a person or a public body** does not fit every check on legal standing and authorisation.

## Versions 3.0.0 and 3.0.1: the copy from the first Bankability

Version 3.0.0 was copied from version 2.0.0 in the `bankability` repository (`bankability-protocol/`) by a script, `docs/aissociate/convert_standard.py` in that repository. The script holds every table mentioned below. Version 3.0.1 corrected the copy after a review. Those corrections are marked.

### Repaired

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

### Restated

1. **Branching.** The old `depends_on`, `on_true`, `on_false` and `on_answer` became `after` and `when` on the check that follows. The meaning is the same, apart from repairs 8 and 9.
2. **Assumptions.** The old "why this matters" is now `assumption` where it states something a check can disprove (220 checks), and `why` where it explains the question (20 checks).
3. **Reference points.** The 16 thresholds are now `flag_when`, in the unit of the answer. Percentages are written as 20, not 0.20. One was widened in 3.0.1: `OBS_FX_PASSTHROUGH_001` now flags every answer but full pass-through.
4. **Strength of evidence.** Primary, secondary and fallback are now `best`, `supporting` and `stated`.
5. **Links.** The 22 relationship types became 19 kinds of link. A role is the end of a link: whoever `borrows` is the borrower.

### Added

- **`disproved_by`** on 162 yes/no checks: whether a yes or a no disproves the assumption. It was set by hand from the wording of each check. Two reviewers then judged all 165 again without seeing the values, and agreed with 162 (3.0.1). The other three lost the field, because the answer only casts doubt on the assumption or the question asks two things: `OBS_AUTH_003`, `OBS_CONT_003` and `OBS_SECPKG_002`. A review by someone who does credit work is still worthwhile.

### Left out

- **Five indicators that asked how the deal is structured**, with 10 checks, and one check on group membership. The graph of parties and links holds those answers.
- **Everything the old engine used to rank and weight:** weights and weight shifts, trust levels, minimum evidence quality, reliability damping, effort, and the report sections an indicator feeds. The reasons that came with the weights are kept as `matters_more_when` and `matters_less_when`.
- **Parts of the old standard that Bankability 2 does not use yet:** data-room profiles, sector lexicons, the ISIC list, financing types, entity types, ratios, document templates and the schemas for financial spreading.

### Licence

The first Bankability's standard was under Apache 2.0. Its licence holder released this version under MIT.
