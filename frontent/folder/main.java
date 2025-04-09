public class InterFunctionTest {
    
    public static void main(String[] args) {
        // Cross-language call
        int result = nativeMultiply(3, 4);  // Line 5
        
        // Inter-function call
        helper("test", 5);  // Line 7
    }

    // Native method declaration
    public static native int nativeMultiply(int a, int b);  // Line 10

    // Helper method
    public static void helper(String str, int num) {  // Line 13
        // Nested cross-language call
        System.loadLibrary("native");  // Line 15
        
        // Local cross-language call
        int x = nativeMultiply(num, 2);  // Line 17
    }
}
