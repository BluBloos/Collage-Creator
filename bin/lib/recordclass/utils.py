import sys as _sys
_PY3 = _sys.version_info[0] >= 3
_PY36 = _PY3 and _sys.version_info[1] >= 6

from keyword import iskeyword as _iskeyword

if _PY3:
    _intern = _sys.intern
    def _isidentifier(s):
        return s.isidentifier()
    if _PY36:
        from typing import _type_check
    else:
        def _type_check(t, msg):
            if isinstance(t, (type, str)):
                return t
            else:
                raise TypeError('invalid type annotation', t)
else:
    from __builtin__ import intern as _intern
    import re as _re
    def _isidentifier(s):
        return _re.match(r'^[a-z_][a-z0-9_]*$', s, _re.I) is not None
    def _type_check(t, msg):
        return t
    
from .dataobject import dataobject, datatuple
from .dataobject import number_of_dataslots

def check_fields(typename, fields):
    if isinstance(fields, str):
        fields = fields.split()
    elif isinstance(fields, tuple):
        fields = list(fields)

    if isinstance(fields, list):
        fields = [fn.strip() for fn in fields]
        n_fields = len(fields)

        for name in [typename] + fields:
            if not isinstance(name, str):
                raise TypeError('Type names and field names must be strings')
            if not _isidentifier(name):
                raise ValueError('Type names and field names must be valid '
                                 'identifiers: %r' % name)
            if _iskeyword(name):
                raise ValueError('Type names and field names cannot be a '
                                 'keyword: %r' % name)
    return fields

def fields_from_bases(bases):
    _fields = []
    for base in bases:
        if base is dataobject or base is datatuple:
            continue
        if issubclass(base, (dataobject, datatuple)):
            n = number_of_dataslots(base)
            if n:
                fs = base.__dict__.get('__fields__', ())
                if type(fs) is tuple:
                    _fields.extend(f for f in fs if f not in _fields)
                else:
                    raise TypeError("invalid fields in base class %r" % base)
    return _fields

def defaults_from_bases(bases):
    _defaults = {}
    for base in bases:
        if base is dataobject or base is datatuple:
            continue
        if issubclass(base, (dataobject, datatuple)):
            n = number_of_dataslots(base)
            if n:
                ds = base.__dict__.get('__defaults__', {})
                _defaults.update(ds)                        
    return _defaults
        
def annotations_from_bases(bases):
    _annotations = {}
    for base in bases:
        if base is dataobject or base is datatuple:
            continue
        if issubclass(base, (dataobject, datatuple)):
            n = number_of_dataslots(base)
            if n:
                ann = base.__dict__.get('__annotations__', {})
                _annotations.update(ann)
    return _annotations

def make_new_function(typename, fields, fields2, varsize, use_dict):
    if use_dict:
        if varsize:
            new_func_template = \
"""
def __new__(cls, {2}, *args, **kw):
    'Create new instance: {0}({1})'
    return _method_new(cls, {1}, *args, **kw)
"""            
        else:
            new_func_template = \
"""
def __new__(cls, {2}, **kw):
    'Create new instance: {0}({1})'
    return _method_new(cls, {1}, **kw)
"""
    else:
        if varsize:
            new_func_template = \
"""
def __new__(cls, {2}, *args):
    'Create new instance: {0}({1})'
    return _method_new(cls, {1}, *args)
"""
        else:
            new_func_template = \
"""
def __new__(cls, {2}):
    'Create new instance: {0}({1})'
    return _method_new(cls, {1})
"""
    new_func_def = new_func_template.format(typename, ', '.join(fields), ', '.join(fields2))
    
    if varsize:
        _method_new = datatuple.__new__
    else:
        _method_new = dataobject.__new__

    namespace = dict(_method_new=_method_new)

    code = compile(new_func_def, "", "exec")
    eval(code, namespace)

    return namespace['__new__']
