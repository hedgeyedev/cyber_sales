# Claude Code Extension Specification: Terminal Automation & Auth Framework

**Version:** 1.0
**Status:** Specification (Not Yet Implemented)
**Author:** Forrest Chang
**Date:** November 2025

## Executive Summary

This specification defines a Claude Code extension providing reusable patterns for:
1. **Terminal automation** (iTerm/Terminal.app window/tab management)
2. **Authentication checking** and graceful failure handling
3. **Cross-project command execution** with context preservation
4. **Interactive user flows** requiring authentication refresh

The extension consolidates patterns currently scattered across cultiv-os, cyber_sales, and jira_claude projects into a unified, reusable framework.

## Problem Statement

### Current State

**Pattern Duplication:**
- iTerm automation logic exists in `~/cultiv-os/scripts/open-iterm-tab.scpt`
- Authentication checking is ad-hoc per project
- Cross-project command execution requires manual cd + claude -p patterns
- No standardized way to handle auth failures gracefully

**Pain Points:**
1. **Auth Expiration**: MCP servers (Jira, GitHub, etc.) require periodic re-authentication
2. **Manual Context Switching**: Users must manually open terminals, cd to directories, authenticate
3. **No Reusability**: Each project reimplements terminal launching and auth checking
4. **Poor UX**: Auth failures are abrupt with no recovery flow

### Desired State

**Unified Extension:**
- Single `claude-code-terminal-automation` extension
- Reusable across all projects
- Declarative configuration
- Graceful auth failure handling
- Automatic terminal launching and authentication flows

## Use Cases

### 1. Cross-Project Command Execution (Primary)

**Scenario:** Create Jira issue from cyber_sales conversation

**Current Approach:**
```bash
# Manual steps:
cd ~/work/jira_claude
claude -p "Create issue with description..."
# If auth fails → manually authenticate → retry
```

**With Extension:**
```markdown
<!-- In slash command -->
Use the TerminalAutomation extension:

- Project: jira_claude
- Command: Create issue with description...
- Auth check: jira-mcp
- On auth fail: Launch iTerm, guide user, retry
```

### 2. Scheduled Authentication Refresh

**Scenario:** Daily brief auto-launches projects, some need auth

**Current Approach:**
- Hope authentication is still valid
- User manually fixes if failures occur

**With Extension:**
- Pre-flight auth check before command
- Automatic iTerm launch if auth expired
- User-friendly prompts for re-authentication

### 3. Multi-Project Workflows

**Scenario:** Update GitHub issue, then Jira ticket, then Slack message

**Current Approach:**
- Three separate manual context switches
- Three separate auth checks
- High cognitive overhead

**With Extension:**
- Declarative workflow definition
- Automatic auth checking for each service
- Single interactive session handles all three

## Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────────┐
│ Claude Code Extension: terminal-automation                   │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ Terminal Manager │  │  Auth Checker    │                │
│  │                  │  │                  │                │
│  │ - iTerm          │  │ - MCP servers    │                │
│  │ - Terminal.app   │  │ - CLI tools      │                │
│  │ - Tab/Window mgmt│  │ - Custom checks  │                │
│  └──────────────────┘  └──────────────────┘                │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ Command Executor │  │  Config Manager  │                │
│  │                  │  │                  │                │
│  │ - Cross-project  │  │ - YAML/JSON      │                │
│  │ - Context aware  │  │ - Per-project    │                │
│  │ - Result capture │  │ - Inheritance    │                │
│  └──────────────────┘  └──────────────────┘                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │ Projects (consumers of extension)      │
        │                                        │
        │ - cyber_sales                          │
        │ - jira_claude                          │
        │ - cultiv-ai                            │
        │ - Any future project                   │
        └────────────────────────────────────────┘
```

### Components

#### 1. Terminal Manager

**Responsibility:** Launch and manage terminal windows/tabs

**API:**
```typescript
interface TerminalManager {
  // Open new tab in iTerm/Terminal
  openTab(config: TabConfig): Promise<TabHandle>

  // Execute command in specific directory
  executeInDirectory(dir: string, command: string): Promise<ExecutionResult>

  // Wait for user interaction in terminal
  waitForUserAction(message: string): Promise<void>
}

