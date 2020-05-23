import unittest, doctest, operator
import pickle, copy
import keyword
import re
import sys
import gc
import weakref

from recordclass import make_class, datatype
from recordclass.datatype import asdict

_t = ()
headgc_size = sys.getsizeof(_t) - _t.__sizeof__()
del _t

TestPickle1 = make_class("TestPickle1", fields=3)
TestPickle2 = make_class("TestPickle2", fields=('x','y','z'))
TestPickle3 = make_class("TestPickle3", fields=('x','y','z'), use_dict=True)
TestPickleV1 = make_class("TestPickleV1", fields=3, varsize=True)
TestPickleV2 = make_class("TestPickleV2", fields=('x','y','z'), varsize=True)
TestPickleV3 = make_class("TestPickleV3", fields=('x','y','z'), varsize=True, use_dict=True)

class dataobjectTest(unittest.TestCase):
    
    def test_create0(self):
        gc.collect()
        cnt1 = gc.get_count()
        A = make_class("A", fields=2)
        B = make_class("B", varsize=True)
        b = B([], ())
        a = A({}, b)
        cnt2 = gc.get_count()
        self.assertEqual(gc.is_tracked(a), False)
        self.assertEqual(gc.is_tracked(b), False)
        del a
        gc.collect()
        cnt3 = gc.get_count()
        self.assertEqual(cnt1, cnt3)

    def test_create1(self):
        gc.collect()
        cnt1 = gc.get_count()
        A = make_class("A", fields=2)
        B = make_class("B", varsize=True)
        C = make_class("C", fields=2, varsize=True)
        b = A([], ())
        c = C(1,2,{1:2,3:4},[1,2])
        b1 = B(1, b)
        a = [b1, c]
        cnt2 = gc.get_count()
        self.assertEqual(gc.is_tracked(b), False)
        self.assertEqual(gc.is_tracked(b1), False)
        self.assertEqual(gc.is_tracked(c), False)
        del a
        gc.collect()
        cnt3 = gc.get_count()
        self.assertEqual(cnt1, cnt3)

    def test_gc_create0(self):
        gc.collect()
        cnt1 = gc.get_count()
        A = make_class("A", fields=2, gc=True)
        B = make_class("B", varsize=True, gc=True)
        b = B([], ())
        a = A({}, b)
        cnt2 = gc.get_count()
        self.assertEqual(gc.is_tracked(a), True)
        self.assertEqual(gc.is_tracked(b), True)
        del a
        gc.collect()
        cnt3 = gc.get_count()
        self.assertEqual(cnt1, cnt3)

    def test_gc_create1(self):
        gc.collect()
        cnt1 = gc.get_count()
        A = make_class("A", fields=2, gc=True)
        B = make_class("B", varsize=True, gc=True)
        C = make_class("C", fields=2, varsize=True, gc=True)
        b = A([], ())
        c = C(1,2,{1:2,3:4},[1,2])
        b1 = B(1, b)
        a = [b1, c]
        cnt2 = gc.get_count()
        self.assertEqual(gc.is_tracked(b), True)
        self.assertEqual(gc.is_tracked(b1), True)
        self.assertEqual(gc.is_tracked(c), True)
        del a
        gc.collect()
        cnt3 = gc.get_count()
        self.assertEqual(cnt1, cnt3)
        
    def test_fields0(self):
        A = make_class("A", fields=0)
        a = A()
        self.assertEqual(len(a), 0)
        self.assertEqual(repr(a), "A()")
        with self.assertRaises(IndexError): 
            a[0]
        with self.assertRaises(TypeError):     
            weakref.ref(a)
        with self.assertRaises(AttributeError):     
            a.__dict__
        a = None
        with self.assertRaises(TypeError):
            A(1)

    def test_fields1(self):
        A = make_class("A", fields=1)
        a = A(100)
        self.assertEqual(repr(a), "A(100)")
        self.assertEqual(len(a), 1)
        self.assertEqual(a[0], 100)
        self.assertEqual(a[-1], 100)
        with self.assertRaises(IndexError): 
            a[1]
        with self.assertRaises(TypeError):     
            weakref.ref(a)
        with self.assertRaises(AttributeError):     
            a.__dict__
        a = None
        with self.assertRaises(TypeError):
            A(1,2)

    def test_gc_fields0(self):
        A = make_class("A", fields=0, gc=True)
        a = A()
        self.assertEqual(repr(a), "A()")
        self.assertEqual(len(a), 0)
        with self.assertRaises(IndexError): 
            a[0]
        with self.assertRaises(TypeError):     
            weakref.ref(a)
        with self.assertRaises(AttributeError):     
            a.__dict__
        a = None
        with self.assertRaises(TypeError):
            A(1)

    def test_gc_fields1(self):
        A = make_class("A", fields=1, gc=True)
        a = A(100)
        self.assertEqual(repr(a), "A(100)")
        self.assertEqual(len(a), 1)
        self.assertEqual(a[0], 100)
        self.assertEqual(a[-1], 100)
        with self.assertRaises(IndexError): 
            a[1]
        with self.assertRaises(TypeError):     
            weakref.ref(a)
        with self.assertRaises(AttributeError):     
            a.__dict__
        a = None
        with self.assertRaises(TypeError):
            A(1,2)
            
    def test_varsize0(self):
        A = make_class("A", varsize=True)
        a = A()
        self.assertEqual(repr(a), "A()")
        self.assertEqual(len(a), 0)
        with self.assertRaises(IndexError): 
            a[0]
        with self.assertRaises(TypeError):     
            weakref.ref(a)
        with self.assertRaises(AttributeError):     
            a.__dict__
        a = None

    def test_varsize1(self):
        A = make_class("A", varsize=True)
        a = A(100)
        self.assertEqual(repr(a), "A(100)")
        self.assertEqual(len(a), 1)
        self.assertEqual(a[0], 100)
        self.assertEqual(a[-1], 100)
        with self.assertRaises(IndexError): 
            a[1]
        with self.assertRaises(TypeError):     
            weakref.ref(a)
        with self.assertRaises(AttributeError):     
            a.__dict__
        a = None

    def test_varsize2(self):
        A = make_class("A", varsize=True)
        a = A(100,200)
        self.assertEqual(repr(a), "A(100, 200)")
        self.assertEqual(len(a), 2)
        self.assertEqual(a[0], 100)
        self.assertEqual(a[1], 200)
        a[0] = -100
        a[1] = -200
        self.assertEqual(a[0], -100)
        self.assertEqual(a[1], -200)
        with self.assertRaises(IndexError): 
            a[100]
        with self.assertRaises(TypeError):     
            weakref.ref(a)
        with self.assertRaises(AttributeError):     
            a.__dict__
        a = None
        
    def test_fields_varsize1(self):
        A = make_class("A", fields=1, varsize=True)
        a = A(100, 200)
        self.assertEqual(repr(a), "A(100, 200)")
        self.assertEqual(len(a), 2)
        self.assertEqual(a[0], 100)
        self.assertEqual(a[1], 200)
        self.assertEqual(a[-1], 200)
        a[0] = -100
        a[1] = -200
        self.assertEqual(a[0], -100)
        self.assertEqual(a[1], -200)
        with self.assertRaises(IndexError): 
            a[2]
        with self.assertRaises(TypeError):     
            weakref.ref(a)
        with self.assertRaises(AttributeError):     
            a.__dict__
        a = None

    def test_gc_varsize0(self):
        A = make_class("A", varsize=True, gc=True)
        a = A()
        self.assertEqual(repr(a), "A()")
        self.assertEqual(len(a), 0)
        with self.assertRaises(IndexError): 
            a[0]
        with self.assertRaises(TypeError):     
            weakref.ref(a)
        with self.assertRaises(AttributeError):     
            a.__dict__
        a = None

    def test_gc_varsize1(self):
        A = make_class("A", varsize=True, gc=True)
        a = A(100,200)
        self.assertEqual(repr(a), "A(100, 200)")
        self.assertEqual(len(a), 2)
        self.assertEqual(a[0], 100)
        self.assertEqual(a[-1], 200)
        with self.assertRaises(IndexError): 
            a[2]
        with self.assertRaises(TypeError):     
            weakref.ref(a)
        with self.assertRaises(AttributeError):     
            a.__dict__
        a = None
        
    def test_datatype(self):
        A = make_class("A", fields=('x', 'y'))

        a = A(1,2)
        self.assertEqual(repr(a), "A(x=1, y=2)")
        self.assertEqual(a.x, 1)
        self.assertEqual(a.y, 2)
        self.assertEqual(asdict(a), {'x':1, 'y':2})
