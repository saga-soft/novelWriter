#!/usr/bin/env python3
"""
novelWriter - Start Script
==========================
"""  # noqa

import os
import sys

os.curdir = os.path.abspath(os.path.dirname(__file__))

if __name__ == "__main__":
    import novelwriter

    novelwriter.main(sys.argv[1:])
