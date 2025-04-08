// ParserTest.java
// Sample Java code containing various integration call patterns
import org.python.util.PythonInterpreter;
import jep.Jep;
import org.apache.thrift.transport.TTransport;
import org.apache.thrift.transport.TSocket;
import org.apache.thrift.protocol.TBinaryProtocol;
import org.apache.thrift.protocol.TProtocol;
import org.apache.thrift.TException;
import java.net.Socket;
import java.io.DataOutputStream;
import java.io.DataInputStream;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.URI;
import com.sun.jna.Native;
import com.sun.jna.Library;

public class ParserTest {

    // Dummy JNA interface
    public interface CLib extends Library {
        CLib INSTANCE = Native.load("mylib", CLib.class);
        int add(int a, int b);
    }

    // Dummy SWIG module
    public static class mymodule {
        public static native int add(int a, int b);
    }

    // Dummy JavaCPP class
    public static class JavaCPPDemo {
        public static native int add(int a, int b);
    }

    // Dummy BridJ class
    public static class BridJDemo {
        public static native int add(int a, int b);
    }

    public static void main(String[] args) throws Exception {
        // 1. Jython
        PythonInterpreter py = new PythonInterpreter();
        py.exec("from mymodule import my_func; my_func(1, 2)");

        // 2. JEP
        Jep jep = new Jep();
        jep.eval("from mymodule import my_func; res = my_func(3, 4)");
        jep.exec("my_func(5, 6)");

        // 3. ProcessBuilder → Python
        ProcessBuilder pbPy = new ProcessBuilder("python3", "myscript.py", "7", "8");
        pbPy.start();

        // 4. Thrift RPC (client side)
        TTransport transport = new TSocket("localhost", 9090);
        transport.open();
        MyService.Client thriftClient = new MyService.Client(
            new TBinaryProtocol(transport)
        );
        int thriftRes = thriftClient.my_func(9, 10);
        transport.close();

        // 5. REST/HTTP → Python Flask
        HttpClient httpClient = HttpClient.newHttpClient();
        HttpRequest httpReq = HttpRequest.newBuilder()
            .uri(URI.create("http://localhost:5000/add?a=11&b=12"))
            .build();
        HttpResponse<String> httpResp = httpClient.send(httpReq, HttpResponse.BodyHandlers.ofString());
        int restRes = Integer.parseInt(
            httpResp.body().replaceAll("\\D+", "")
        );

        // 6. Raw sockets → Python socket server
        Socket sockPy = new Socket("localhost", 6000);
        DataOutputStream outPy = new DataOutputStream(sockPy.getOutputStream());
        DataInputStream inPy = new DataInputStream(sockPy.getInputStream());
        outPy.writeInt(13);
        outPy.writeInt(14);
        int sockPyRes = inPy.readInt();
        sockPy.close();

        // 7. JNI
        JNIDemo jni = new JNIDemo();
        int jniRes = jni.add(15, 16);

        // 8. JNA
        int jnaRes = CLib.INSTANCE.add(17, 18);

        // 9. SWIG
        int swigRes = mymodule.add(19, 20);

        // 10. JavaCPP
        int cppRes1 = JavaCPPDemo.add(21, 22);

        // 11. BridJ
        int bridjRes = BridJDemo.add(23, 24);

        // 12. ProcessBuilder → C++ binary
        ProcessBuilder pbCpp = new ProcessBuilder("./myprog", "25", "26");
        pbCpp.start();

        // 13. Raw sockets → C++ socket server
        Socket sockCpp = new Socket("localhost", 7000);
        DataOutputStream outCpp = new DataOutputStream(sockCpp.getOutputStream());
        DataInputStream inCpp = new DataInputStream(sockCpp.getInputStream());
        outCpp.writeInt(27);
        outCpp.writeInt(28);
        int sockCppRes = inCpp.readInt();
        sockCpp.close();

        // 14. Direct static/global call
        int directRes = my_func(29, 30);
    }

    // Dummy global function to test static calls
    public static int my_func(int a, int b) {
        return a + b;
    }

    // Dummy Thrift service interface
    public static class MyService {
        public static class Client {
            public Client(TProtocol proto) {}
            public int my_func(int a, int b) throws TException { return a + b; }
        }
    }

    // Dummy JNI class
    public static class JNIDemo {
        static { System.loadLibrary("native"); }
        public native int add(int a, int b);
    }
}
