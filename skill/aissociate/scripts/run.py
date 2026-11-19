"""Run the tool from the skill's folder: python3 scripts/run.py <command> <deal folder>"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # the package sits beside this file, in scripts/aissociate

from aissociate.__main__ import main  # noqa: E402

sys.exit(main())