interface TabConfig {
  directory: string           // Working directory (supports ~)
  command?: string            // Command to execute
  terminal?: 'iterm' | 'terminal' | 'auto'  // Terminal app preference
  newWindow?: boolean         // Open new window vs tab (default: tab)
  focus?: boolean             // Bring terminal to front (default: true)
}

interface TabHandle {
  id: string
  close(): Promise<void>
  sendCommand(command: string): Promise<void>
}

interface ExecutionResult {
  stdout: string
  stderr: string
  exitCode: number
  duration: number
}
```

**Implementation Notes:**
- Uses AppleScript for macOS (iTerm, Terminal.app)
- Graceful fallback if preferred terminal not available
- Path expansion (~ → $HOME)
- Error handling for permission issues

#### 2. Auth Checker

**Responsibility:** Verify authentication status for various services

**API:**
```typescript
interface AuthChecker {
  // Check if auth is valid for a service
  checkAuth(service: string): Promise<AuthStatus>

  // Register custom auth checker
  registerChecker(name: string, checker: AuthCheckFunction): void

  // Get instructions for authenticating
  getAuthInstructions(service: string): string
}

interface AuthStatus {
  valid: boolean
  service: string
  message?: string            // Error or info message
  expires?: Date              // Token expiration if known
  requiresInteractive?: boolean  // Needs user interaction vs background refresh
}

type AuthCheckFunction = () => Promise<AuthStatus>
```

**Built-in Checkers:**
- `jira-mcp` - Check Jira MCP server connectivity
- `github-mcp` - Check GitHub MCP server connectivity
- `generic-mcp` - Generic MCP server health check
- `cli-tool` - Check if CLI tool is authenticated (gh, gcloud, aws, etc.)

**Custom Checkers:**
Projects can define custom auth check logic in their config:
```yaml
auth_checkers:
  my-service:
    type: command
    command: "curl -s https://api.example.com/user"
    success_pattern: "\"authenticated\":\\s*true"
    failure_pattern: "401|403|unauthorized"
```

#### 3. Command Executor

**Responsibility:** Execute commands in different project contexts

**API:**
```typescript
interface CommandExecutor {
  // Execute command in another project
  executeInProject(config: ProjectCommandConfig): Promise<CommandResult>

  // Execute with automatic auth check + retry
  executeWithAuth(config: ProjectCommandConfig, authService: string): Promise<CommandResult>

  // Execute multiple commands in sequence
  executePipeline(commands: ProjectCommandConfig[]): Promise<CommandResult[]>
}

interface ProjectCommandConfig {
  project: string             // Project name or path
  command: string             // Command to execute (can be multi-line)
  type?: 'prompt' | 'interactive' | 'background'
  timeout?: number            // Milliseconds
  captureOutput?: boolean     // Default: true
}

interface CommandResult {
  success: boolean
  output: string
  error?: string
  duration: number
  authRequired?: boolean      // True if failed due to auth
}
```

**Command Types:**
- `prompt` - Execute `claude -p "<prompt>"` (non-interactive)
- `interactive` - Execute `claude -c` (opens session)
- `background` - Execute shell command silently

**Features:**
- Automatic directory resolution (project name → path)
- Output capture and parsing
- Timeout handling
- Auth-aware retries

#### 4. Config Manager

**Responsibility:** Load and merge configuration from multiple sources

**Configuration Hierarchy:**
1. Extension defaults (`~/.claude/extensions/terminal-automation/config.yaml`)
2. Global user config (`~/.claude/terminal-automation.yaml`)
3. Project config (`.claude/terminal-automation.yaml`)

**API:**
```typescript
interface ConfigManager {
  // Load merged configuration for current context
  getConfig(projectPath?: string): TerminalAutomationConfig

  // Get specific service config
  getServiceConfig(serviceName: string): ServiceConfig

  // Validate configuration
  validateConfig(config: TerminalAutomationConfig): ValidationResult
}

interface TerminalAutomationConfig {
  // Terminal preferences
  terminal: {
    preferred: 'iterm' | 'terminal' | 'auto'
    new_window: boolean
    focus_on_launch: boolean
  }

