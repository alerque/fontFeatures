"""
Class Definitions
=================

To define a named glyph class in the FEE language, use the ``DefineClass``
verb. This takes three arguments: the first is a class name, which must
start with the ``@`` character; the second is the symbol ``=``; the third
is a glyph selector as described above::

    DefineClass @upper_alts = @upper.alt;
    DefineClass @lower = /^[a-z]$/;
    DefineClass @upper_and_lower = [A B C D E F G @lower];

In addition, glyph classes can be *combined* within the ``DefineClass``
statement using intersection (``|``) and union (``&``) operators::

    DefineClass @all_marks = @lower_marks | @upper_marks;
    DefineClass @uppercase_vowels = @uppercase & @vowels;

Finally, glyph classes can be filtered through the use of one or more
*predicates*, which take the form ``and`` followed by a
bracketed relationship, and which tests the properties of the glyphs
against the expression given::

    DefineClass @short_behs = /^BE/ and (width < 200);

- The first part of the relationship is a metric, which can be one of

  - ``width`` (advance width)
  - ``lsb`` (left side bearing)
  - ``rsb`` (right side bearing)
  - ``xMin`` (minimum X coordinate)
  - ``xMax`` (maximum X coordinate)
  - ``yMin`` (minimum Y coordinate)
  - ``yMax`` (maximum Y coordinate)
  - ``rise`` (difference in Y coordinate between cursive entry and exit)

- The second part is a comparison operator (``>=``, ``<=``,
  ``=``, ``<``, or ``>``).

- The third is either an integer or a metric name and the name of a
  single glyph in brackets.

This last form is best understood by example. The following definition
selects all members of the glyph class ``@alpha`` whose advance width is
less than the advance width of the ``space`` glyph::

    DefineClass @shorter_than_space = @alpha and (width < width(space));


Binned Definitions
------------------

Sometimes it is useful to split up a large glyph class into a number of
smaller classes according to some metric, in order to treat them
differently. For example, when performing an i-matra substitution in
Devanagari, you would generally want to split your base glyphs by width,
and apply the appropriate matra for each set of glyphs. FEE calls the
operation of organising glyphs into groups of similar metrics "binning".

The ``ClassDefinition`` plugin also provides the ``DefineClassBinned`` verb,
which generated a set of related glyph classes. The arguments of ``DefineClassBinned``
are identical to that of ``DefineClass``, except that after the class name
you must specify an open square bracket, the metric to be used to bin the
glyphs, a comma, the number of bins to create, and a close bracket, like so::

    DefineClassBinned @bases[width,5] = @bases;

This will create five classes, called ``@bases_width1`` .. ``@bases_width2``,
grouped in increasing order of advance width. Note that the size of the bins is
not guaranteed to be equal, but glyphs are clustered according to the similarity
of their metric. For example, if the advance widths are 99, 100, 110, 120,
500, and 510 and two bins are created, four glyphs will be in one bin and two
will be in the second.

Glyph Class Debugging
---------------------

The combination of the above rules allows for extreme flexibility in creating
glyph classes, to the extent that it may become difficult to understand the
final composition of glyph classes! To alleviate this, the verb ``ShowClass``
will take any glyph selector and display its contents on standard error.

"""

import re
from glyphtools import get_glyph_metrics
import warnings


GRAMMAR = """
predicate = ws 'and' ws '(' ws <letter+>:metric ws ('>='|'<='|'='|'<'|'>'):comparator ws (<digit+>|bracketed_metric):value ws ')' -> {'predicate': metric, 'comparator': comparator, 'value': value}
bracketed_metric = <letter+>:metric '(' <(letter|digit|"."|"_")+>:glyph ')' -> {'metric': metric, 'glyph': glyph}
andconjunction = glyphselector:l ws '&' ws primary:r -> {'conjunction': 'and', 'left': l, 'right': r}
orconjunction = glyphselector:l2 ws '|' ws primary:r2 -> {'conjunction': 'or', 'left': l2, 'right': r2}
primary_paren = '(' ws primary:p ws ')' -> p
primary =  primary_paren | orconjunction | andconjunction | glyphselector

DefineClass_Args = classname:c ws '=' ws definition:d -> (c,d)
definition = primary:g predicate*:p -> (g,p)

DefineClassBinned_Args = classname:c '[' <letter+>:metric ws "," ws <digit+>:bincount ']' ws '=' ws definition:d -> (metric, bincount, c,d)

ShowClass_Args = glyphselector:g -> (g,)
"""

VERBS = ["DefineClass", "ShowClass", "DefineClassBinned"]

class DefineClass:
    @classmethod
    def action(self, parser, classname, definition):
        glyphs = self.resolve_definition(parser, definition[0])
        predicates = definition[1]
        for p in predicates:
            glyphs = list(filter(lambda x: self.meets_predicate(x, p, parser), glyphs))
        parser.fontfeatures.namedClasses[classname["classname"]] = tuple(glyphs)

    @classmethod
    def resolve_definition(self, parser, primary):
        if isinstance(primary, dict) and "conjunction" in primary:
            left = set(self.resolve_definition(parser, primary["left"]))
            right = set(self.resolve_definition(parser, primary["right"]))
            if primary["conjunction"] == "or":
                return list(left | right)
            else:
                return list(left & right)
        else:
            return primary.resolve(parser.fontfeatures, parser.font)

    @classmethod
    def meets_predicate(self, glyphname, predicate, parser):
        metric = predicate["predicate"]
        comp = predicate["comparator"]
        if isinstance(predicate["value"], dict):
            v = predicate["value"]
            testvalue_metrics = get_glyph_metrics(parser.font, v["glyph"])
            if v["metric"] not in testvalue_metrics:
                raise ValueError("Unknown metric '%s'" % metric)
            testvalue = testvalue_metrics[v["metric"]]
        else:
            testvalue = int(predicate["value"])

        metrics = get_glyph_metrics(parser.font, glyphname)
        if metric not in metrics:
            raise ValueError("Unknown metric '%s'" % metric)
        value = metrics[metric]
        if comp == ">":
            return value > testvalue
        elif comp == "<":
            return value < testvalue
        elif comp == ">=":
            return value >= testvalue
        elif comp == "<=":
            return value <= testvalue
        raise ValueError("Bad comparator (can't happen?)")


class DefineClassBinned(DefineClass):
    @classmethod
    def action(self, parser, metric, bincount, classname, definition):
        from glyphtools import bin_glyphs_by_metric
        glyphs = self.resolve_definition(parser, definition[0])
        predicates = definition[1]
        for p in predicates:
            glyphs = list(filter(lambda x: self.meets_predicate(x, p, parser), glyphs))

        binned = bin_glyphs_by_metric(parser.font, glyphs, metric, bincount=int(bincount))
        for i in range(1, int(bincount) + 1):
            parser.fontfeatures.namedClasses["%s_%s%i" % (classname["classname"], metric, i)] = tuple(binned[i - 1][0])


class ShowClass:
    @classmethod
    def action(self, parser, classname):
        warnings.warn(
            "%s = %s"
            % (
                classname.as_text(),
                " ".join(classname.resolve(parser.fontfeatures, parser.font)),
            )
        )
        return []
