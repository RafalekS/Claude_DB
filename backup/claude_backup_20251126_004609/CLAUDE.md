- DO NOT LIE or SUGAR COAT!
- Never mark anything complete until it has been tested!

# User Personal Details
Name: Rafal Staska
Organisation: RLS SAP Security Ltd.
Timezone: GMT
Date format: DD/MM/YYYY
Work: Idorsia contractor with email rafal.staska@ext.idorsia.com, username staskra1
Emails: r.staska@gmail.com, r_staska@msn.com
GitHub ID: RafalekS
Git email: r.staska@gmail.com

When calculating token usage, always include:
System tools (~15k),
Reserved buffer (45k)
in addition to Messages - report total context usage, not just conversation tokens.


### For File Tool Parameters (Read/Write/Edit)
- ALWAYS use Windows-style absolute paths with backslashes and drive letters
- Format: `C:\\Users\\r_sta\\file.txt` (note double backslashes in strings)
- This prevents "File has been unexpectedly modified" errors
- Applies to: Read(), Write(), Edit(), NotebookEdit() tool file_path parameters

### For Bash Commands
- ALWAYS use Unix-style paths with forward slashes
- Convert Windows paths: `C:\` becomes `/c/`, `D:\` becomes `/d/`
- Applies to: ALL Bash tool commands (ls, ssh, scp, rsync, cd, etc.)
- Failure to use correct format causes "file not found" errors and password prompts

## File Editing Protocol - CRITICAL

When Write or Edit tool fails with "File has not been read yet" OR "File has been unexpectedly modified":

**Root Cause:** File state tracking bug in Claude Code v1.0.111+ on Windows, often triggered by:
- Path format inconsistencies (mixing forward/backward slashes)
- External file watchers (IDE autosave, format-on-save)
- File state not properly shared between Read/Write/Edit tools

**Protocol:**
1. IMMEDIATELY use Read tool on that exact file path with proper Windows backslash format
2. Then retry Write/Edit with the new content using the same path format
3. DO NOT try bash workarounds (cat, heredoc, echo redirection, Python scripts) for editing source code files
4. If Read→Write still fails after retrying, use Python via Bash as last resort:
   ```bash
   python -c "
   with open('C:/path/to/file.txt', 'r', encoding='utf-8') as f:
       content = f.read()
   content = content.replace('old', 'new')
   with open('C:/path/to/file.txt', 'w', encoding='utf-8') as f:
       f.write(content)
   "
   ```

**Prevention:**
- Always use consistent Windows backslash paths in Read/Write/Edit tool parameters
- Check for IDE file watchers that may interfere (disable autosave/format-on-save if needed)
- Use absolute paths, not relative paths.

## Work Style and Preferences
DO NOT ASSUME file location, settings, names of folders/files or folder structures, variables !!!
Be precise and accurate, check existing memory entities before creating new ones.
Don't say 'fixed' when not tested.

User Values direct, no-nonsense communication and gets frustrated with unnecessary complexity or placeholders
If you don't know or are unsure then ask! I will either tell you or I will ask you to research.
KISS: Keep it Simple Stupid


## Hardware

1.) Personal Laptop:

Name: r_sta@P16-WIN11
OS: Windows 11 Pro x86_64
Host: 21K9CTO1WW (ThinkPad P16s Gen 2)
Kernel: WIN32_NT 10.0.26200.6899 (25H2)
Shell: PowerShell 7.5.4
Display: 1920x1200 in 16"
Terminal: Windows Terminal
CPU: AMD Ryzen 7 PRO 7840U (16) @ 5.13 GHz
GPU: AMD Radeon(TM) 780M @ 0.80 GHz (4.25 GiB) [Integrated]
Memory: 27.67 GiB

2.) Samsung S10 Ultra Tab
3.) Samsung S25+
4.) Xbox Series X  (IP: 192.168.0.101)
5.) Raspberry Pi4  (IP: 192.168.0.94)
6.) Dell Inspiron with Kali Linux
7.) QNAP TS-464 NAS (IP: 192.168.0.166)
Hostname: NAS-RLS
Model: TS-464
CPU: Intel(R) Celeron(R) N5095 @ 2.00GHz, 4 Cores
Graphics: Intel UHD Graphics (16 execution units)
RAM: 16GB

8.) Router Virgin HUB 5  IP Address: 192.168.0.1
