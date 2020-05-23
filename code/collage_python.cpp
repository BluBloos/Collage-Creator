/*
PyObject *PythonArgsFromIntArray(int arraySize, int *array)
{
 PyObject *pArgs = Py_NewTuple();
 for (unsigned int i = 0; i < arraySize; i++)
 {
 
 }
}

PyObject *PythonFunctionCall(PyObject *module, char *funcName, PyObject * pArgs)
{
 if (pModule)
 {
  PyObject * pFunc = PyObject_GetAttrString(pModule, funcName);
  
  if (pFunc && PyCallable_Check(pFunc))
  {
   PyObject * pValue = PyObject_CallObject(pFunc, pArgs);
   Py_DECREF(pArgs);
   
   if (pValue)
   {
 long long newVal = PyLong_AsLong(pValue);
 Py_DECREF(pValue);
   }
  }
  
  // xdecref is used when the thing may be null
  Py_XDECREF(pFunc);
  Py_DECREF(pModule);
 }
}
*/