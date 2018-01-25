#-*- coding: utf-8 -*-

#+---------------------------------------------------------------------------+
#|          01001110 01100101 01110100 01111010 01101111 01100010            |
#|                                                                           |
#|               Netzob : Inferring communication protocols                  |
#+---------------------------------------------------------------------------+
#| Copyright (C) 2011-2017 Georges Bossert and Frédéric Guihéry              |
#| This program is free software: you can redistribute it and/or modify      |
#| it under the terms of the GNU General Public License as published by      |
#| the Free Software Foundation, either version 3 of the License, or         |
#| (at your option) any later version.                                       |
#|                                                                           |
#| This program is distributed in the hope that it will be useful,           |
#| but WITHOUT ANY WARRANTY; without even the implied warranty of            |
#| MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the              |
#| GNU General Public License for more details.                              |
#|                                                                           |
#| You should have received a copy of the GNU General Public License         |
#| along with this program. If not, see <http://www.gnu.org/licenses/>.      |
#+---------------------------------------------------------------------------+
#| @url      : http://www.netzob.org                                         |
#| @contact  : contact@netzob.org                                            |
#| @sponsors : Amossys, http://www.amossys.fr                                |
#|             Supélec, http://www.rennes.supelec.fr/ren/rd/cidre/           |
#+---------------------------------------------------------------------------+

#+---------------------------------------------------------------------------+
#| File contributors :                                                       |
#|       - Georges Bossert <georges.bossert (a) supelec.fr>                  |
#|       - Frédéric Guihéry <frederic.guihery (a) amossys.fr>                |
#+---------------------------------------------------------------------------+

#+---------------------------------------------------------------------------+
#| Standard library imports                                                  |
#+---------------------------------------------------------------------------+
import random
from typing import Callable, List

#+---------------------------------------------------------------------------+
#| Related third party imports                                               |
#+---------------------------------------------------------------------------+

#+---------------------------------------------------------------------------+
#| Local application imports                                                 |
#+---------------------------------------------------------------------------+
from netzob.Common.Utils.Decorators import typeCheck, NetzobLogger
from netzob.Model.Vocabulary.Domain.Variables.AbstractVariable import AbstractVariable
from netzob.Model.Vocabulary.Domain.Variables.Nodes.AbstractVariableNode import AbstractVariableNode
from netzob.Model.Vocabulary.Domain.GenericPath import GenericPath
from netzob.Model.Vocabulary.Domain.Parser.ParsingPath import ParsingPath, ParsingException
from netzob.Model.Vocabulary.Domain.Specializer.SpecializingPath import SpecializingPath


altCbkType = Callable[[GenericPath, List[AbstractVariable]], AbstractVariable]


