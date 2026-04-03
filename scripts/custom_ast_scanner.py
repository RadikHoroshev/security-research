import ast
import json
import os
import sys

class SecurityScanner(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename
        self.findings = []
        self.source_lines = []
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.source_lines = f.readlines()
        except Exception:
            pass

    def get_snippet(self, lineno):
        if 1 <= lineno <= len(self.source_lines):
            return self.source_lines[lineno-1].strip()
        return ""

    def is_static_arg(self, node):
        """Check if an argument is a literal (string, bytes, number)."""
        return isinstance(node, (ast.Constant, ast.Str, ast.Bytes, ast.Num))

    def visit_Call(self, node):
        # 1. os.system or subprocess calls
        if isinstance(node.func, ast.Attribute):
            # os.system(...)
            if isinstance(node.func.value, ast.Name) and node.func.value.id == 'os' and node.func.attr == 'system':
                if node.args and not self.is_static_arg(node.args[0]):
                    self.findings.append({
                        "file": self.filename,
                        "line": node.lineno,
                        "vuln_type": "os.system with dynamic argument",
                        "code_snippet": self.get_snippet(node.lineno)
                    })
            
            # subprocess.run, Popen, call, check_call, check_output
            elif isinstance(node.func.value, ast.Name) and node.func.value.id == 'subprocess':
                if node.func.attr in ['run', 'Popen', 'call', 'check_call', 'check_output']:
                    if node.args and not self.is_static_arg(node.args[0]):
                        self.findings.append({
                            "file": self.filename,
                            "line": node.lineno,
                            "vuln_type": f"subprocess.{node.func.attr} with dynamic argument",
                            "code_snippet": self.get_snippet(node.lineno)
                        })

            # 3. pickle.loads
            elif isinstance(node.func.value, ast.Name) and node.func.value.id == 'pickle' and node.func.attr == 'loads':
                self.findings.append({
                    "file": self.filename,
                    "line": node.lineno,
                    "vuln_type": "pickle.loads (insecure deserialization)",
                    "code_snippet": self.get_snippet(node.lineno)
                })

        # 2. eval() or exec() calls
        elif isinstance(node.func, ast.Name):
            if node.func.id in ['eval', 'exec']:
                self.findings.append({
                    "file": self.filename,
                    "line": node.lineno,
                    "vuln_type": f"{node.func.id}() call",
                    "code_snippet": self.get_snippet(node.lineno)
                })

        self.generic_visit(node)

def scan_directory(root_dir):
    all_findings = []
    ignore_dirs = {'tests', 'docker', '__pycache__', '.git'}

    for root, dirs, files in os.walk(root_dir):
        # In-place directory filtering
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        tree = ast.parse(f.read(), filename=file_path)
                    
                    scanner = SecurityScanner(file_path)
                    scanner.visit(tree)
                    all_findings.extend(scanner.findings)
                except Exception as e:
                    # Skip files with syntax errors or encoding issues
                    pass

    return all_findings

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python custom_ast_scanner.py <directory_to_scan>")
        sys.exit(1)

    target_dir = sys.argv[1]
    if not os.path.isdir(target_dir):
        print(f"Error: {target_dir} is not a directory.")
        sys.exit(1)

    results = scan_directory(target_dir)
    print(json.dumps(results, indent=2))
