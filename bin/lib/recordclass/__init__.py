# The MIT License (MIT)
# 
# Copyright (c) <2011-2014> <Shibzukhov Zaur, szport at gmail dot com>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import sys as _sys
_PY36 = _sys.version_info[:2] >= (3, 6)
del _sys

# __all__ = ('memoryslots', 'recordobject', 'datatype', 'make_class', 
#            'recordclass', 'structclass', 'join_classes', 'arrayclass',
#            'dataobject', 'datatuple',
#            'RecordClass', 'StructClass')

from .memoryslots import memoryslots
from .recordclass import recordclass

from .recordobject import sequenceproxy, recordobject
from .structclass import structclass, join_classes
from .arrayclass import arrayclass

from .datatype import make_class, datatype
from .dataobject import dataobject, datatuple

if _PY36:
    from .typing import RecordClass, StructClass

__version__ = '0.10.2'
