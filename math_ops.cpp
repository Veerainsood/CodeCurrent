int add(const int arr[], int left, int right, int target) {
    if (left > right) return -1; // Base case: not found

    int mid = left + (right - left) / 2;
    if (arr[mid] == target) return mid; // Found the target
    return add(arr, left, mid - 1, target);
}