@NetzobLogger
class Alt(AbstractVariableNode):
    """The Alt class is a node variable that represents an alternative of variables.

    A definition domain can take the form of a combination of
    permitted values/types/domains. This combination is represented by
    an alternate node. It can be seen as an OR operator between two or
    more children nodes.

    The Alt constructor expects some parameters:

    :param children: The set of variable elements permitted in the
                     alternative. The default is None.
    :param callback: The callback function should return an integer used to
                     determine the child index to select. The default is None.
    :type children: a :class:`list` of :class:`Variable <netzob.Model.Vocabulary.Domain.Variables.AbstractVariable>`, optional
    :type callback: callable function taking two positional arguments returning
                    an integer, optional

    The Alt class provides the following public variables:

    :var children: The sorted typed list of children attached to the variable node.
    :var varType: The type of the variable (Read-only).
    :vartype children: a list of :class:`Variable <netzob.Model.Vocabulary.Variables.Variable>`
    :vartype varType: :class:`str`


    **Callback prototype**

    A callback function can be used to determine the child index to select.
    The callback function has the following prototype:

    .. function:: callback(path, children)
       :noindex:

       :param path: data structure that allows access to the values of the
                    :class:`Variable <netzob.Model.Vocabulary.Domain.Variables.AbstractVariable.AbstractVariable>`
                    elements.
       :type path: object, required
       :param children: children of the
                        :class:`~netzob.Model.Vocabulary.Domain.Variables.Nodes.Alt.Alt`
                        variable.
       :type children: ~typing.List[~netzob.Model.Vocabulary.Domain.Variables.Nodes.Alt.Alt], required

    Access to :class:`Variable <netzob.Model.Vocabulary.Domain.Variables.AbstractVariable.AbstractVariable>`
    values is done through the ``path``, thanks to its methods
    :meth:`~netzob.Model.Vocabulary.Domain.GenericPath.hasData` and
    :meth:`~netzob.Model.Vocabulary.Domain.GenericPath.getData`:

    * ``path.hasData(child)`` will return a :class:`bool` telling if a data has
      been specialized or parsed for the child
      :class:`Variable <netzob.Model.Vocabulary.Domain.Variables.AbstractVariable.AbstractVariable>`.
    * ``path.getData(child)`` will return a :class:`bitarray` that corresponds
      to the value specialized or parsed for the child
      :class:`Variable <netzob.Model.Vocabulary.Domain.Variables.AbstractVariable.AbstractVariable>`.


    The following code denotes an alternate object that
    accepts either the string "filename1.txt" or the string
    "filename2.txt":

    >>> from netzob.all import *
    >>> t1 = String("filename1.txt")
    >>> t2 = String("filename2.txt")
    >>> domain = Alt([t1, t2])


    **Examples of Alt internal attribute access**

    >>> from netzob.all import *
    >>> domain = Alt([Raw(), String()])
    >>> domain.varType
    'Alt'
    >>> print(domain.children[0].dataType)
    Raw(nbBytes=(0,8192))
    >>> print(domain.children[1].dataType)
    String(nbChars=(0,8192))


    **Example of a deterministic Alt computation**

    >>> def cbk(path, children):
    ...    return -1
    >>> f = Field(Alt([String(_) for _ in "abc"], callback=cbk), "alt")
    >>> sym = Symbol([f])
    >>> data = sym.specialize()
    >>> print(data)
    b'c'
    >>> Symbol.abstract(data, [sym])
    (Symbol, OrderedDict([('alt', b'c')]))


    .. ifconfig:: scope in ('netzob')

       **Abstraction of alternate variables**

       This example shows the abstraction process of an Alternate
       variable:

       >>> from netzob.all import *
       >>> v0 = String("john")
       >>> v1 = String("kurt")
       >>> f0 = Field(Alt([v0, v1]), name='f0')
       >>> s = Symbol([f0])
       >>> data = "john"
       >>> Symbol.abstract(data, [s])
       (Symbol, OrderedDict([('f0', b'john')]))
       >>> data = "kurt"
       >>> Symbol.abstract(data, [s])
       (Symbol, OrderedDict([('f0', b'kurt')]))

       In the following example, an Alternate variable is defined. A
       message that does not correspond to the expected model is then
       parsed, thus the returned symbol is unknown:

       >>> data = "nothing"
       >>> Symbol.abstract(data, [s])
       (Unknown message 'nothing', OrderedDict())

    """

    def __init__(self, children=None, callback=None):
        super(Alt, self).__init__(self.__class__.__name__, children)
        self.callback = callback  # type: altCbkType

    @typeCheck(ParsingPath)
    def parse(self, parsingPath, carnivorous=False):
        """Parse the content with the definition domain of the alternate."""

        if parsingPath is None:
            raise Exception("ParsingPath cannot be None")

        if len(self.children) == 0:
            raise Exception("Cannot parse data if ALT has no children")

        dataToParse = parsingPath.getData(self)
        self._logger.debug("Parse '{}' with '{}'".format(dataToParse.tobytes(), self))

        parserPaths = [parsingPath]
        parsingPath.assignData(dataToParse.copy(), self.children[0])

        # create a path for each child
        if len(self.children) > 1:
            for child in self.children[1:]:
                newParsingPath = parsingPath.duplicate()
                newParsingPath.assignData(dataToParse.copy(), child)
                parserPaths.append(newParsingPath)

        # parse each child according to its definition
        for i_child, child in enumerate(self.children):
            parsingPath = parserPaths[i_child]
            self._logger.debug("Start Alt parsing of {0}/{1} with {2}".format(i_child + 1, len(self.children), parsingPath))

            try:
                childParsingPaths = child.parse(parsingPath)
            except ParsingException:
                self._logger.debug("Error in parsing of child")
            else:
                for childParsingPath in childParsingPaths:
                    data_parsed = childParsingPath.getData(child)
                    self._logger.debug("End of Alt parsing of {}/{} with {}. Data parsed: '{}'".format(i_child + 1, len(self.children), parsingPath, data_parsed))
                    childParsingPath.addResult(self, data_parsed)
                    yield childParsingPath
        self._logger.debug("End of parsing of Alt variable")

    @typeCheck(SpecializingPath)
    def specialize(self, specializingPath, fuzz=None):
        """Specializes an Alt"""

        from netzob.Fuzzing.Fuzz import MaxFuzzingException

        if specializingPath is None:
            raise Exception("SpecializingPath cannot be None")

        if len(self.children) == 0:
            raise Exception("Cannot specialize ALT if its has no children")

        specializingPaths = []

        # If we are in a fuzzing mode
        if fuzz is not None and fuzz.get(self) is not None:

            # Retrieve the mutator
            mutator = fuzz.get(self)

            try:
                # Chose the child according to the integer returned by the mutator
                generated_value = mutator.generate()
            except MaxFuzzingException:
                self._logger.debug("Maximum mutation counter reached")
                return

            if 0 <= generated_value < len(self.children):
                child = self.children[generated_value]
            else:
                raise ValueError("Field position '{}' is bigger than the length of available children '{}'"
                                 .format(generated_value, len(self.children)))

        elif callable(self.callback):
            i_child = self.callback(specializingPath, self.children)
            if not isinstance(i_child, int):
                raise Exception("The Alt callback return value must be the index"
                                " (int) of the child to select, not '{}'"
                                .format(i_child))
            child = self.children[i_child]
        # Else, randomly chose the child
        else:
            child = random.choice(self.children)

        newSpecializingPath = specializingPath.duplicate()

        for childSpecializingPath in child.specialize(newSpecializingPath, fuzz=fuzz):
            value = childSpecializingPath.getData(child)
            self._logger.debug("Generated value for {}: {} ({})".format(self, value, id(self)))
            childSpecializingPath.addResult(self, value)

            yield childSpecializingPath

