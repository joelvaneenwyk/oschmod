# -*- coding: utf-8 -*-
"""Command line interface (CLI) for the 'oschmod' library."""

from __future__ import absolute_import, division, print_function, unicode_literals, with_statement

import argparse

from . import set_mode, set_mode_recursive


def main():
    """Provide main function for CLI."""
    parser = argparse.ArgumentParser(
        description="Change the mode (permissions) of a file or directory"
    )
    parser.add_argument("-R", action="store_true", help="apply mode recursively")
    parser.add_argument("mode", nargs=1, help="octal or symbolic mode of the object")
    parser.add_argument("object", nargs=1, help="file or directory")

    args = parser.parse_args()
    mode = args.mode[0]
    obj = args.object[0]
    if args.R:
        set_mode_recursive(obj, mode)
    else:
        set_mode(obj, mode)
