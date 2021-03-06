#!env python3
from fontFeatures.feeLib import FeeParser
from fontFeatures.ttLib import unparse
from fontTools.ttLib import TTFont
import sys
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString

from argparse import ArgumentParser, FileType

parser = ArgumentParser()
parser.add_argument("input", help="font file to process", metavar="OTF")
parser.add_argument(
    "feature",
    default="-",
    nargs="?",
    help="FEE file(s) to add",
    metavar="FEE",
)
parser.add_argument("-o", dest="output", help="path to output font", metavar="FILE")
args = parser.parse_args()

output = args.output
if output is None:
    output = "fea-" + args.input

font = TTFont(args.input)
p = FeeParser(args.input)
# Unparse existing features
p.fea = unparse(font)
# Add features from FEE
p.parseFile(args.feature)

# Send it back to fea
fea = p.fea.asFea()
addOpenTypeFeaturesFromString(font, fea)
print("Saving on " + output)
font.save(output)
