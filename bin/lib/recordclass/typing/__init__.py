import collections
from recordclass import recordclass, structclass
from typing import _type_check

import sys as _sys
_PY36 = _sys.version_info[:2] >= (3, 6)

_prohibited = ('__new__', '__init__', '__slots__', '__getnewargs__',
               '__attrs__', '_field_defaults', '_field_types',
               '_make', '_replace', '_asdict', '_source')

_special = ('__module__', '__name__', '__qualname__', '__annotations__')

def _make_recordclass(name, types, readonly=False, hashable=False):
    msg = "RecordClass('Name', [(f0, t0), (f1, t1), ...]); each t must be a type"
    types = [(n, _type_check(t, msg)) for n, t in types]
    rec_cls = recordclass(name, [n for n, t in types], readonly=readonly, hashable=hashable)
    rec_cls.__annotations__ = dict(types)
    try:
        rec_cls.__module__ = _sys._getframe(2).f_globals.get('__name__', '__main__')
    except (AttributeError, ValueError):
        pass
    return rec_cls

class RecordClassMeta(type):
    def __new__(cls, typename, bases, ns):
        if ns.get('_root', False):
            return super().__new__(cls, typename, bases, ns)
        types = ns.get('__annotations__', {})

        options = ns.pop('__options__', {})
        readonly = options.get('readonly', False)
        hashable = options.get('hashable', False)

        if readonly and not hashable:
            hashable = True

        defaults = []
        defaults_dict = {}
        for field_name in types:
            if field_name in ns:
                default_value = ns[field_name]
                defaults.append(default_value)
                defaults_dict[field_name] = default_value
            elif defaults:
                raise TypeError("Non-default recordclass field {field_name} cannot "
                                "follow default field(s) {default_names}"
                                .format(field_name=field_name,
                                        default_names=', '.join(defaults_dict.keys())))

        rec_cls = _make_recordclass(typename, types.items(), readonly=readonly, hashable=hashable)
        rec_cls.__annotations__ = dict(types)

        rec_cls.__new__.__defaults__ = tuple(defaults)
        rec_cls.__new__.__annotations__ = collections.OrderedDict(types)
        # update from user namespace without overriding special recordclass attributes
        for key in ns:
            if key in _prohibited:
                raise AttributeError("Cannot overwrite RecordClass attribute " + key)
            elif key not in _special and key not in rec_cls.__attrs__:
                setattr(rec_cls, key, ns[key])

        return rec_cls


class RecordClass(metaclass=RecordClassMeta):
    _root = True

    def __new__(self, typename, fields=None, **kwargs):
        if fields is None:
            fields = kwargs.items()
        elif kwargs:
            raise TypeError("Either list of fields or keywords"
                            " can be provided to RecordClass, not both")
        return _make_recordclass(typename, fields)


def _make_structclass(name, types, readonly=False, usedict=False, gc=False, 
                            weakref=False, hashable=False):
    msg = "StructClass('Name', [(f0, t0), (f1, t1), ...]); each t must be a type"
    types = [(n, _type_check(t, msg)) for n, t in types]
    struct_cls = structclass(name, [n for n, _ in types], 
                             readonly=readonly, usedict=usedict, gc=gc, 
                             weakref=weakref, hashable=hashable)
    struct_cls.__annotations__ = dict(types)
    try:
        struct_cls.__module__ = _sys._getframe(2).f_globals.get('__name__', '__main__')
    except (AttributeError, ValueError):
        pass
    return struct_cls
    
class StructClassMeta(type):
    def __new__(cls, typename, bases, ns):
        if ns.get('_root', False):
            return super().__new__(cls, typename, bases, ns)
        types = ns.get('__annotations__', {})

        options = ns.pop('__options__', {})
        readonly = options.get('readonly', False)
        usedict = options.get('usedict', False)
        weakref = options.get('weakref', False)
        hashable = options.get('hashable', False)
        
        if 'gc' in options:
            gc = options.get('gc')
        else:
            gc = 0        
        
        defaults = []
        defaults_dict = {}
        for field_name in types:
            if field_name in ns:
                default_value = ns[field_name]
                defaults.append(default_value)
                defaults_dict[field_name] = default_value
            elif defaults:
                raise TypeError("Non-default recordclass field {field_name} cannot "
                                "follow default field(s) {default_names}"
                                .format(field_name=field_name,
                                        default_names=', '.join(defaults_dict.keys())))
        
        struct_cls = _make_structclass(typename, types.items(),
                            readonly=readonly, usedict=usedict, gc=gc, 
                            weakref=weakref, hashable=hashable)

        struct_cls.__new__.__defaults__ = tuple(defaults)
        struct_cls.__new__.__annotations__ = collections.OrderedDict(types)
        #struct_cls._field_defaults = defaults_dict
        # update from user namespace without overriding special recordclass attributes
        for key in ns:
            if key in _prohibited:
                raise AttributeError("Cannot overwrite RecordClass attribute " + key)
            elif key not in _special and key not in struct_cls.__attrs__:
                setattr(struct_cls, key, ns[key])

        return struct_cls

class StructClass(metaclass=StructClassMeta):
    _root = True

    def __new__(self, typename, fields=None, **kwargs):
        if fields is None:
            fields = kwargs.items()
        elif kwargs:
            raise TypeError("Either list of fields or keywords"
                            " can be provided to RecordClass, not both")
        return _make_structclass(typename, fields)
