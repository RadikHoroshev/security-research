# RAGFlow Dependency Security Check Summary

Analysis of `infiniflow/ragflow` (as of April 2026) regarding document parsing and dependency-related security risks.

## Critical Vulnerabilities Identified

### 1. Supply Chain Risk: `unstructured` (CVE-2025-64712)
- **Status**: Critical (CVSS 9.8)
- **Component**: `unstructured` (specifically the `partition_msg()` function) via the `extract-msg` dependency.
- **Vulnerability**: Path Traversal leading to Arbitrary File Write.
- **Risk**: If RAGFlow utilizes `unstructured` for processing Microsoft Outlook `.msg` files, an attacker could craft a malicious `.msg` file with a filename like `../../root/.ssh/authorized_keys`. This would overwrite critical system files upon processing, leading to Remote Code Execution (RCE).
- **Remediation**: Ensure `unstructured` is updated to version **0.18.18** or higher.

### 2. RAGFlow Core: Insecure Deserialization (CVE-2024-12433)
- **Status**: Critical (CVSS 9.8)
- **Component**: RPC Server
- **Vulnerability**: Hard-coded RPC AuthKey combined with insecure `pickle.loads()` deserialization.
- **Risk**: Allows unauthenticated attackers with network access to the RPC port to achieve full RCE.
- **Fixed In**: v0.14.0.

### 3. RAGFlow Core: Dynamic Class Instantiation (CVE-2024-10131)
- **Status**: Critical
- **Component**: `add_llm` function
- **Vulnerability**: Insecure instantiation of LLM classes from user-supplied input.
- **Risk**: Remote Code Execution (RCE).
- **Fixed In**: v0.11.0.

### 4. RAGFlow Core: Authentication Bypass (CVE-2025-69286)
- **Status**: Critical
- **Component**: API Key Management
- **Vulnerability**: Derivable API keys from shared assistant URLs.
- **Risk**: Full account takeover and access to private documents.
- **Fixed In**: v0.22.0.

## Document Parsing Dependency Stack

RAGFlow relies on a multi-format parsing stack, including:
- **PDF**: `pdfplumber`, `PyMuPDF` (fitz)
- **Microsoft Office**: `python-docx`, `python-pptx`, `mammoth`
- **Outlook**: `extract-msg`
- **OCR/Vision**: `onnxruntime`, `paddleocr`

## General Recommendations

1. **Mandatory Upgrade**: Ensure RAGFlow is at version **v0.22.0** or later to mitigate the most severe known RCE and authentication bypass vectors.
2. **Dependency Auditing**: Regularly run `pip audit` or similar tools to check for new CVEs in the document parsing stack, particularly in libraries that handle complex binary formats like `.msg`, `.docx`, and `.pdf`.
3. **Sandboxing**: Execute document parsing workloads in isolated, restricted environments (e.g., Docker containers with minimal filesystem permissions and no network access) to limit the impact of potential zero-day exploits in parsing libraries.
