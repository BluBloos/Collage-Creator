from .recordobject import recordobject, arrayclasstype

import sys as _sys

def arrayclass(typename, n, readonly=False, usedict=False, gc=False, weakref=False, 
               hashable=False, module=None):
    new_func_template = """\
def __new__(_cls, *args):
    'Create new instance of dataobject of fixed size {0}'
    return _dataobject.__new__(_cls, *args)
""" 
    new_func_def = new_func_template.format(n)

    namespace = dict(_dataobject=recordobject)    
    code = compile(new_func_def, "", "exec")
    eval(code, namespace)    
    __new__ = namespace['__new__']

    def __repr__(self):
        'Return a nicely formatted representation string'
        return self.__class__.__name__ + "(" + ", ".join(str(x) for x in self) + ")" 

    for method in (__new__, __repr__,):
        method.__qualname__ = typename + "." + method.__name__

    __options__ = {'readonly':readonly, 'usedict':usedict, 'gc':gc, 'weakref':weakref, 'hashable':hashable}        

    class_namespace = {
        #'__slots__': (),
        '__size__': n, 
        '__doc__': typename+'(*args)',
        '__new__': __new__,
        '__repr__': __repr__,
        '__options__': __options__,
    }
    
    _result = arrayclasstype(typename, (recordobject,), class_namespace)
    
    # For pickling to work, the __module__ variable needs to be set to the frame
    # where the class is created. 
    if module is None:
        try:
            module = _sys._getframe(1).f_globals.get('__name__', '__main__')
        except (AttributeError, ValueError):
            pass
    if module is not None:
        _result.__module__ = module    

    return _result