  // Project mappings
  projects: {
    [name: string]: {
      path: string
      default_command?: string
    }
  }

  // Service definitions
  services: {
    [name: string]: ServiceConfig
  }

  // Auth checker definitions
  auth_checkers: {
    [name: string]: AuthCheckerConfig
  }
}

interface ServiceConfig {
  project: string             // Which project hosts this service
  auth_checker: string        // Which auth checker to use
  auth_instructions?: string  // Instructions for user
  retry_count?: number        // Retries before failing (default: 1)
}

interface AuthCheckerConfig {
  type: 'mcp' | 'command' | 'custom'
  command?: string            // For 'command' type
  success_pattern?: string    // Regex for success
  failure_pattern?: string    // Regex for failure
  custom_function?: string    // For 'custom' type (function name)
}
```

### Extension Installation

**Location:** `~/.claude/extensions/terminal-automation/`

**Structure:**
```
~/.claude/extensions/terminal-automation/
├── extension.json           # Extension metadata
├── config.yaml              # Default configuration
├── scripts/
│   ├── open-iterm-tab.scpt  # iTerm automation (from cultiv-os)
│   ├── open-terminal-tab.scpt  # Terminal.app automation
│   └── utils.sh             # Helper scripts
├── lib/
│   ├── terminal-manager.ts  # Terminal Manager implementation
│   ├── auth-checker.ts      # Auth Checker implementation
│   ├── command-executor.ts  # Command Executor implementation
│   └── config-manager.ts    # Config Manager implementation
└── README.md                # Usage documentation
```

**Extension Metadata (`extension.json`):**
```json
{
  "name": "terminal-automation",
  "version": "1.0.0",
  "description": "Terminal automation and authentication framework for Claude Code",
  "author": "Forrest Chang",
  "license": "MIT",
  "permissions": [
    "bash:osascript:*",
    "file:read:~/.claude/terminal-automation.yaml",
    "file:read:.claude/terminal-automation.yaml"
  ],
  "entry_point": "lib/index.ts",
  "dependencies": []
}
```

## Configuration Examples

### Global Config (~/.claude/terminal-automation.yaml)

```yaml
# Terminal preferences
terminal:
  preferred: iterm          # iterm, terminal, auto
  new_window: false         # Open new window vs tab
  focus_on_launch: true     # Bring to front when launching

# Project mappings (name → path)
projects:
  jira_claude:
    path: ~/work/jira_claude
    default_command: claude -c

  github_ops:
    path: ~/work/github-ops
    default_command: claude -c

  cyber_sales:
    path: ~/work/cyber_sales
    default_command: ./refresh_analysis.sh

# Service definitions
services:
  jira:
    project: jira_claude
    auth_checker: jira-mcp
    auth_instructions: |
      Authenticate with Jira by:
      1. Following prompts in the terminal
      2. Entering your Atlassian email
      3. Providing API token from https://id.atlassian.com/manage/api-tokens
    retry_count: 1

  github:
    project: github_ops
    auth_checker: github-mcp
    auth_instructions: |
      Authenticate with GitHub:
      1. Follow the device flow prompts
      2. Visit the provided URL
      3. Enter the code shown
    retry_count: 1

# Auth checker definitions
auth_checkers:
  jira-mcp:
    type: command
    command: cd ~/work/jira_claude && claude -p "List first epic you can find"
    success_pattern: "\\w+-\\d+"  # Jira issue key format
    failure_pattern: "401|403|unauthorized|authentication"

  github-mcp:
    type: command
    command: cd ~/work/github_ops && claude -p "Get current authenticated user"
    success_pattern: "login|username"
    failure_pattern: "401|403|unauthorized|authentication"
```

### Project Config (.claude/terminal-automation.yaml)

Example for cyber_sales project:

```yaml
# Extend/override global config for this project

# This project's external service dependencies
external_services:
  - jira              # For creating issues
  - github            # For pushing reports

