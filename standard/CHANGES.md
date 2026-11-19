# Changes

## Tool 0.10.0: the package renamed

The Python package is now `aissociate`, so the command is `python3 -m aissociate`, and the skill's launcher is `scripts/run.py`. Nothing else changes, and the standard stays at 4.4.0. A deal folder made before works unchanged: nothing in it names the package.

## Tool 0.9.0 and standard 4.4.0: AIssociate

Most of what follows came out of a worked example on a third real company, from its public documents only, and out of the owner's reading of its wiki. The tool and its guide are now AIssociate, the AIssociate plugin. The list of checks is the Bankability DDQ, which the files call the standard, now at 4.4.0: no check is added, dropped or asked differently, and none says any longer what settles it. The skill is in `skill/aissociate` and packs to `dist/aissociate.zip`. The Python package stays `bankability2` and the launcher `scripts/bk2.py`, so a deal folder made by 0.8.0 works unchanged.

- **No `settled_by`.** Version 4.3.0 gave each check what settles it: the company, a screening, the terms, the lender, an expert or public sources. Who or what settles a check depends on the deal, so the analyst and the assistant say it for each deal, where it helps, in the note on an open check. `status` and the page of checks no longer count or filter the open checks by it. The page gives the open checks by stage in its first lines, and its names for a screening are every party and person the record names. `upgrade` takes a deal on 4.3.x to 4.4.0 and lists no check as changed: every answer stands. A check that a deal's or an institution's own layer added with `settled_by` keeps that field, which nothing reads any more; `adjust` with `{"do": "change", "target": "<the check>", "set": {"settled_by": null}, "reason": "No longer read."}` takes it out.
- **A rounded figure passes.** `check` lets a figure pass when a cited record holds the same figure, or one that rounds to it at the precision the page writes, with a scale word such as bn on either side: KES 4.1bn against KES 4,060m. A figure cut short does not: KES 4.0bn is reported. Where the page and the record both give a scale word and the two differ, the figure is reported unless the amounts are equal: KES 4,060bn against KES 4,060m is reported, and so is 50bn against 50 million, while KES 4.06bn against KES 4,060m passes. A whole number below 10 is now checked where a scale word follows it. The short k and m count as scale words only when they are written against the number, as in 4,060m or 50k.
- **A question can carry a note**: why it was reworded or narrowed. It shows with the question: on the page of its subject, in `show <ID>` and in the view.
- **An open check can carry a note on what is missing**, for one subject, with `adjust` and `"do": "note"`. It answers nothing, shows beside the open check on the page of checks, in `status` where the check is listed (every one with `--all`) and in `show <check>`, and goes once the check is answered.
- **Own word on the page of checks.** A favourable answer to a test that rests only on what a party says of itself, or only on evidence the check lists as `stated`, is marked `own word` there and in `show <check>`.
- **What the wiki has not taken in.** `show <deal> uncited` lists the current facts that no page cites, by source, and `status` says how many there are. A fact that only a draft cites is listed: it has not been taken into the wiki. `pages` prints how many words each page holds.
- **No drafts in the view.** A draft is written when the analyst asks for one, from the wiki and the record. It is the analyst's document in `Internal/outputs`, not part of the wiki, so the browser view no longer lists the drafts or carries their text. `check` still reads them, and a link from a page to a draft opens the file.
- **A timeline in the wiki.** `pages` writes `Internal/wiki/timeline.md` from the log of the record: what was recorded, when and by whom, the newest first. Where a page of that name is there that the tool did not write, as a folder made by 0.8.0 may hold, `pages` leaves it alone, writes no timeline and says to rename the page.
- **The guide:** what a group says does not answer a check asked of one of its companies unless it gives something of that company's own. An answer that took work is kept on a page. Every few sources, and before a draft, the assistant reads the changed pages for meaning. An earlier text of a page is in the version history of the folder's storage.

## Version 4: a new framework

Version 4 rebuilds the checks on the framework in [FRAMEWORK.md](FRAMEWORK.md). The data room and the stages are unchanged from version 3. Version 4.0.1 is version 4.0.0 after two reviews. Version 4.1.0 is version 4.0.1 after its first trial on a real company, version 4.1.1 is 4.1.0 after a second pass of that trial, version 4.2.0 follows an assessment of which open checks of that deal are material, version 4.2.1 is 4.2.0 after a review, version 4.2.2 adds notes from the third round of the trial, version 4.3.0 says what settles each check, version 4.3.1 adds what a trial on a second company showed, and version 4.4.0, at the top of this file with tool 0.9.0, takes what settles a check out again. The seven before 4.4.0 come first here, the latest on top. The sections after them describe version 4 as it stood at 4.0.1.

### Version 4.3.1: what a second company showed

Assistants with only the skill built the record of a second company, listed on a stock exchange, from what it had published. Their reports named a few places where the standard left a choice open. No check is added, dropped or asked differently.

