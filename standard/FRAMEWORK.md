# The framework

How the Bankability DDQ, which the files call the standard, is organised, and why. The lists and the checks are in the other files. This page is the thinking behind them.

## 1. Start from repayment

A loan is repaid from somewhere. The framework starts there.

1. **The structure.** Who and what is in the deal, and how they are linked: companies, people, groups, the loan under review, assets, projects and contracts. It is discovered, never assumed, and it can change at any time.
2. **The reliance.** What repayment relies on, in order: the first way out and the second. Each points at something in the structure: a party's cash flow, a guarantor's promise, an asset's value, a customer's payments.
3. **The claims.** About each thing relied on, the lender makes claims: "this company can service the loan from its own cash flow", "this guarantor can and must pay if the borrower does not". Each claim has checks that try to disprove it.

Nothing is tied to the word "borrower". There can be several, they can change, and repayment may in truth rest on a parent, a group or a customer. The analysis follows the reliance, wherever it points.

## 2. Four layers, kept apart

Rating agencies build a credit view in layers and do not blend them. The standard does the same. Every indicator belongs to one layer.

| Layer | The question | Asked about |
|---|---|---|
| **The deal** | What is asked for, how is it repaid, who is in it, what kind of business is it? | The deal, once |
| **Each party on its own** | Is this party sound by itself? | The business and its money, once. The owners, the integrity, the board and the standing of each company |
| **The links** | What does each link add or take away? | Every link that bears on repayment |
| **The facility** | Is this loan well placed if things go wrong? | The loan under review, each asset that secures it, and each party that signs |

A weak layer is not averaged away by a strong one. A sound company with a guarantee that cannot be enforced has a sound first way out and no second.

## 3. The loan, the perimeter and the entity

Three distinctions keep each check where it belongs.

- **The loan under review.** A facility in the structure is a loan that the lender is considering. The roles that belong to that loan, borrower and guarantor, and the checks on a guarantee or on security, arise only from links that point at it. Debt that already exists is not a facility. It is a link from its lender to the company that owes it, and its terms, its security and its guarantors are facts about that link. An owner who guarantees an old bank loan is therefore not a guarantor of this one.
- **The perimeter.** The business and its money are examined once, on the perimeter whose cash repays the loan. Often that is a consolidated group. The companies inside it are examined as legal entities: their owners, their integrity, their boards, their standing. The tie between them is examined for one thing: whether the cash can reach the lender. So a company inside the group is not asked again what the group is asked, and a group is never asked what only a legal entity can answer.
- **A person is not a company.** A natural person is a kind of subject of its own, and is asked only what fits a person: sanctions, political exposure, integrity, where the money comes from, disputes, and the capacity to pay what the person has guaranteed.

## 4. The analysis follows reliance

| What repayment relies on | How it shows in the structure | What is examined |
|---|---|---|
| A party's cash flow | It `borrows`, or the facility `relies_on` it | The full view of the party on its own: all six pillars below |
| A promise to pay the loan under review | `guarantees`, `supports` | The promise itself, the giver's capacity to honour it, and whether the giver would fail for the same reason as the borrower |
| An owner or a group | `owns`, `sponsors`, `controls`, `member_of` | Who they are, whether support would come down, and whether cash can be taken up |
| A customer, a supplier, a builder, an operator | `sells_to`, `supplies_to`, `builds`, `operates` | How much depends on them, whether they can be replaced, what the contract gives |
| Another lender, and the debt already owed to it | `lends_to` | Who ranks ahead, what they hold, and what lets them call their loan |
| An asset | `secures` | Whose it is, what it is worth in distress, whether the security holds |
| What the loan pays for | `finances` | Whether the project or the asset can be built or bought, and run, as planned |

A guarantor is therefore not asked how it runs a factory. It is asked whether it can pay, whether it must, and whether its own money comes from the borrower. If repayment in truth rests on the guarantor, the facility `relies_on` it, and it gets the full view.

Checks on a project follow the financing. They are asked of the project that the loan pays for. Other projects of the business are described, and are not checked.

When a party changes role, nothing is lost and nothing is rewritten. The facts stay with the party they are about. The checks follow the role to whoever holds it now.

