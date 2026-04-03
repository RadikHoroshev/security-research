from mcp.server.fastmcp import FastMCP

mcp = FastMCP("AgentBridge")

@mcp.tool()
def run_gemini_task(prompt: str, output_file: str) -> str:
    """Run Gemini CLI task and save result to file"""
    import subprocess
    import os
    
    cmd = f'export PATH="/opt/homebrew/bin:$PATH" && gemini -p "{prompt}" --yolo'
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
        with open(output_file, 'w') as f:
            f.write(result.stdout)
        return f"Task completed. Output saved to {output_file}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def run_qwen_task(prompt: str, output_file: str) -> str:
    """Run Qwen (Ollama) task and save result to file"""
    import subprocess
    import json
    
    cmd = f'''curl -s http://localhost:11434/api/generate -d '{{
        "model": "qwen2.5-coder:14b",
        "prompt": "{prompt}",
        "stream": false
    }}' '''
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        with open(output_file, 'w') as f:
            f.write(result.stdout)
        return f"Qwen task completed. Output saved to {output_file}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def read_file(filepath: str) -> str:
    """Read file content"""
    try:
        with open(filepath, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

if __name__ == "__main__":
    print(">>> Starting Agent Bridge MCP Server...")
    print(">>> Tools: run_gemini_task, run_qwen_task, read_file")
    mcp.run()