- **What a listed company publishes has a kind.** A page of its website, a news release and a broker's research report are public sources, and the description of `public_source` now says so. A sustainability report is filed as an annual report, the company's own report on its governance as board composition, and a notice filed with a stock exchange as a regulatory document. An assistant had filed website pages as company records, which many checks count as supporting evidence: `company_record` now says that it is for what the company keeps, not for what it publishes about itself.
- **Three years of revenue give two changes.** The note of `OBS_REV_004` says how the average is taken.
- **Lines that come up for renewal in the same year are taken together.** The note of `OBS_LENDER_004` says so: one by one each could be repaid from a year's cash flow, together they could not.
- **Where the party is a group**, its consolidated accounts are "party alone" for `OBS_ACC_004`.

**A deal that runs on 4.3.0.** `upgrade` lists three checks as changed, each by its note. A source that was filed under a kind that fits less well can be changed in place: send its `id` with the new `kind`. It keeps its ID and its place in the folder.

### Version 4.3.0: what settles each check

After the third round an assistant divided the open checks of the trial deal by hand into a few pieces of work: one request to the company, one screening of names, the terms of the loan, the lender's own answers, and a little public search. The standard now carries that division, so that the tool can print it.

- **`settled_by` on every check.** It names the main route to an answer: `company` (its documents or its answers), `screening` (a search on a name), `terms` (the terms of this financing once they are on paper), `lender` (the lender itself), `expert` (counsel, an engineer, a valuer, a consultant) or `public` (registries, statistics, regulations, the press). Three readers tagged the 551 checks and a fourth read every tag: 360 company, 70 terms, 53 expert, 30 lender, 22 public, 16 screening.
- **`ask_whom` is gone.** `settled_by: lender` (gone since 4.4.0) says the same.
- **"Analyst" for "officer".** The kind of source `officer_note` is now `analyst_note`.
- **The first pillar is called "The opportunity".** It is an opportunity until terms are on paper.
- **A part of an asset is examined with the whole.** An asset that is `part_of` another asset is asked no checks. A line or a machine inside a plant can then be recorded as what it is.

No check is added or dropped: 551 checks as before.

**Open, for a practitioner to confirm.** One value is the main route, and some checks have two: the party is asked and a register is searched, or the company is asked first and the terms settle it. The second route is not recorded. The tests that count the proposed loan and do not wait for its terms are tagged `company`, and have to be answered again once the terms are known.

**A deal that runs on 4.2.2.** `upgrade` lists as changed only the checks whose question, answer, conditions or note changed: what settles a check and the evidence it lists do not change what an answer means. It takes the record to the new names: a source of kind `officer_note` becomes `analyst_note`, and `officer` becomes `analyst` where a fact says who said it and where a decision says who took it or who owns it. The standard carries the list of such names under `renamed`. With tool 0.6.0 it also moves the pages of the wiki to the new shelves, repoints the links between them and writes the contents page, the page of checks and the browser view again. The words in the pages themselves stay as they were written.

### Version 4.2.2: notes from the third round of the trial

In the third round an assistant was asked where the decisions of a subsidiary are taken, and another acted on a credit colleague's review of the open checks. The documents showed a company with no board of its own, whose large decisions were resolved by the board of its parent. The standard already examines such a company at the parent: `OBS_BOARD_001` is answered no, `OBS_BOARD_006` asks who oversees in the board's place, and the parent is asked the board checks as a company of the group. The changes say this plainly and settle two readings on which a colleague and an assistant differed.

- **A company led by one office-holder has no board.** The note of `OBS_BOARD_001` says so, also where the owner's board takes its large decisions.
- **The board of the parent in the board's place.** The note of `OBS_BOARD_006` asks the fact to say so, and to count how many members of that board manage the party: if all of them do, the body does not count. The parent's board is tested where the parent is asked these checks, which is when it is recorded as a member of the group the loan relies on.
- **Independent of the significant shareholders.** `OBS_BOARD_003` said "not a shareholder nor a shareholder's relative". Read to the letter, that ruled out a director whose relative had a very small holding, while the claim speaks of the main shareholder. The question, its assumption and its wording for the company now say "significant shareholder". The note gives a guide for what is significant, and says that a director named by a financial investor that does not control the company counts.
- **Which earnings make an asset matter.** `OBS_ASSET_007` asks whether an asset carries about a tenth of the earnings that repay the loan. One reader took the plant's own contribution and another its owner's profit after interest, and they got opposite answers. The note says the first is meant, set against the same line of the whole business.

No check is added or dropped: 551 checks as before.

**Open, for a practitioner to confirm.** Whether a body that oversees a subsidiary should count when most, and not all, of its members are that subsidiary's own managers: today the fact says so and nothing tests it. And whether `OBS_BOARD_007`, which asks if the board ever turned a proposal down, should be a test of the claim and not a question: a company overseen by its parent's board is asked one test of its own.