## 5. Nine pillars

The order is the order of a credit analysis: the deal, then each party from its surroundings inward to its money, then the links, then the loan.

| | Pillar | Layer | What it examines |
|---|---|---|---|
| 0 | The deal | Deal | The request, the two ways out, who is in the deal, the kind of business |
| 1 | Environment | Party | Country, sector and market, licences and regulation |
| 2 | Business | Party | Customers, inputs, operations and assets |
| 3 | People and governance | Party | Owners and control, integrity, board and controls, management |
| 4 | Cash flow and debt | Party | The accounts, profitability, cash flow against debt service, existing debt |
| 5 | Liquidity and financial risks | Party | Liquidity and working capital, currency, interest rate and price risk |
| 6 | Environmental, social and impact | Party and deal | E&S risk and its management, land and supply chain, impact and additionality |
| 7 | Links | Link | Guarantee, group, key customer, key supplier, builder and operator, other lenders |
| 8 | The facility | Facility | Terms, covenants, security, legal standing, conditions |

Pillars 1, 2, 4, 5 and 6 are asked of the perimeter. Pillar 3 is asked of each legal entity. Pillar 7 is asked of each link. Its two indicators that are asked of a party, related parties and a guarantor's capacity, follow the perimeter.

Pillars carry the weight, not the number of checks. A pillar with thirty checks does not count for more than one with ten.

Some indicators belong to one kind of business: banks, power projects, agribusiness. They sit in the pillar they belong to and apply only when discovery says so. A bank has its own cash-flow pillar (capital, loan quality, funding). The framework around it stays the same.

## 6. One claim per indicator

An indicator is one claim: **what the lender relies on**, in one sentence that can turn out false. "Management is strong" forbids nothing and is not a claim. "No single customer's loss would stop the company from servicing its debt" is one.

Because every claim says what the lender relies on, a claim that is disproved is always bad news.

There are 70 claims. People and assistants work from them. The checks are the detail behind a claim.

A check has one of three jobs:

- **A question** opens the topic or describes it. It tests nothing. "What is the total debt outstanding?"
- **A test** can disprove the claim. It states its own assumption and which answer disproves it, or a reference point with a reason.
- **A mitigant** is asked once a test has gone against the claim. It asks what limits the damage.

From the answers AIssociate's tool works out where each claim stands, for each party or link it is asked about:

| The claim | Means |
|---|---|
| is **not tested** | No test is answered, or the answers rest only on someone's own word |
| **stands so far** | Some tests are answered and none goes against it. Work is left: a test is open or waits for an earlier answer, or an answer rests on someone's own word or on evidence that is thin or old for the stage. The tool says how many |
| **stands** | Every test is answered and none goes against it, and no answer is left to strengthen. The tool says on what evidence |
| is **challenged** | A test went against it. The tool says which, and whether a mitigant is known, holds or fails |
| is **contested** | Two facts answer the same test, or a question behind the claim, differently |

No topic closes on one answer. A company with no foreign-currency revenue can still be exposed through its costs, its debt or its suppliers. Each independent way a risk can enter is tested before the claim is left alone.

A test asks about what matters for repayment. Where the thing exists but is too small to matter, the answer is the favourable one, and the fact says how small. A currency test that fails on one small foreign loan tells the reader nothing.

There are no scores and no weights. What matters is stated with its reason.

## 7. Discovery

Discovery is the first pillar and it never quite ends.

- **It opens what applies.** The first question is what kind of credit this is: an operating business, a single project, a financial institution or a fund. The answer decides which view of a party applies. The sector then switches on what belongs to it, such as the checks for a power project or an agribusiness. Until discovery has answered, those checks wait. If one party is of another kind than the rest of the deal, the answer is recorded for that party alone.
- **It calls for structure.** Some answers mean that a party or a link must exist. "One customer buys a large share of revenue" calls for that customer and a `sells_to` link. If the structure lacks it, the tool says so. The link then brings its own checks. Where the analyst decides that nothing needs to be added, that decision is recorded with its reason, and the tool stops asking.
- **It is provisional.** A discovery answer that rests on what someone said is marked until a document confirms it. A few checks exist only to cross-check an earlier answer.
- **It walks the chain.** Each owner that is found is asked the same questions about its own owners, up to natural persons.
- **It asks for description.** A few open questions ask how the business earns its money, what is particular about it compared with others of its kind, and what the project is. They test nothing. Understanding starts from their answers.
- **It asks what usually goes wrong.** Each deal starts with the question how businesses of this kind, in this place, usually fail. The answer says where to look first.

