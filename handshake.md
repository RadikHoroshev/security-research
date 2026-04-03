# 🤖 TASK: Agent Connectivity Check (Handshake)

**Executor:** Agent IDE (Qwen)
**Context:** We need to verify that the Orchestrator (Goose) and other Agents (Gemini, Jules) are reachable.

## 📋 INSTRUCTIONS FOR AGENT IDE

Please execute the following steps strictly in order. Do not ask the user for permission (assume YOLO mode).

### Step 0: Setup

Ensure results directory exists:

```bash
mkdir -p /Users/code/project/intel/results
```

### Step 1: Test Gemini CLI

1. **Execute Command:**
   Run the following shell command to test if Gemini CLI is responsive:

   ```bash
   export PATH="/opt/homebrew/bin:$PATH" && \
   gemini -p "Write 'GEMINI_OK' into file /Users/code/project/intel/results/conn_gemini.txt" --yolo
   ```

2. **Verify:**
   Read the file `/Users/code/project/intel/results/conn_gemini.txt`.
   - If it contains "GEMINI_OK", set status: **SUCCESS**.
   - If file missing or empty, set status: **FAIL**.

### Step 2: Test Jules CLI (Session-based)

**Note:** Jules is an asynchronous agent that works with git repositories and sessions.

1. **Change to git repository:**

   ```bash
   cd /Users/code/project/intel
   ```

2. **Create Jules session:**

   ```bash
   jules new "Create file results/conn_jules.txt with content JULES_OK"
   ```

   This will either:
   - Open TUI (text interface), or
   - Create a background session with ID

3. **Wait for completion** (10-15 seconds)

4. **Get session ID:**
   ```bash
   jules remote list
   ```
5. **Pull result:**

   ```bash
   jules remote pull --session <SESSION_ID> --apply
   ```

6. **Verify:**
   Read the file `/Users/code/project/intel/results/conn_jules.txt`.
   - If it contains "JULES_OK", set status: **SUCCESS**.
   - If file missing or empty, set status: **FAIL**.

### Step 3: Final Report

1. **Write Log:**
   Append the results to `/Users/code/project/intel/CHRONICLE.md`:

   ```text
   [TIMESTAMP] Agent IDE executed Handshake. Gemini: [RESULT], Jules: [RESULT].
   ```

2. **Create Report File:**
   Write JSON to `/Users/code/project/intel/results/handshake_report.json`:

   ```json
   {
     "gemini": "PASS|FAIL",
     "jules": "PASS|FAIL",
     "timestamp": "YYYY-MM-DDTHH:MM:SS",
     "executor": "Agent IDE (Qwen)"
   }
   ```

3. **Output to Console:**
   Print a summary of which agents responded and which failed.
