#!env python
import sys
from fontTools.ttLib import TTFont
from fontFeatures.ttLib import unparse
from fontFeatures.optimizer import Optimizer
from argparse import ArgumentParser

import logging
import os

LOGLEVEL = os.environ.get("LOGLEVEL", "WARNING").upper()
logging.basicConfig(level=LOGLEVEL)

import warnings


def warning_on_one_line(message, category, filename, lineno, file=None, line=None):
    return "# [warning] %s\n" % (message)


warnings.formatwarning = warning_on_one_line

parser = ArgumentParser()
parser.add_argument("input", help="font file to process", metavar="FILE")
parser.add_argument(
    "--gdef",
    dest="gdef",
    action="store_true",
    help="Also output GDEF table information",
)
parser.add_argument(
    "--no-lookups",
    dest="nolookups",
    action="store_true",
    help="Just list languages and features, don't unparse lookups",
)
parser.add_argument(
    "--config", default=None, help="config file to process", metavar="CONFIG"
)
parser.add_argument(
    "-O", "--optimize", dest="optimize", type=int, default=1, help="Run optimizer"
)

args = parser.parse_args()

config = {}
if args.config:
    import json

    with open(args.config) as f:
        config = json.load(f)

font = TTFont(args.input)
ff = unparse(font, do_gdef=args.gdef, doLookups=(not args.nolookups), config=config)
if args.optimize:
    Optimizer(ff).optimize(level=args.optimize)
print(ff.asFea())