**A deal that runs on 4.2.1.** `upgrade` lists the four checks as changed. Read the answer to `OBS_BOARD_003` again where a director's small holding decided it, and the answer to `OBS_ASSET_007` where the owner's profit after interest was the measure. Version 0.5.2 of the tool comes with this version of the standard, and two things read differently with it. A claim stands only when every test is answered on evidence the check lists as supporting or best, with nothing thin, old or on someone's own word, so a claim that stood may now stand so far. And a decision without an owner or a date speaks only of the subject it names in `about`: on an open check it takes the check off for that subject.

### Version 4.2.1: after a review of 4.2.0

A reviewer read 4.2.0 before it was released and found gates that could hide a check when it matters.

- **"No terms yet" made 24 checks fall away.** `OBS_TS_001` asked whether a term sheet was agreed. At screening the honest answer is no. The checks on terms, covenants and conditions then left the list, and nothing brought them back. `OBS_TS_011` takes its place. It asks how far the terms have got on paper, and its answers are proposed, agreed and signed. It has no answer for "none yet". While it is open the 24 checks wait, and `status` lists the question as the thing to do. It is due by the concept stage. `OBS_TS_001` was due at screening.
- **The funding test fell away where the use of the money was vague.** `OBS_USE_003` waited for a yes on `OBS_USE_001`, which is a test and not an opening question. A loan with no list of uses then lost the test of whether the plan is funded. `OBS_USE_003` is asked without a condition again.
- **"None" could be read as "none yet".** The note of `OBS_SECPKG_001` now says to choose "none" only where the loan is to be unsecured, and to leave the question open while the security is not settled. The note of `OBS_ASSET_007` says to answer again when the security is settled.

One check is dropped and one is new: 551 checks as before, of which 119 questions, 365 tests and 67 mitigants.

**Open, for a practitioner to confirm.** Since 4.2.0 the three checks on traceability are asked of an agribusiness, or where `OBS_ES_003` flags the place or the source of the raw materials. A manufacturer that buys a farm or forest commodity from a setting that no list flags is not asked them.

**A deal that runs on 4.2.0.** After `upgrade`, an answer to `OBS_TS_001` no longer counts. Leave `OBS_TS_011` open until terms are on paper. Where `OBS_SECPKG_001` was answered "none" because the security was not yet discussed, withdraw that answer.

### Version 4.2.0: a check waits for the answer that opens it

**The assessment.** After the second pass the trial deal had 580 checks open or waiting. Three assessors, each working as a credit analyst on a third of the pillars, judged every one of them: would it change a credit decision on this deal, and what would settle it?

| Judgement | Checks |
|---|---|
| Material, and the record already decides it | 67 |
| Material, needs the company | 96 |
| Material, needs a third party: a screening, a registry, counsel, a consultant | 64 |
| Material, needs the terms of the loan | 55 |
| Conditional: a real question only if an earlier answer turns out a certain way | 180 |
| Not material for this deal | 118 |

So about half were material. A third were conditional, most of them mitigants that are asked only if a test goes against its claim. A fifth would not have changed a decision on this deal. The 67 that the record already decided were facts recorded without the check they answer.

**What was not material, and what changed.**

- **Checks on terms were open before there were terms.** The tests of the term sheet, the covenants and the conditions, 24 checks, are now asked once a term sheet is agreed (`OBS_TS_001`). The checks on security in law, the assignment of payments and the forced-sale value are asked once something is offered as security (`OBS_SECPKG_001`).
- **A clause of the lender's own agreement was asked once for each other lender.** `OBS_LENDER_007` is dropped. `OBS_COV_011` asks the same once, of the facility.
- **Every plant was examined as if repayment hung on it.** `OBS_ASSET_007` is new: does repayment depend on this asset, or is it security? The five tests on its condition, its upkeep and its remaining life are asked when the answer is yes. A contract and a customer already had a question of this kind.
- **Three checks did not wait for their own opening question.** `OBS_OFFTAKER_004` now waits for `OBS_OFFTAKER_001`, `OBS_CONT_005` for `OBS_CONT_001`, and `OBS_OWN_007` for `OBS_OWN_006`.
- **Forest and traceability were asked of a recycler.** `OBS_SUPPLYCHAIN_001`, `OBS_SUPPLYCHAIN_002` and `OBS_SUPPLYCHAIN_003` are asked of an agribusiness, or where `OBS_ES_003` has flagged the place or the source of the raw materials.
- **Sources and uses were asked before a use was set out.** `OBS_USE_003` waits for `OBS_USE_001`. Version 4.2.1 takes this back.
- **A company that runs its own plant was asked for its operator's contract.** The descriptions of `operates` and `builds` now say that they are for a party that works for the owner under a contract.

One check is dropped and two are new: 551 checks, of which 119 questions, 365 tests and 67 mitigants.

**Left as it was, on purpose.** `OBS_GROUP_010` is still asked of every owner tie, also where the lender relies on it in neither direction: an owner that needs the company's cash takes it whatever the lender relies on. The checks on other lenders are still asked of each lender link: the fix there is to give a link only to a lender that matters.

