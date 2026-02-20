#!/usr/bin/env python
from __future__ import annotations

import os
import sys

import pytest


def main() -> int:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")
    args = sys.argv[1:] or ["tests"]
    return pytest.main(args)


if __name__ == "__main__":
    raise SystemExit(main())
