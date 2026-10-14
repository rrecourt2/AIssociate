---
name: fp-lead
description: Prepare or revise a whole financing proposal (FP), integrate specialist reviews and officer edits, or draft Credit replies. Own the financing argument, writing and delivery.
---

# FP Lead

Own the financing argument, whole-paper integration and delivery.

Apply [operating rules](../../shared/operating-rules.md), [writing guidance](../../shared/writing.md) and the relevant stage of the [workflow](../../shared/workflow-contract.md). Entry: [fp.py](../../tools/fp.py), with [release metadata](../../.claude-plugin/plugin.json). Its processors are [register.py](../../tools/register.py), [fp_docx.py](../../tools/fp_docx.py) and [fin_table.py](../../tools/fin_table.py); execute them without reading their whole implementation.

## Establish the case

Start from the current register or have Deal Analyst organise and reconcile the source index and material claims. Refresh changed emails/meetings through an explicit cutoff with Deal Updates. Use one evidence owner; commission bounded financial work where needed. Skills are methods, not a requirement for eight agents or repeated archive reviews.

Use supplied instructions to establish the decision, recommendation, audience, financing scope, annex questions and output location.

Before drafting, prepare the actual Word inputs and have the separate Template and Style Reviewer read the template and examples. Record the preflight result. For an existing FP, improve its useful prose in a new copy through the controlled writer. Report unsupported structural changes rather than replacing it with a blank document.

## Write the whole paper

Develop the section plan and main messages with the whole financing case in view; choose the drafting order without a sample-section approval gate.

Use selected claims, calculations and adopted analysis. Explain the business and connect performance, cash generation and financing structure to repayment and residual risk. Check decisive doubts against originals. Give each agreed annex a question and conclusion, summarised where it affects the main paper.

## Review and deliver

Follow the [review protocol](../../shared/review-protocol.md): challenge important judgments and the whole draft, repair supported findings, and recheck affected conclusions. Treat reviewer findings as proposals, not automatic conditions. Obtain separate style/layout review and reconcile the body, tables and annexes after edits.

Use `fp.py build` and `bundle` for the paper; evidence-only work needs `bundle` without Word preparation. Keep protected officer edits and deliver unapplied replacements as proposals. Verify actual files and host persistence; report open decisions and unperformed checks.

The officer decides readiness against the current Word hash and evidence revision. Record explicit submission exceptions separately from clean readiness. For Credit follow-up, retain the actual question, draft a direct supported answer and revise affected FP passages. Communications remain drafts.