**A deal that runs on 4.1.1.** The tool's `upgrade` command puts 4.2.0 into the deal folder. Then:

- Answer `OBS_ASSET_007` for each asset. Until then the tests on the asset wait.
- An answer to `OBS_LENDER_007` no longer counts. Answer `OBS_COV_011` once there are terms.
- Checks on terms, covenants and conditions are asked once `OBS_TS_001` is answered yes, and checks on security once `OBS_SECPKG_001` names a kind of security. Version 4.2.1 changes the first of the two.

### Version 4.1.1: after the second pass of the trial

**The second pass.** The deal folder of the first trial was upgraded to 4.1.0 and worked on again by assistants that had only the skill and the tool. They brought the record in line with the new standard, took in nine more documents and a new purpose for the loan, reworked the wiki and drafted the proposal again. A reviewer compared the two passes and read sampled facts against the original documents.

**What held.** Open checks fell from 630 to 357. Eight claims were challenged, against fourteen, and the reviewer judged each of the eight justified. The three overstated challenges of the first pass were gone. 43 of 44 sampled facts matched their documents, and 12 of 12 figures stood in the originals at the place the fact gives.

**What did not, and what changed.**

- **An owner link brought checks wherever it pointed.** A company that owns its plant was asked the nine tests of "Owner and group". `owns` now carries `counts_for: [party, group]`: it gives its role, and is asked its checks, only where it points at a party or a group. Who owns a plant or a project is still recorded with `owns`. `sponsors` is unchanged, and its description now says that it is for whoever stands behind the borrower or the project the loan pays for.
- **A financed project was asked what is asked of a whole business.** Of its 29 open checks most repeated, in the same words, what the group was asked. Thirteen checks are now asked only of the borrower and the repayment source: `OBS_ENV_004`, `OBS_ENV_006` and `OBS_ENV_007`, `OBS_SUPPLYCHAIN_001` to `OBS_SUPPLYCHAIN_005`, and `OBS_SOC_001`, `OBS_SOC_003`, `OBS_SOC_004`, `OBS_SOC_005` and `OBS_SOC_006`. The project keeps what is its own: its impact assessment and permits, contamination and climate exposure of its site, its land, its neighbours and its guards. The notes of five of the thirteen now say to count what the loan pays for: the workers who build it, its expected emissions and the suppliers of its equipment.
- **The parent fell out of view when its subsidiary became the borrower.** People and governance was asked of a company only while it held a role of its own, so the listed parent of the group was no longer asked about its board, its controls or its shareholders, and a pledge over its shares counted against no claim. The tool now asks each member of a group what is asked of a legal entity, in the group's place. For an owner that is not itself asked, the notes of `OBS_OWN_008` and `OBS_OWN_009` now say to look up the chain of owners: a pledge over the owner's shares is recorded with its level, and counts under `OBS_OWN_009` when its enforcement would change who controls the party. The note of `OBS_OWN_008` also gives a sense of size: a pledge counts when it could move control or a blocking stake.
- **What an owner owes on its own account** was asked only where the lender relies on cash coming up from the company. `OBS_GROUP_011` is now asked whenever the lender relies on the tie in either direction: an owner's own debt comes before any support it can give.
- **"Stands" was said too early.** A claim stood as soon as one test was answered in its favour, with others still open. The tool now says "stands so far" until every test of the claim is answered. A question on which two facts disagree now makes its claim contested, as a test does. [FRAMEWORK.md](FRAMEWORK.md) has the five places a claim can stand in.

No check was added or dropped and no ID changed.

**A deal that runs on 4.1.0.** The tool's `upgrade` command puts 4.1.1 into the deal folder. Then look at these:

- An `owns` link that points at an asset or a project gives no role any more. Nothing needs to be done.
- An answer that was recorded for a financed project to one of the thirteen checks no longer counts there. The tool lists it.
- A claim that stood with tests still open now stands so far.
- A member of a group that holds no role of its own is asked the checks on people and governance. Answers recorded for it count again.

### Version 4.1.0: after the first trial on a real company

**The trial.** Version 4.0.1 was tried on a real, listed company, from its public documents only. Assistants that had nothing but the skill and the tool built the record and the wiki from eight documents, took in two later ones and drafted a financial proposal. A reviewer then checked a sample of the recorded facts against the documents and read every page. The company is not named here, and its deal folder is not part of this repository.

**What held.** 85 of the 88 sampled facts matched their documents. Each assistant picked the deal up from the record where the last one had stopped. The claims pointed at the real issues: the reviewer judged ten of the fourteen challenged claims justified, among them how the loan would be repaid.

**What did not.**

