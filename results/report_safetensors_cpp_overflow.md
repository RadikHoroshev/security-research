# Integer Overflow in safetensors-cpp `get_shape_size()` → Heap Buffer Overflow

## Vulnerability Type
Integer Overflow / Buffer Overflow / Improper Input Validation

## CVSS 3.1 Score
**9.8 Critical** — `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H`

## Summary
The C++ SafeTensors parser (`safetensors-cpp`) contains an integer overflow vulnerability in the `get_shape_size()` function. When computing the total number of tensor elements by multiplying shape dimensions, the function performs unchecked `size_t` multiplication. A crafted `.safetensors` file with shape dimensions whose product overflows `size_t` (e.g., 2^64) will result in a small or zero `tensor_size`. This overflowed value allows the file to pass all validation checks (like `validate_data_offsets()`), but downstream code accessing the tensor data using the original large shape dimensions will perform out-of-bounds (OOB) memory access, leading to a heap buffer overflow, information disclosure, or remote code execution.

## Root Cause
In `safetensors.hh` at line 4628:
```cpp
size_t sz = 1;
for (size_t i = 0; i < t.shape.size(); i++) {
    sz *= t.shape[i];  // ← NO OVERFLOW CHECK
}
return sz;
```
The script multiplies shape dimensions without checking for overflow. A crafted shape like `[2^33, 2^33]` results in `sz` being `2^66 mod 2^64 = 4`.

## Steps to Reproduce
1.  Use the provided `poc_safetensors_cpp_overflow.py` to create a malicious `.safetensors` file:
    ```bash
    python3 poc_safetensors_cpp_overflow.py --create overflow.safetensors
    ```
2.  Compile a C++ application that uses `safetensors-cpp` to load the file.
3.  Load `overflow.safetensors`. The library will report that the file is valid and has been loaded successfully.
4.  Observe that `get_shape_size()` returns a small overflowed value (e.g., 4) while the actual shape is much larger.
5.  Any subsequent access to the tensor data based on the shape dimensions will result in a heap buffer overflow.

## Proof of Concept
A standalone PoC script `poc_safetensors_cpp_overflow.py` is included. It can:
-   Verify the vulnerability in the live GitHub source using `--verify`.
-   Compile and run a C++ test case to demonstrate the overflow using `--test`.

## Impact
-   **Critical Heap Buffer Overflow:** Exploitable for Remote Code Execution (RCE).
-   **Information Disclosure:** Out-of-bounds reads can leak sensitive heap memory.
-   **Denial of Service:** Causes application crashes due to invalid memory access.
-   **Supply Chain Risk:** Malicious models on the Hugging Face Hub can target C++ users of SafeTensors.

## Remediation
Implement overflow-checked multiplication in `get_shape_size()`:
```cpp
size_t sz = 1;
for (size_t i = 0; i < t.shape.size(); i++) {
    if (t.shape[i] > 0 && sz > SIZE_MAX / t.shape[i]) {
        return 0; // Overflow
    }
    sz *= t.shape[i];
}
```
The `validate_data_offsets()` function should also be updated to reject shapes that cause an overflow.

## Researcher's Note
This vulnerability was previously identified in the Rust reference implementation (TOB-SFTN-1) and fixed using `checked_mul`. However, the C++ port (`safetensors-cpp`) remains vulnerable, highlighting a lack of parity between the reference implementation and its ports.
