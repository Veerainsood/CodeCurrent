#!/usr/bin/env python3
# test_calls.py

import jpype
from jpype import JClass
from py4j.java_gateway import JavaGateway, JavaGateway as PJG
import ctypes
from cffi import FFI
import subprocess
import mycppmod              # pretend this is a pybind11/SWIG/C++ extension
from com.example import OtherJavaClass   # Jython-style import

# — JPype via module
jpype.startJVM(classpath=['/path/to/lib.jar'])
MyJavaClass = jpype.JClass('com.example.MyJavaClass')
java_obj1 = MyJavaClass()
res1 = java_obj1.doSomething(42, "hello")
jpype.shutdownJVM()

# — JPype via direct JClass import
MyJavaClass2 = JClass('com.example.MyOtherClass')
java_obj2 = MyJavaClass2()
res2 = java_obj2.otherMethod()

# — Py4J via default name
gateway1 = JavaGateway()
entry1 = gateway1.entry_point
res3 = entry1.compute(3, 4)

# — Py4J via alias
gateway2 = PJG()
entry2 = gateway2.entry_point
res4 = entry2.aliasCompute(5, 6)

# — Jython-style class instantiation
jobj1 = OtherJavaClass()
res5 = jobj1.processData("foo")

# — subprocess → Java
result_java = subprocess.run(
    ['java', '-cp', 'app.jar', 'com.example.Main', 'arg1', 'arg2'],
    capture_output=True, text=True
)

# — ctypes.CDLL
lib1 = ctypes.CDLL('./mylib.so')
res6 = lib1.add(1, 2)
res7 = lib1.multiply(3, 4)

# — ctypes.WinDLL
winlib = ctypes.WinDLL('mylib.dll')
res8 = winlib.win_func(9, 10)

# — cffi
ffi = FFI()
lib2 = ffi.dlopen('./mylib.so')
res9 = lib2.subtract(5, 6)

# — generic C++ extension (SWIG/pybind11)
res10 = mycppmod.foo(7, 8)
res11 = mycppmod.bar("a", "b", "c")

# — subprocess → C++ binary
result_cpp = subprocess.run(
    ['./myprog', 'param1', 'param2'],
    capture_output=True, text=True
)

print("Done!")