- **Roles arose from any link.** An owner who had guaranteed existing bank loans in person became a guarantor of the deal. An existing bond, recorded as a facility, was asked the 26 checks of a new loan.
- **The business was examined twice.** Of 630 open checks, 129 were asked of the borrower and again of the group it belongs to.
- **A person was asked what is asked of a company**, such as whether it is incorporated and whether its accounts are audited.
- **A project the loan would not pay for** brought 30 checks of its own.
- **Tests without a sense of size challenged trifles.** Currency risk went against its claim on one very small foreign loan, tax on a small incentive, and existing debt on a guarantee for a company inside the borrower's own group. Three of the fourteen challenges were overstated for this reason.
- **A test that was already decided stayed open.** Debt was far above the reference point before any new loan, and the test on leverage waited because it asks about debt "after this loan".
- **`OBS_RP_006` had no answer** for the main related-party fact of the deal: security and guarantees that the owners give for the company's debt.
- **Two notes disagreed** on a business that trades more than it makes. The sector went by revenue and the place in the value chain by profit.
- **Kinds of source were missing** for an annual report, a prospectus and a press article. An annual report that was not itself audited was filed as audited, and its facts counted as the best evidence.
- **Rigour without depth.** The pages were long and followed the checks. Nothing in the standard asked what the business is and what is particular about it.

**What changed.**

- **The loan under review.** A link type may carry `counts_for`. `borrows`, `guarantees`, `supports` and `secures` give their role, and are asked their checks, only when they point at a facility, and `completion_support` when it points at a facility or a project. A facility is a loan under review. Debt that already exists is a `lends_to` link with its terms, its security and its guarantors as facts about the link.
- **The perimeter.** Each pillar of the party layer carries `asked_of`. Environment, business, cash flow and debt, liquidity and financial risks, and environmental, social and impact are asked of the perimeter: a member of a group that is asked the same check is not asked. People and governance is asked of each legal entity, and never of a group. In the pillar Links, related parties and a guarantor's capacity follow the perimeter too: dealings between the companies inside it are examined with the tie between them.
- **A person** is a new kind of subject, with IDs that start with `N`. It is asked six indicators only: sanctions, political exposure, integrity record, source of funds, litigation and the guarantor's capacity. A party is now a company or a public body.
- **Checks follow the financing.** `finances` is a new kind of link, from the facility to the project or asset it pays for. The five indicators on a project (`CAS_FEASIBILITY_001` and the four on power) and the project part of the three on environment, social matters and land are asked of the financed project. `OBS_REQUEST_003` is new: does the money pay for a project or an asset that can be named.
- **Size.** `OBS_FX_008`, `OBS_TAX_008` and `OBS_DEBT_009` now ask about an amount that matters, with "about a tenth" as a guide in the question and a note that says so. `OBS_DEBT_009` no longer counts a guarantee for a member of the group that repayment relies on. The three keep their IDs.
- **Decided before the loan.** Eight tests that speak of this loan now say in their note that an answer which already goes against the assumption on today's debt is recorded at once: `OBS_DS_003`, `OBS_DS_004`, `OBS_DS_005`, `OBS_FX_008`, `OBS_FX_009`, `OBS_RATE_002`, `OBS_MARKET_004` and `OBS_REV_008`.
- **`OBS_RP_006`** has two new options: guarantees and security received, and pay and advances to insiders. Its note says to choose every kind that applies. A guarantee given for a related party no longer calls for a link.
- **One rule for a business that trades more than it makes.** `OBS_SECTOR_002` and `OBS_VALUE_CHAIN_001` both go by where the profit comes from.
- **Questions that ask for description.** How the business earns its money (`OBS_BUSINESS_MODEL_001`), what is particular about it (`OBS_BUSINESS_MODEL_002`), what the project is (`OBS_FEAS_008`), and, where the lender relies on cash from an owned company, what the owner owes on its own account and what cash it received (`OBS_GROUP_011`, `OBS_GROUP_012`). They test nothing. Their answers feed the wiki.
- **Kinds of source.** `annual_report`, `prospectus` and `press_article` are new. `audited_annual_report` is now titled "Audited financial statements". Wherever a check counts audited statements as its best evidence, an annual report and a prospectus count as supporting: 208 checks. Wherever a check lists a public source, a press article counts the same: 48 checks. The one exception is `OBS_SUPPLYCHAIN_004`, where the public source is the register of a certification scheme and counts as best evidence. A press article is supporting there.

No check was dropped and no ID changed. Six checks are new.

**A deal that runs on 4.0.1.** The tool's `upgrade` command puts 4.1.0 into the deal folder. Then look at these:

- An answer of yes to `OBS_FX_008`, `OBS_TAX_008` or `OBS_DEBT_009` that rests on a small amount is now a no.
- `OBS_SECTOR_002` goes by profit. An answer that went by revenue may change.
- A `guarantees`, `supports` or `secures` link that does not point at a facility gives no role any more. Record what it stood for as a fact about the `lends_to` link of that debt.
- Existing debt that was recorded as a facility or a contract is recorded again as a `lends_to` link.
- A natural person that was recorded as a party is recorded again as a person.
- A project is checked only once the facility `finances` it.
- Answers on the business and its money that were recorded for a member of the perimeter's group no longer count there. The tool lists them.