#         self.assertEqual(sys.getsizeof(a), 32)
        with self.assertRaises(TypeError):     
            weakref.ref(a)
        with self.assertRaises(AttributeError):     
            a.__dict__
        with self.assertRaises(AttributeError):     
            a.z = 3
        with self.assertRaises(AttributeError):     
            a.z            
        a = None

    def test_datatype_copy(self):
        A = make_class("A", fields=('x', 'y'))

        a = A(1,2)
        b = a.__copy__()
        self.assertEqual(a, b)

    def test_datatype_copy2(self):
        A = make_class("A", fields=('x', 'y'), varsize=True)

        a = A(1,2,(3,4,5))
        b = a.__copy__()
        self.assertEqual(a, b)
        
    def test_datatype_copy_dict(self):
        A = make_class("A", fields=('x', 'y'), use_dict=True)

        a = A(1,2, z=3,w=4)
        b = a.__copy__()
        self.assertEqual(a, b)
        
#     def test_datatype_subscript(self):
#         A = make_class("A", fields=('x', 'y'), sequence=True)

#         a = A(1,2)
#         self.assertEqual(a['x'], 1)
#         self.assertEqual(a['y'], 2)
#         a['x'] = 100
#         self.assertEqual(a['x'], 100)
#         a = None
        
    def test_datatype_dict(self):
        A = make_class("A", fields=('x', 'y'), use_dict=True, use_weakref=True)

        a = A(1,2)
        self.assertEqual(repr(a), "A(x=1, y=2)")
        self.assertEqual(a.x, 1)
        self.assertEqual(a.y, 2)
        self.assertEqual(asdict(a), {'x':1, 'y':2})
