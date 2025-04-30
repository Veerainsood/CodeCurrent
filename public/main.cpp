#include <Python.h>
#include <pybind11/embed.h>
#include <boost/python.hpp>
#include <cstdlib>
#include <jni.h>
#include <zmq.hpp>
namespace py = pybind11;
using namespace boost::python;

void test_python_c_api() {
    Py_Initialize();
    PyObject *mod = PyImport_ImportModule("mymodule");
    PyTuple_SetItem(args, 0, PyLong_FromLong(10));
    PyObject *func = PyObject_GetAttrString(mod, "myfunc");
    PyTuple_SetItem(args, 1, PyUnicode_FromString("hello"));
    PyObject *args = PyTuple_New(2);
    PyObject *res = PyObject_CallObject(func, args);
    Py_Finalize();
}

void test_pybind11() {
    py::scoped_interpreter guard{};
    py::object mod = py::module::import("mymodule");
    py::object result = mod.attr("myfunc")(10, "world");
}

void test_boost_python() {
    Py_Initialize();
    object mod = import("mymodule");
    object res = mod.attr("myfunc")(99, "boost");
    Py_Finalize();
}

void test_swig_wrapper() {
    int result = myfunc(123, "swig test");
}

void test_system_python() {
    system("python3 -c \"import mymodule; mymodule.myfunc(1, 'x')\"");
}

void test_zmq_python() {
    zmq::context_t ctx(1);
    zmq::socket_t s(ctx, ZMQ_REQ);
    s.connect("tcp://localhost:5000");
    s.send(zmq::buffer("myfunc(10, 'abc')"));
    zmq::message_t reply;
    s.recv(reply);
}

void test_java_jni() {
    JavaVM *jvm;
    JNIEnv *env;
    JavaVMInitArgs args;
    JavaVMOption opt[1];
    opt[0].optionString = (char*)"-Djava.class.path=.";
    args.version = JNI_VERSION_1_8;
    args.nOptions = 1;
    args.options = opt;
    JNI_CreateJavaVM(&jvm, (void**)&env, &args);

    jclass cls = env->FindClass("MyJavaClass");
    jmethodID mid = env->GetStaticMethodID(cls, "myJavaMethod", "(I)I");
    jint result = env->CallStaticIntMethod(cls, mid, 42);

    jvm->DestroyJavaVM();
}

void test_system_java() {
    system("java MyJavaClass 42");
}

void test_http_java() {
    system("curl http://localhost:8080/myJavaMethod?x=42");
}

void test_socket_java() {
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    connect(sock, nullptr, 0); // skipped actual socket setup
    send(sock, "myJavaMethod(42)", 16, 0);
}