# Custom workflows
workflows:
  create_jira_issue:
    steps:
      - name: Check Jira auth
        type: auth_check
        service: jira

      - name: Create issue
        type: command
        project: jira_claude
        command: "Create issue: {{description}}"

      - name: Report result
        type: report
        template: "✅ Created {{issue_key}}"

  publish_reports:
    steps:
      - name: Generate reports
        type: command
        project: cyber_sales
        command: ./package_reports.sh

      - name: Commit to GitHub
        type: command
        project: cyber_sales
        command: git add reports/*.html && git commit -m "Update reports"

      - name: Push
        type: command
        project: cyber_sales
        command: git push
```

## Usage Patterns

### Pattern 1: Simple Cross-Project Command

**Slash command content:**
```markdown
Execute command in jira_claude project:

Use extension: terminal-automation

- Project: jira_claude
- Command: Create issue with title "{{title}}" and description "{{description}}"
- Auth check: jira
- On auth fail: interactive
```

**Extension behavior:**
1. Resolve project path (jira_claude → ~/work/jira_claude)
2. Check auth (jira-mcp checker)
3. If auth valid:
   - Execute `claude -p "Create issue..."` in ~/work/jira_claude
   - Capture and return output
4. If auth invalid:
   - Launch iTerm to ~/work/jira_claude with `claude -c`
   - Display auth instructions to user
   - Wait for user confirmation
   - Retry auth check
   - Execute command

### Pattern 2: Multi-Service Workflow

**Slash command content:**
```markdown
Execute workflow: publish_reports (from cyber_sales project config)

Use extension: terminal-automation

- Workflow: publish_reports
- Interactive: true
```

**Extension behavior:**
1. Load workflow definition from cyber_sales/.claude/terminal-automation.yaml
2. Execute each step in sequence:
   - Generate reports (local command)
   - Check GitHub auth before commit
   - If auth needed → launch iTerm, wait for auth
   - Commit and push

### Pattern 3: Scheduled Auth Refresh

**In daily-brief.md:**
```markdown
Before auto-launching projects, check authentication:

Use extension: terminal-automation

- Operation: check_auth_for_services
- Services: [jira, github, slack]
- Auto-refresh: true
- Report: brief
```

**Extension behavior:**
1. Check auth for all listed services in parallel
2. For any that need refresh:
   - Launch iTerm to appropriate project
   - Show auth instructions
   - Wait for completion
3. Summarize in brief:
   ```
   🔐 Authentication Status:
   - Jira: ✅ Valid until Nov 15
   - GitHub: ✅ Valid (no expiration)
   - Slack: ⚠️ Refreshed (was expired)
   ```

## API Reference for Slash Commands

### Execute in Project

```markdown
<!-- In any slash command -->

Use extension: terminal-automation

Operation: execute
Project: jira_claude
Command: |
  Create a Jira issue with these details:
  - Summary: {{summary}}
  - Description: {{description}}
Auth check: jira
Interactive: false
```

### Check Authentication

```markdown
Use extension: terminal-automation

Operation: check_auth
Service: jira
Auto-refresh: true
```

### Execute Workflow

```markdown
Use extension: terminal-automation

Operation: workflow
Workflow: publish_reports
Project: cyber_sales
Variables:
  report_date: {{today}}
  format: html
```

### Launch Terminal

```markdown
Use extension: terminal-automation

Operation: launch_terminal
Project: jira_claude
Command: claude -c
Instructions: |
  Please authenticate with Jira in the opened terminal,
  then return here to continue.
```

## Migration from Existing Patterns

### From cultiv-os Scripts

**Before:**
```bash
# In slash command
Run command:
osascript ~/cultiv-os/scripts/open-iterm-tab.scpt "$HOME/work/jira_claude" "claude -c"
```

**After:**
```markdown
Use extension: terminal-automation

Operation: launch_terminal
Project: jira_claude
Command: claude -c
```

**Benefits:**
- No hardcoded paths
- Works on any system (extension handles OS differences)
- Graceful error handling
- Logging and debugging

### From Ad-hoc Auth Checking

**Before:**
```bash
# Try command, hope it works
cd ~/work/jira_claude && claude -p "Create issue..."

# If fails, user manually fixes
```

**After:**
```markdown
Use extension: terminal-automation

Operation: execute_with_auth
Project: jira_claude
Command: Create issue...
Auth check: jira
```

**Benefits:**
- Automatic pre-flight check
- Graceful auth failure handling
- User-friendly prompts
- Automatic retry after auth

### From Manual Context Switching

**Before:**
```markdown
<!-- In /create-jira command -->
1. User runs /create-jira in cyber_sales
2. Command displays prompt to paste
3. User manually: cd ~/work/jira_claude
4. User runs: claude -p "<pasted prompt>"
5. User copies result back
```

**After:**
```markdown
<!-- In /create-jira command -->
Use extension: terminal-automation

Operation: execute_with_auth
Project: jira_claude
Command: {{generated_prompt}}
Auth check: jira
Capture output: true

<!-- Extension handles everything automatically -->
```

**Benefits:**
- No manual context switching
- No copy-paste errors
- Automatic output capture
- Better UX

## Implementation Roadmap

### Phase 1: Core Infrastructure (Week 1)
- [ ] Extension scaffolding and registration
- [ ] Config Manager implementation
- [ ] Terminal Manager (iTerm + Terminal.app support)
- [ ] Basic AppleScript integration (migrate from cultiv-os)

### Phase 2: Auth Framework (Week 2)
- [ ] Auth Checker interface and built-in checkers
- [ ] MCP server health checking
- [ ] CLI tool auth detection
- [ ] Custom auth checker registration

### Phase 3: Command Execution (Week 3)
- [ ] Command Executor implementation
- [ ] Cross-project command routing
- [ ] Output capture and parsing
- [ ] Error handling and retries

### Phase 4: Integration (Week 4)
- [ ] Update /create-jira to use extension
- [ ] Update /daily-brief to use extension
- [ ] Migrate cultiv-os patterns to extension
- [ ] Documentation and examples

### Phase 5: Advanced Features (Week 5+)
- [ ] Workflow engine
- [ ] Pipeline execution
- [ ] Parallel command execution
- [ ] Result aggregation and reporting
- [ ] Auth status dashboard
- [ ] Token expiration tracking

## Success Metrics

**Adoption:**
- [ ] 3+ projects using extension within 1 month
- [ ] 10+ slash commands using extension patterns

**Reliability:**
- [ ] <1% auth check failure rate
- [ ] <2 second terminal launch latency
- [ ] 95%+ automatic auth refresh success

**UX Improvement:**
- [ ] 80% reduction in manual context switching
- [ ] 90% reduction in auth failure friction
- [ ] User reports "seamless" cross-project workflows

## Open Questions

1. **Windows/Linux Support:** Should initial version support non-macOS platforms?
   - **Recommendation:** Start macOS-only (iTerm/Terminal.app), add Windows Terminal + tmux in Phase 6

2. **Security:** How to handle sensitive credentials in config?
   - **Recommendation:** Never store credentials; only store project paths and service names

3. **Extension Discovery:** How do slash commands discover the extension?
   - **Recommendation:** Explicit "Use extension: terminal-automation" syntax (like function calling)

4. **Versioning:** How to handle breaking changes?
   - **Recommendation:** Semantic versioning + migration guides + deprecation warnings

5. **Distribution:** How should users install the extension?
   - **Recommendation:**
     - Manual: Clone to ~/.claude/extensions/terminal-automation/
     - Future: Claude Code extension marketplace

## References

**Existing Implementations:**
- cultiv-os iTerm launcher: `~/cultiv-os/scripts/open-iterm-tab.scpt`
- cultiv-os schedule system: `~/cultiv-os/schedule.yaml`
- /daily-brief auto-launch: `~/work/cultiv-ai/commands/daily-brief.md`

**Related Specifications:**
- Claude Code Extension API: (To be documented by Anthropic)
- MCP Server Protocol: https://modelcontextprotocol.org/

**Inspiration:**
- VS Code Remote Development: https://code.visualstudio.com/docs/remote/remote-overview
- Tmux session management: https://github.com/tmux/tmux/wiki
- iTerm2 Python API: https://iterm2.com/python-api/

---

**Next Steps:**
1. Review this spec with team
2. Prototype Terminal Manager + Auth Checker (Phase 1)
3. Test with /create-jira command
4. Iterate based on real-world usage
5. Expand to other projects (cultiv-ai, github-ops, etc.)

**Maintainer:** Forrest Chang <forrest@example.com>
**Last Updated:** November 12, 2025