#         self.assertEqual(sys.getsizeof(a), 48)
#         self.assertEqual(A.__dictoffset__, 32)
#         self.assertEqual(A.__weakrefoffset__, 40)
        weakref.ref(a)
        self.assertEqual(a.__dict__, {})
        
        a.z = 3
        self.assertEqual(a.z, a.__dict__['z'])
        a = None

    def test_datatype_dict2(self):
        A = make_class("A", fields=('x', 'y'), use_dict=True)
        a = A(1,2,v=3,z=4)
        self.assertEqual(a.__dict__, {'v':3, 'z':4})
        b = A(1,2,z=3)
        self.assertEqual(b.__dict__, {'z':3})
        self.assertEqual(repr(b), "A(x=1, y=2, **{'z': 3})")
        
    def test_subclass(self):
        A = make_class("A", fields=('x', 'y'))
                
        class B(A):
            pass

        self.assertEqual(type(A), type(B))
        self.assertEqual(B.__dictoffset__, 0)
        self.assertEqual(B.__weakrefoffset__, 0)
        b = B(1,2)
        self.assertEqual(repr(b), "B(x=1, y=2)")
        self.assertEqual(b.x, 1)
        self.assertEqual(b.y, 2)
        self.assertEqual(asdict(b), {'x':1, 'y':2})
#         self.assertEqual(sys.getsizeof(a), 32)
        self.assertEqual(A.__basicsize__, B.__basicsize__)
        with self.assertRaises(TypeError):     
            weakref.ref(b)
        with self.assertRaises(AttributeError):     
            b.__dict__        
        #a = None

    def test_subclass2(self):
        A = make_class("A", fields=('x', 'y'))

        class B(A):
            __fields__ = ('z',)
                
        class C(B):
            pass

        self.assertEqual(type(A), type(B))
        self.assertEqual(type(C), type(B))
        self.assertEqual(C.__dictoffset__, 0)
        self.assertEqual(C.__weakrefoffset__, 0)
        c = C(1,2,3)
        self.assertEqual(repr(c), "C(x=1, y=2, z=3)")
        self.assertEqual(c.x, 1)
        self.assertEqual(c.y, 2)
        self.assertEqual(c.z, 3)
        self.assertEqual(asdict(c), {'x':1, 'y':2, 'z':3})