An unexplained change in the numbers is a discovery too. A margin that falls by a fifth needs a cause, and the cause points at a topic.

## 8. Evidence

Who says something matters as much as what is said.

- **An admission stands on the speaker's word.** A company that says it breached a covenant is believed.
- **A favourable statement does not.** A company that says its hedging is adequate, or a parent that says it will support, has said nothing yet. The claim stands only once something independent supports it. Until then the answer is marked as the party's own word.
- **Thin evidence can open a question. It cannot close one.**
- **Strength grows with the stage.** What the client says is fine at a first screening. By approval it should be the best kind of document. Each check says which kinds of source count as best, as supporting, and as only stated.
- **The original is the source.** A text extract made from a document is a working aid that is kept with it. A fact cites the place in the original.
- **A search that found nothing is recorded**, with what was searched, where and when. It is different from not having looked.
- **Figures at their worst, not at year-end.** Debt at its seasonal peak, profit in cash and not in fair-value gains, margins over a whole price cycle.

## 9. Stages are targets, and they balance the standard

Stages say when an answer is ideally there. Nothing waits for a stage.

| Stage | What is ideally known |
|---|---|
| Screening | Whether this can be a deal: the request, the two ways out, the structure, the kind of business, and the fatal flaws (exclusion list, sanctions, country) |
| Concept note | The claims that carry the deal, each tested at least once |
| Due diligence | The tests verified on the best evidence, the figures, the mitigants |
| Approval and after | What remains is turned into conditions and agreed actions, and then followed |

A check that is not yet due is not a gap.

A test is answered as soon as it is decided, whatever the terms of the loan turn out to be. Debt that is above the reference point before the new loan has already decided the test on leverage.

A check can end in a third way besides answered and open: **a gap with an agreed action**, an owner and a date. That is how an action plan, a condition or a covenant is recorded. An open check with an agreed action is acceptable at approval. And in a fourth: **settled for one subject** by a decision that gives the reason and names no owner and no date. The check is then off for that subject and still asked of the others.

## 10. Change

- **A claim is looked at again** when something it rests on changes: a new document of a kind that bears on it, a new answer elsewhere, or simply age.
- **A new party in a role starts untested.** Its predecessor's facts stay with the predecessor.
- **Across several parties, a claim stands where its weakest party stands.** A mitigant at one party does not cover another.

## 11. What the framework is not

- **Not a script.** The standard is a backbone. It says where to look, and it keeps the record honest. It does not replace the analysis. A capable analyst or assistant follows the deal, not the list.
- **Not a checklist to complete.** An open check that does not matter for this deal is not a gap, and nothing is gained by answering it.
- **Not the understanding.** The standard gives rigour: claims, tests and evidence. Understanding is written beside it, in the wiki of the deal: what the business is, what is particular about it, and how its context shows in its figures.
- **Not a rating and not a decision.** It says where each claim stands and on what. The judgement stays with people.

## 12. Where this comes from

- **The first Bankability**: falsification as the backbone, a risk and its mitigant per topic with a plain verdict, discovery that shapes what is asked, trust that depends on who speaks, reopening, and subjects in a graph instead of names in text. Its weights and scores are gone. Their reasons are kept.
- **Rating agencies** (Fitch, Moody's, S&P): the layers, the pillars of a party's own credit, weak points that cap instead of being averaged, and the way a link is tested: obligation, ability and incentive, in both directions.
- **Development finance practice**: stage as the balancing device, checks that attach to roles and links, the action plan as a third state, and the topics a commercial bank does not ask.
- **Analytic method**: a claim must forbid something; evidence that fits every explanation proves nothing; a statement against interest is strong and a statement in one's own favour is weak.

The alignment with the agencies is one of structure. The standard produces no rating.
