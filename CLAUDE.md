# CLAUDE.md — Cowork-Local v3.1

## Operation Modes

### COWORK MODE (prefix "cowork:")
Full autonomous graph. DeepSeek plans → Qwen3 generates → pytest validates → DeepSeek reviews → loop decides.
Execute: ./apps/cli/loop.sh "task"

### CODE MODE (default)
DeepSeek generates code, explains, analyzes. Not conversational chat.

## Rules
- Prioritize code generation over explanations
- Do not modify files without asking
- Use absolute paths: /media/SSD1T/cowork-local/
- When user asks to create/generate code, use ./apps/cli/loop.sh

## Tools

### Code Generation
- ./apps/cli/loop.sh "task" → full autonomous graph
- python apps/cli/execute_command.py write-file /path → create file (stdin)
- python apps/cli/execute_command.py write-json /path → create file (JSON)
- python apps/cli/cowork_graph.py "task" → direct graph

### Search
- python apps/cli/search_tools.py search "query" → grep code
- python apps/cli/search_tools.py find "*.py" → find files
- python apps/cli/search_tools.py modules → list modules

### Code Manipulation
- python apps/cli/apply_diff.py change file "old" "new" → replace text
- python apps/cli/apply_diff.py line file N "new" → replace line

### Memory
- python apps/cli/session_memory.py save "query" → save session
- python apps/cli/session_memory.py load 5 → load history

### AI Skills (via MCP Skills Server)
- generate_tests: Generate pytest unit tests for code
- review_code: Review code for bugs, performance, best practices
- generate_docs: Generate docstrings and documentation
- generate_pdf: Create formatted PDF documents
- generate_excel: Create formatted Excel files
- generate_pptx: Create PowerPoint presentations
- generate_chart: Create charts (bar, line, pie)
- web_search: Search the web via DuckDuckGo