#         self.assertEqual(sys.getsizeof(c), 40)
        with self.assertRaises(TypeError):     
            weakref.ref(c)
        with self.assertRaises(AttributeError):     
            c.__dict__
        c = None
        
    def test_defaults(self):
        A = make_class("A", fields=('x', 'y', 'z'), defaults=(100, 200, 300))
                
        a1 = A()
        self.assertEqual(repr(a1), "A(x=100, y=200, z=300)")
        self.assertEqual(a1.x, 100)
        self.assertEqual(a1.y, 200)
        self.assertEqual(a1.z, 300)
        self.assertEqual(asdict(a1), {'x':100, 'y':200, 'z':300})
        a2 = A(1,z=400)
        self.assertEqual(repr(a2), "A(x=1, y=200, z=400)")
        self.assertEqual(a2.x, 1)
        self.assertEqual(a2.y, 200)
        self.assertEqual(a2.z, 400)
        self.assertEqual(asdict(a2), {'x':1, 'y':200, 'z':400})
        a3 = A(1,2,z=400)
        self.assertEqual(repr(a3), "A(x=1, y=2, z=400)")
        self.assertEqual(a3.x, 1)
        self.assertEqual(a3.y, 2)
        self.assertEqual(a3.z, 400)
        self.assertEqual(asdict(a3), {'x':1, 'y':2, 'z':400})

    def test_keyword_args(self):
        A = make_class("A", fields=('x', 'y', 'z'), defaults=(None, None, None))

        a1 = A(x=1)
        self.assertEqual(repr(a1), "A(x=1, y=None, z=None)")
        self.assertEqual(a1.x, 1)
        self.assertEqual(a1.y, None)
        self.assertEqual(a1.z, None)
        a2 = A(x=1,y=2)
        self.assertEqual(repr(a2), "A(x=1, y=2, z=None)")
        self.assertEqual(a2.x, 1)
        self.assertEqual(a2.y, 2)
        self.assertEqual(a2.z, None)
        a3 = A(x=1,y=2,z=3)
        self.assertEqual(repr(a3), "A(x=1, y=2, z=3)")
        self.assertEqual(a3.x, 1)
        self.assertEqual(a3.y, 2)
        self.assertEqual(a3.z, 3)

    def test_keyword_args_defaults(self):
        A = make_class("A", fields=('x', 'y', 'z'), defaults=(100, 200, 300))

        a1 = A(x=1)
        self.assertEqual(repr(a1), "A(x=1, y=200, z=300)")
        self.assertEqual(a1.x, 1)
        self.assertEqual(a1.y, 200)
        self.assertEqual(a1.z, 300)
        a2 = A(x=1,y=2)
        self.assertEqual(repr(a2), "A(x=1, y=2, z=300)")
        self.assertEqual(a2.x, 1)
        self.assertEqual(a2.y, 2)
        self.assertEqual(a2.z, 300)
        a3 = A(x=1,y=2,z=3)
        self.assertEqual(repr(a3), "A(x=1, y=2, z=3)")
        self.assertEqual(a3.x, 1)
        self.assertEqual(a3.y, 2)
        self.assertEqual(a3.z, 3)

    def test_missing_args(self):
        A = make_class("A", fields=3)
        a=A(1)
        self.assertEqual(a[0], 1)
        self.assertEqual(a[1], None)
        self.assertEqual(a[2], None)

    def test_missing_args2(self):
        A = make_class("A", fields=('a','b','c'), argsonly=True)
        a=A(1)
        self.assertEqual(a.a, 1)
        self.assertEqual(a.b, None)
        self.assertEqual(a.c, None)
    
    def test_tuple(self):
        A = make_class("A", fields=3)
        a=A(1, 2.0, "a")
        self.assertEqual(tuple(a), (1, 2.0, "a"))
        
    def test_hash(self):
        A = make_class("A", fields=3)
        a=A(1, 2.0, "a")
        hash(a)
        
    def test_reduce(self):
        A = make_class("A", fields=("x","y","z"))
        a = A(1,2,3)
        o,t = a.__reduce__()
        self.assertEqual(o, A)
        self.assertEqual(t, (1,2,3))
        
    def test_pickle1(self):
        p = TestPickle1(10, 20, 30)