def _test(self):
    r"""

    >>> from netzob.all import *
    >>> Conf.seed = 0
    >>> Conf.apply()

    Here is an example with an Alt variable:

    >>> from netzob.all import *
    >>> m1 = RawMessage("220044")
    >>> f1 = Field("22", name="f1")
    >>> f2 = Field(Alt(["00", "0044", "0", "004"]), name="f2")
    >>> s = Symbol([f1, f2], messages=[m1], name="S0")
    >>> print(s.str_data())
    f1   | f2    
    ---- | ------
    '22' | '0044'
    ---- | ------


    ## Size field on the right

    Size field targeting a field containing a alt variable, with size field on the right:

    >>> f1 = Field(Alt(["A", "B", "C"]), name='f1')
    >>> f2 = Field(Size(f1, dataType=uint8()), name='f2')
    >>> s = Symbol([f2, f1])
    >>> d = s.specialize()
    >>> d
    b'\x01B'
    >>> Symbol.abstract(d, [s])
    (Symbol, OrderedDict([('f2', b'\x01'), ('f1', b'B')]))

    Size field targeting a alt variable, with size field on the right:

    >>> v1 = Alt(["A", "B", "C"])
    >>> v2 = Size(v1, dataType=uint8())
    >>> s = Symbol([Field(v2, name='f2'), Field(v1, name='f1')])
    >>> d = s.specialize()
    >>> d
    b'\x01B'
    >>> Symbol.abstract(d, [s])
    (Symbol, OrderedDict([('f2', b'\x01'), ('f1', b'B')]))


    ## Size field on the left

    Size field targeting a field containing a alt variable, with size field on the left:

    >>> f1 = Field(Alt(["A", "B", "C"]), name='f1')
    >>> f2 = Field(Size(f1, dataType=uint8()), name='f2')
    >>> s = Symbol([f1, f2])
    >>> d = s.specialize()
    >>> d
    b'A\x01'
    >>> Symbol.abstract(d, [s])
    (Symbol, OrderedDict([('f1', b'A'), ('f2', b'\x01')]))

    Size field targeting a alt variable, with size field on the left:

    >>> v1 = Alt(["A", "B", "C"])
    >>> v2 = Size(v1, dataType=uint8())
    >>> s = Symbol([Field(v1, name='f1'), Field(v2, name='f2')])
    >>> d = s.specialize()
    >>> d
    b'B\x01'
    >>> Symbol.abstract(d, [s])
    (Symbol, OrderedDict([('f1', b'B'), ('f2', b'\x01')]))


    ## Value field on the right

    Value field targeting a field containing a alt variable, with value field on the right:

    >>> f1 = Field(Alt(["A", "B", "C"]), name='f1')
    >>> f2 = Field(Value(f1), name='f2')
    >>> s = Symbol([f2, f1])
    >>> d = s.specialize()
    >>> d
    b'CC'
    >>> Symbol.abstract(d, [s])
    (Symbol, OrderedDict([('f2', b'C'), ('f1', b'C')]))

    Value field targeting a alt variable, with value field on the right:

    >>> v1 = Alt(["A", "B", "C"])
    >>> v2 = Value(v1)
    >>> s = Symbol([Field(v2, name='f2'), Field(v1, name='f1')])
    >>> d = s.specialize()
    >>> d
    b'BB'
    >>> Symbol.abstract(d, [s])
    (Symbol, OrderedDict([('f2', b'B'), ('f1', b'B')]))


    ## Value field on the left

    Value field targeting a field containing a alt variable, with value field on the left:

    >>> f1 = Field(Alt(["A", "B", "C"]), name='f1')
    >>> f2 = Field(Value(f1), name='f2')
    >>> s = Symbol([f1, f2])
    >>> d = s.specialize()
    >>> d
    b'BB'
    >>> Symbol.abstract(d, [s])
    (Symbol, OrderedDict([('f1', b'B'), ('f2', b'B')]))

    Value field targeting a alt variable, with value field on the left:

    >>> v1 = Alt(["A", "B", "C"])
    >>> v2 = Value(v1)
    >>> s = Symbol([Field(v1, name='f1'), Field(v2, name='f2')])
    >>> d = s.specialize()
    >>> d
    b'BB'
    >>> Symbol.abstract(d, [s])
    (Symbol, OrderedDict([('f1', b'B'), ('f2', b'B')]))

    """
