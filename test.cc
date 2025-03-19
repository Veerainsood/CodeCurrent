#include <iostream>
#include <vector>
#include <algorithm>

using namespace std;

// Recursive Binary Search
int recursiveBinarySearch(const vector<int>& arr, int left, int right, int target) {
    if (left > right) return -1; // Base case: not found

    int mid = left + (right - left) / 2;

    if (arr[mid] == target) return mid; // Found the target
    if (arr[mid] < target) return recursiveBinarySearch(arr, mid + 1, right, target);
    
    return recursiveBinarySearch(arr, left, mid - 1, target);
}

// Iterative Binary Search
int iterativeBinarySearch(const vector<int>& arr, int target) {
    int left = 0, right = arr.size() - 1;

    while (left <= right) {
        int mid = left + (right - left) / 2;

        if (arr[mid] == target) return mid;
        if (arr[mid] < target) left = mid + 1;
        else right = mid - 1;
    }
    return -1; // Not found
}

// STL-based Binary Search (returns true/false)
bool stlBinarySearch(const vector<int>& arr, int target) {
    return binary_search(arr.begin(), arr.end(), target);
}

int main() {
    vector<int> arr = {1, 2, 4, 4, 5, 6, 7, 9, 12, 15};
    int target = 4;

    // Recursive Search
    int recursiveIndex = recursiveBinarySearch(arr, 0, arr.size() - 1, target);
    cout << "Recursive Binary Search: " << (recursiveIndex != -1 ? to_string(recursiveIndex) : "Not Found") << endl;

    // Iterative Search
    int iterativeIndex = iterativeBinarySearch(arr, target);
    cout << "Iterative Binary Search: " << (iterativeIndex != -1 ? to_string(iterativeIndex) : "Not Found") << endl;

    // STL Binary Search
    cout << "STL Binary Search: " << (stlBinarySearch(arr, target) ? "Found" : "Not Found") << endl;

    return 0;
}