### What changed from version 3

- **Claims.** Every indicator is now one claim: what the lender relies on, in a sentence that can turn out false. There are 70 of them.
- **Three jobs.** A check is a question, a test or a mitigant. A test states its own assumption, and the assumption is always what the lender relies on, so an answer against it is bad news. The old standard tested assumptions nobody holds, such as "Entity is debt-free". Those are now plain questions, and the tests ask what matters: "The party has paid its lenders as agreed".
- **Nine pillars in four layers** replace the eight workstreams: the deal; then each party on its own (environment, business, people and governance, cash flow and debt, liquidity and financial risks, environmental, social and impact); then the links; then the facility. No pillar holds more than a fifth of the checks. In version 3 more than half were financial and commercial, and twelve were environmental and social.
- **Checks follow reliance.** A facility `relies_on` the party or group whose cash flow repays it, whoever signs the loan. That party gets the full view. A guarantor is asked whether it can pay and must pay, and no longer how it runs a factory.
- **Links have their own checks.** A guarantee, a support undertaking, an owner or a group, a key customer, a key supplier, a builder or an operator, another lender and an asset given as security are each examined where they exist.
- **Discovery opens what applies.** The kind of credit (`OBS_SECTOR_001`: corporate, project, financial institution or fund) decides which view of a party applies. The sector (`OBS_SECTOR_002`) switches on the checks for power and for agribusiness. Until discovery has answered, those checks wait.
- **Discovery calls for structure.** 60 answers mean that a party, a link, an asset, a project or a contract must be in the structure. The tool says so until it is there, or until a decision says why it is not needed.
- **Mitigants.** 67 checks are mitigants. Each is asked once a test it answers has gone against the claim. In version 3 two indicators had a mitigant.
- **Stages after due diligence.** 26 checks are due at approval, legal documentation, disbursement or monitoring. In version 3 none was.

### The numbers

| | Version 3.0.1 | Version 4.0.1 | Version 4.1.0 | Version 4.2.0 |
|---|---|---|---|---|
| Indicators | 50 | 70 | 70 | 70 |
| Checks | 267 | 544 | 550 | 551 |
| of which questions, tests, mitigants | | 112, 365, 67 | 118, 365, 67 | 119, 365, 67 |
| Checks due at screening, concept, due diligence, later | 76, 33, 158, 0 | 85, 148, 285, 26 | 88, 151, 285, 26 | 89, 151, 285, 26 |
| Reference points | 16 (11 on a number, 5 on a choice) | 51 (16 on a number, 35 on a choice), each with its reason | 51 | 51 |
| Kinds of source | 79 | 79 | 82 | 82 |
| Kinds of subject, kinds of link | 6, 19 | 6, 20 | 7, 21 | 7, 21 |

The rest of this section compares 4.0.1 with 3.0.1. 216 of the 267 checks keep their ID. Most were reworded. 328 checks are new. 49 of the 50 indicators keep their ID: `CAS_DISCOVERY_ESG_MANDATE_001` is gone and its checks are in `CAS_ES_SCREENING_001`. Titles changed.

### Checks that were dropped

An ID is never used again for another meaning. 51 checks of version 3 are gone.

**Replaced by a sharper check under a new ID**

| Dropped | Why | Now |
|---|---|---|
| `OBS_BORROWER_002` | Asked whether the borrower has employees | `OBS_BORROWER_004`: the borrower carries on the business itself |
| `OBS_SECTOR_CONFIRM_001`, `OBS_SECTOR_CONFIRM_002` | Cross-checked property businesses only | `OBS_SECTOR_CONFIRM_003`, `OBS_SECTOR_CONFIRM_004`: the accounts show the stated business |
| `OBS_INPUT_006` | "Remaining tenor below 5 years" means nothing without the loan | `OBS_SUPPLIER_004`, asked about each key supplier |
| `OBS_CONT_004` | Asked about expiry within twelve months | `OBS_CONT_005`: before the loan is repaid |
| `OBS_ERES_003` | Asked for two numbers in one answer | `OBS_ERES_007`: the P90 yield as a share of the P50 |
| `OBS_LIQ_001` | Yes or no on "cash reserves" | `OBS_LIQ_006`: the amount of free cash |
| `OBS_WC_003` | "Is inventory management documented" cannot fail in a way that matters | `OBS_WC_006`: stock is counted and valued by someone independent |
| `OBS_SECPKG_005` | "Consistent with the risk profile" names nothing to measure against | `OBS_SECPKG_006`: forced-sale value against the most that can be owed |
| `OBS_TS_003` | "Appropriate for the risk profile", likewise | `OBS_TS_007`, `OBS_TS_008`: timing of repayments, reliance on a refinancing |
| `OBS_OFFTAKER_003` | A customer rated single-B passed because its standing "is known" | `OBS_OFFTAKER_009`: a rating of B or below goes against the claim |
| `OBS_KYC_001` | Asked every company for a compliance officer | `OBS_KYC_009`: written rules against bribery, someone who answers for them, a way to report |
| `OBS_DEBT_003` | "Mostly short-term" is sound for seasonal stock | `OBS_DEBT_010`: short-term debt that finances fixed assets or losses |