#         print(p.__sizeof__())
        for module in (pickle,):
            loads = getattr(module, 'loads')
            dumps = getattr(module, 'dumps')
            for protocol in range(-1, module.HIGHEST_PROTOCOL + 1):
                tmp = dumps(p, protocol)
                q = loads(tmp)
                self.assertEqual(p, q)

    def test_pickle2(self):
        p = TestPickle2(10, 20, 30)
#         print(p.__sizeof__())
        for module in (pickle,):
            loads = getattr(module, 'loads')
            dumps = getattr(module, 'dumps')
            for protocol in range(-1, module.HIGHEST_PROTOCOL + 1):
                tmp = dumps(p, protocol)
                q = loads(tmp)
                self.assertEqual(p, q)

    def test_pickle3(self):
        p = TestPickle3(10, 20, 30)
        p.a = 1
        p.b = 2
#         print(p.__sizeof__())
        for module in (pickle,):
            loads = getattr(module, 'loads')
            dumps = getattr(module, 'dumps')
            for protocol in range(-1, module.HIGHEST_PROTOCOL + 1):
                tmp = dumps(p, protocol)
                q = loads(tmp)
                self.assertEqual(p, q)

    def test_pickle4(self):
        p = TestPickleV1(10, 20, 30)
#         print(p.__sizeof__())
        for module in (pickle,):
            loads = getattr(module, 'loads')
            dumps = getattr(module, 'dumps')
            for protocol in range(-1, module.HIGHEST_PROTOCOL + 1):
                tmp = dumps(p, protocol)
                q = loads(tmp)
                self.assertEqual(p, q)

    def test_pickle5(self):
        p = TestPickleV2(10, 20, 30)
#         print(p.__sizeof__())
        for module in (pickle,):
            loads = getattr(module, 'loads')
            dumps = getattr(module, 'dumps')
            for protocol in range(-1, module.HIGHEST_PROTOCOL + 1):
                tmp = dumps(p, protocol)
                q = loads(tmp)
                self.assertEqual(p, q)

    def test_pickle6(self):
        p = TestPickleV3(10, 20, 30)
        p.a = 1
        p.b = 2
#         print(p.__sizeof__())
        for module in (pickle,):
            loads = getattr(module, 'loads')
            dumps = getattr(module, 'dumps')
            for protocol in range(-1, module.HIGHEST_PROTOCOL + 1):
                tmp = dumps(p, protocol)
                q = loads(tmp)
                self.assertEqual(p, q)

    def test_pickle7(self):
        p = TestPickleV2(10, 20, 30, 100, 200, 300)
#         print(p.__sizeof__())
        for module in (pickle,):
            loads = getattr(module, 'loads')
            dumps = getattr(module, 'dumps')
            for protocol in range(-1, module.HIGHEST_PROTOCOL + 1):
                tmp = dumps(p, protocol)
                q = loads(tmp)
                self.assertEqual(p, q)
                
    def test_iter(self):
        A = make_class("A", fields=3)
        a=A(1, 2.0, "a")
        self.assertEqual(list(iter(a)), [1, 2.0, "a"])
        
    def test_iter2(self):
        A = make_class("A", fields=('x', 'y', 'z'))
        a=A(1, 2.0, "a")
        self.assertEqual(list(iter(a)), [1, 2.0, "a"])

    def test_enable_gc(self):

        A = make_class("A", ('x', 'y', 'z'))
        
        B = make_class("B", ('x', 'y', 'z'), gc=True)
            
        a = A(1,2,3)
        b = B(1,2,3)
        self.assertEqual(a.x, b.x)
        self.assertEqual(a.y, b.y)
        self.assertEqual(a.z, b.z)
        self.assertEqual(sys.getsizeof(b)-sys.getsizeof(a), headgc_size)
                
def main():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(dataobjectTest))
    return suite

