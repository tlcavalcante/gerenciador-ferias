#!/usr/bin/env python3
"""Ponto de entrada portátil do Gerenciador de Férias."""

import sys
sys.dont_write_bytecode = True

from app import main


if __name__ == "__main__":
    raise SystemExit(main())
