# Validation

The [real-deal pilot](pilot-acceptance.md) is the acceptance test. [Results](results.md) distinguish actual Word checks, local tool behaviour and tenant outcomes. Keep all real documents and detailed run records in their approved environment.

Local tests cover file integrity, persistence and extracted-package operation. Run `uv run pytest -q` and build both ZIPs. Those checks do not prove the assistant writes a good FP.

The older synthetic scenarios in this folder are optional diagnostic material, not a product target or substitute for the complete workflow. Use them only when they help reproduce an observed problem.
