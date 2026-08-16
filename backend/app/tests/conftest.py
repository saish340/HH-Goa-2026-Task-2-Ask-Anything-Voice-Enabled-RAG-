"""Shared pytest fixtures — force demo mode so tests never load the big index."""

import os

os.environ.setdefault("AA_DEMO", "1")