"""TaxPilot - autonomous tax-prep and compliance copilot.

The whole design turns on one split: the LLM reads messy documents, retrieves and
explains rules, and spots anomalies; a deterministic Python engine does every
piece of arithmetic and cites the authority behind each figure. Nothing the model
"says" ever becomes a number on the return.
"""

__version__ = "0.1.0"
