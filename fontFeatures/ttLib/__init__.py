from fontTools.misc.py23 import *
import fontTools
from fontTools.feaLib.ast import *
from collections import OrderedDict

from .GDEFUnparser import GDEFUnparser
from .GSUBUnparser import GSUBUnparser
from .GPOSUnparser import GPOSUnparser
from fontFeatures import FontFeatures


def unparseLanguageSystems(tables):
    scripts = OrderedDict()
    for table in tables:
        for scriptRecord in table.table.ScriptList.ScriptRecord:
            scriptTag = scriptRecord.ScriptTag
            languages = scripts.get(scriptTag, [])
            script = scriptRecord.Script
            items = []
            if script.DefaultLangSys is not None:
                items.append(("dflt", script.DefaultLangSys))
            items += [(l.LangSysTag, l.LangSys) for l in script.LangSysRecord]
            languages = set([i[0] for i in items])

            if languages and not scriptTag in scripts:
                scripts[scriptTag] = languages

    return scripts


def unparse(font, do_gdef=False, doLookups=True, config={}):
    gsub_gpos = [font[tableTag] for tableTag in ("GSUB", "GPOS") if tableTag in font]
    ff = FontFeatures()

    languageSystems = unparseLanguageSystems(gsub_gpos)

    # if 'GDEF' in font and do_gdef:
    #     table = GDEFUnparser(font["GDEF"]).unparse()
    #     if table:
    #         ff.statements.append(table)

    if "GSUB" in font:
        GSUBUnparser(
            font["GSUB"], ff, languageSystems, font=font, config=config
        ).unparse(doLookups=doLookups)

    if "GPOS" in font:
        GPOSUnparser(
            font["GPOS"], ff, languageSystems, font=font, config=config
        ).unparse(doLookups=doLookups)
    return ff
