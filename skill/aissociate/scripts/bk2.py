"""Run the tool from the skill's folder: python3 scripts/bk2.py <command> <deal folder>"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bankability2.__main__ import main  # noqa: E402

sys.exit(main())
