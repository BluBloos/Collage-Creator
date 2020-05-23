from .dataobject import dataobject, datatuple, itemgetset
from .dataobject import enable_gc, dataobject_type_init, dataslot_offset
from .dataobject import number_of_dataslots, set_dict, set_hash, set_weakref, sequence_protocol

from .utils import make_new_function, check_fields
from .utils import fields_from_bases, defaults_from_bases, annotations_from_bases

import sys as _sys
_PY3 = _sys.version_info[0] >= 3
#_PY36 = _PY3 and _sys.version_info[1] >= 6

if _PY3:
    _intern = _sys.intern
else:
    from __builtin__ import intern as _intern
    
# __all__ = 'datatype', 'new_datatype', 'make_class', 'asdict'

int_type = type(1)

def new_datatype(typename, fields=0, bases=None, namespace=None, 
                 varsize=False,  use_dict=False, use_weakref=False, hashable=True,
                 sequence=False, readonly=False, gc=False,
                 defaults=None, module=None, argsonly=False):

    annotations = {}
    fields_is_int = False
    if isinstance(fields, str):
        fields = fields.replace(',', ' ').split()
    elif isinstance(fields, int_type):
        fields_is_int = True
    else:
        msg = "new_datatype('Name', [(f0, t0), (f1, t1), ...]); each t must be a type"
        field_names = []
        if isinstance(fields, dict):
            for fn in fields:
                t = fields[fn]
                t = _type_check(t, msg)
                annotations[fn] = t
                field_names.append(fn)
        else:
            for fn in fields:
                if type(fn) is tuple:
                    n, t = fn
                    t = _type_check(t, msg)
                    annotations[n] = t
                    field_names.append(n)
                else:
                    field_names.append(fn)
        fields = field_names

    typename = _intern(str(typename))
    
    if not fields_is_int and defaults is not None:
        n_fields = len(fields)
        defaults = tuple(defaults)
        n_defaults = len(defaults)
        if n_defaults > n_fields:
            raise TypeError('Got more default values than fields')
    else:
        defaults = None

    options = {
        'dict':use_dict, 'weakref':use_weakref,
        'hash':hashable, 'varsize':varsize,
        'sequence':sequence, 'readonly':readonly,
        'defaults':defaults, 'argsonly':argsonly,
    }

    if namespace is None:
        ns = {}
    else:
        ns = namespace

    if defaults:
        for i in range(-n_defaults, 0):
            fname = fields[i]
            val = defaults[i]
            ns[fname] = val

    ns['__options__'] = options
    ns['__fields__'] = fields
    if annotations:
        ns['__annotations__'] = annotations
    cls = datatype(typename, bases, ns)
    
    if gc:
        cls = enable_gc(cls)

    if module is None:
        try:
            module = _sys._getframe(1).f_globals.get('__name__', '__main__')
        except (AttributeError, ValueError):
            module = None
    if module is not None:
        cls.__module__ = module

    return cls

make_class = new_datatype
    
class datatype(type):

    def __new__(metatype, typename, bases, ns):        

        options = ns.pop('__options__', {})
        readonly = options.get('readonly', False)
        hashable = options.get('hashable', True)
        sequence = options.get('sequence', False)
        varsize = options.get('varsize', False)
        argsonly = options.get('argsonly', False)

        if not bases:
            if varsize:
                bases = (datatuple,)
            else:
                bases = (dataobject,)
                
        if issubclass(bases[0], datatuple):
            varsize = True
        elif issubclass(bases[0], dataobject):
            varsize = False
        else:
            raise TypeError("First base class should be instance of dataobject or datatuple")

        use_dict = False
        if '__dict__' in ns:
            use_dict = True
        use_weakref = False
        if '__weakref__' in ns:
            use_weakref = True

        use_dict = use_dict or options.get('dict', False)
        use_weakref = use_weakref or options.get('weakref', False)

        annotations = ns.get('__annotations__', {})

        if '__fields__' in ns:
            fields = ns.pop('__fields__')
        else:
            fields = [name for name in annotations]
            
        has_fields = True
        if isinstance(fields, int_type):
            has_fields = False
            n_fields = fields
            sequence = True
            
        if varsize:
            sequence = True

        if has_fields:
            fields = check_fields(typename, fields)

            if '__dict__' in fields:
                fields.remove('__dict__')
                use_dict = True

            if '__weakref__' in fields:
                fields.remove('__weakref__')
                use_weakref = True

            n_fields = len(fields)
                
            _fields = fields_from_bases(bases)
            _annotations = annotations_from_bases(bases)
            _defaults = defaults_from_bases(bases)

            defaults = {f:ns[f] for f in fields if f in ns}

            if fields:
                fields = [f for f in fields if f not in _fields]
                n_fields = len(fields)
            fields = _fields + fields
            n_fields += len(_fields)

            _defaults.update(defaults)
            defaults = _defaults

            _annotations.update(annotations)
            annotations = _annotations
        
            fields = tuple(fields)
        
            if fields and (not argsonly or defaults) and '__new__' not in ns:
                if fields and defaults:
                    fields2 = [f for f in fields if f not in defaults] + [f for f in fields if f in defaults]
                else:
                    fields2 = fields
                fields2 = tuple(fields2)

                __new__ = make_new_function(typename, fields, fields2, varsize, use_dict)

                if defaults:
                    default_vals = tuple(defaults[f] for f in fields2 if f in defaults)
                    __new__.__defaults__ = default_vals
                if annotations:
                    __new__.__annotations__ = annotations

                ns['__new__'] = __new__

        cls = type.__new__(metatype, typename, bases, ns)

        if fields:
            cls.__fields__ = fields
        if has_fields:
            if defaults:
                cls.__defaults__ = defaults
            if annotations:
                cls.__annotations__ = annotations

        dataobject_type_init(cls, n_fields, varsize, has_fields)
        set_dict(cls, use_dict)
        set_hash(cls, hashable)
        set_weakref(cls, use_weakref)        

        sequence_protocol(cls, sequence, readonly)

        if has_fields:
            if readonly is None or type(readonly) is bool:
                if readonly:
                    readonly_fields = set(fields)
                else:
                    readonly_fields = set()
            else:
                readonly_fields = set(readonly)

            for i, name in enumerate(fields):
                if name in readonly_fields:
                    setattr(cls, name, itemgetset(dataslot_offset(cls, i), True))
                else:
                    setattr(cls, name, itemgetset(dataslot_offset(cls, i)))
        
        return cls

def asdict(ob):
    _getattr = getattr
    return {fn:_getattr(ob, fn) for fn in ob.__class__.__fields__}
    
from .dataobject import _fix_type
_fix_type(dataobject, datatype)
_fix_type(datatuple, datatype)
del _fix_type