**Asked in a better place: on the link, the asset, the contract or another indicator**

`OBS_SUPPORT_EVENTS_001` (on each support link). `OBS_KEY_CONTRACTS_001` (`OBS_CONT_002`, `OBS_CONT_005`). `OBS_ECON_002` (`OBS_BUILDOP_001`). `OBS_EGEN_006` (`OBS_FEAS_002`). `OBS_EREG_001` (`OBS_REG_002`). `OBS_SECPKG_002` (`OBS_SUPPORT_TOPOLOGY_001`). `OBS_SECPKG_003` (`OBS_SECASSET_006`, `OBS_SECPKG_007`). `OBS_TS_005` (`OBS_PROJ_006`). `OBS_COST_003` (`OBS_INPUT_001`). `OBS_COST_005` (`OBS_RP_002`). `OBS_OWN_001` (`OBS_BO_002`). `OBS_WC_004` (`OBS_CHG_003`). `OBS_LIT_005` (the checks on each authority: `OBS_REG_003`, `OBS_TAX_005`, `OBS_ENV_006`, `OBS_SOC_004`, `OBS_KYC_003`). `OBS_HEDGE_001`, `OBS_HEDGE_002` (`OBS_HEDGE_003`, `OBS_HEDGE_004`). `OBS_FIG_005` (`OBS_ACC_001`, `OBS_ACC_003`). `OBS_COMPSUPPORT_001` (the kind of link says it). `OBS_LIFECYCLE_CONFIRM_001` (`OBS_CAPEX_PLAN_001`). `OBS_TAX_001` (`OBS_TAX_004`). `OBS_DEBT_004` (`OBS_LENDER_001`). `OBS_DEBT_005` (`OBS_LENDER_006`). `OBS_DEBT_006` (`OBS_DS_005`).

**Questions whose answer nothing used**

`OBS_BOARD_002`, `OBS_AUTH_003`, `OBS_AUTH_005`, `OBS_LEGAL_005`, `OBS_LIQ_002`, `OBS_LIQ_005`, `OBS_ERES_004`, `OBS_ESG_MANDATE_002`, `OBS_REV_002`, `OBS_REV_006`, `OBS_TAX_002`, and `OBS_FX_TRANSLATION_001`, which moves reported equity and not cash.

**Repeated a neighbour**

`OBS_BO_003`, `OBS_OWN_002`, `OBS_LEGAL_004`, `OBS_INVESTOR_ROLE_004`.

### Answers that no longer fit

A deal that recorded answers under version 3 has to answer these again. The options changed:

- `OBS_SECTOR_001` (now the kind of credit), `OBS_SECTOR_002` (now eight sectors), `OBS_VALUE_CHAIN_001`, `OBS_LIFECYCLE_001`.
- `OBS_GUARANTEE_KIND_001`, `OBS_FX_003`, `OBS_INPUT_MIT_001`, `OBS_COV_001`, `OBS_COV_004`, `OBS_KYC_005`.
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
2. Eleven writers each rewrote one part against the framework and one common brief. A checker refused output that broke the format or the rules it can test. That was version 4.0.0, with 570 checks.
3. Every test and mitigant was judged blind: a judge saw the question and the assumption, not the answer the standard marks as going against it. No yes/no test and no test on a number had the wrong direction. Six tests on a choice differed on a middle option, and three were changed.
4. Two reviewers then read the whole standard, one for overlap between the parts and one as a credit practitioner. All but four of their 110 findings were applied. That is version 4.0.1. The 46 tests that were added or reworded were judged blind again by two judges, who agreed with the standard on every one.

Nobody who does credit work for a living has reviewed it yet.

### What the two reviews changed (4.0.1)

- **The financial core was thin.** New tests: leverage (`OBS_DS_005`, total debt above four times EBITDA), the lowest projected cover for a project or a new business (`OBS_DS_008`), a fall of the earning currency as deep as the worst of the last ten years (`OBS_FX_009`), short-term debt that finances fixed assets (`OBS_DEBT_010`), the auditor's standing (`OBS_ACC_010`), and revenue against tax returns and bank statements (`OBS_ACC_011`).
- **Some tests challenged almost every sound deal**, so that "challenged" said little. A share of revenue in foreign currency (`OBS_FX_002`), a largest input above 30 percent of cost (`OBS_INPUT_002`), a customer above a tenth of revenue (`OBS_BUYER_CONC_001`) and a board that never said no (`OBS_BOARD_007`) are now questions. The tests ask what matters instead: whether the margin held when the input price rose (`OBS_INPUT_010`), and whether the party could lose its largest customer for a year (`OBS_REV_008`). `OBS_LENDER_004`, `OBS_MARKET_004` and `OBS_TAX_005` were reworded for the same reason.
- **Agribusiness and customers.** Farm produce for added capacity (`OBS_AGRI_010`), collection and cooling on the way in (`OBS_AGRI_008`), and a large customer that cuts prices or lengthens payment terms without a contract (`OBS_OFFTAKER_010`).
- **Owners.** The owners' own cash in the plan (`OBS_USE_004`), an owner that needs the company's cash for its own debt (`OBS_GROUP_010`), the lender's right to leave when control changes (`OBS_COV_010`), and the party's place against its competitors (`OBS_MARKET_009`).
- **Banks.** The institution's record with its own lenders (`OBS_FIL_009`), loans in foreign currency to borrowers who do not earn it (`OBS_FIP_009`), and the screening of its own lending for environmental and social risk (`OBS_ES_006`).
- **Mitigants.** Business interruption insurance for a single plant (`OBS_OPS_MIT_002`), and a cash sweep where repayment depends on a refinancing (`OBS_TS_MIT_001`).
- **Overlap.** 47 checks went: 34 from version 3 and 13 that were new in 4.0.0. They are in the lists above.
- **Claims** of four indicators were rewritten to say what a lender relies on: projections, the board, political exposure, and the power tariff.

### For a credit reviewer

- **Reference points on a number.** `OBS_DS_003` and `OBS_DS_008` debt service cover below 1.2. `OBS_DS_005` total debt above 4 times EBITDA. `OBS_ACC_005` accounts older than 18 months. `OBS_FX_INPUT_001` imported inputs above 25 percent. `OBS_HEDGE_003` hedged share at most 50 percent. `OBS_INPUT_MIT_003` and `OBS_REC_SECURITY_001` below 50 percent. `OBS_REC_GOV_001` above 20 percent. `OBS_REV_004` revenue falling. `OBS_WC_005` overdue receivables above 10 percent. `OBS_RP_EXPOSURE_001` above 10 percent of equity. `OBS_RP_PEAK_001` above 1.5. `OBS_FIC_002` capital headroom below 2 points. `OBS_FIP_004` restructured loans above 5 percent. `OBS_SECPKG_006` cover below 100 percent. Each has its reason in `why`. An institution changes them in its own layer.
- **Tests that still go against the claim in many sound deals**, by design, so that the mitigant is asked: an unsecured loan (`OBS_COLLATERAL_001`), a refinancing (`OBS_USE_002`), more than about a tenth of the debt in a currency the party does not earn (`OBS_FX_008`), a price-taker (`OBS_MARKET_003`), a single plant (`OBS_OPS_003`), a subsidised tariff (`OBS_EREG_004`).
- **Sizes named in questions** ("about a tenth", "about a third", "three years") are guides and say so in their notes.
- **Words that carry a definition** in their note: `mixed` in `OBS_CASHFLOW_BASIS_001`, `blended` in `OBS_LIFECYCLE_CONFIRM_002`, the border between agribusiness and trade in `OBS_SECTOR_002`.
- **The four new checks with the most wording of their own**: `OBS_KYC_009`, `OBS_OFFTAKER_010`, `OBS_GROUP_010`, `OBS_ACC_010`.

### Known gaps

- **No module for funds or for real estate.** A fund gets the deal, the links and the facility, and nothing about its own repayment. `OBS_SECTOR_001` says so in its note.
- **The modules are uneven.** Power has four indicators, agribusiness one.
- **Banks.** The quality of capital and the use of the money by a bank that lends it on are not asked.
- **Projects.** Disbursement against an independent engineer's certificates is not asked.
- **Currency.** A rise of the local currency against foreign-currency revenue is not tested.
- **`lends_to` covers a loan received and a loan given.** The checks on another lender make no sense for a loan the party gave to an affiliate. The first check says so.
- **Kinds of source are missing** for a land title, a court search, an independent engineer's report, a certificate from a certification scheme and an impact report. The checks use the nearest kind.
- **A public body** does not fit every check on legal standing and authorisation. A person has had a kind of its own since 4.1.0.
- **A guarantee of existing debt has no record of its own.** It is a fact about that debt's `lends_to` link, so nothing examines the giver for it.

## Versions 3.0.0 and 3.0.1: the copy from the first Bankability

Version 3.0.0 was copied from version 2.0.0 in the `bankability` repository (`bankability-protocol/`) by a script, `docs/aissociate/convert_standard.py` in that repository. The script holds every table mentioned below. Version 3.0.1 corrected the copy after a review. Those corrections are marked.

### Repaired

1. **One list for evidence.** The checks named 160 kinds of evidence, and 24 of them existed in the list of 64 document types. There is now one list of 79 kinds of source: the 64 document types and 15 new ones, among them calls, notes by the analyst and internal memos. The other names were mapped onto that list.
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
