---
name: ssh
description: Use when working with SSH communication, remote terminals, file transfers, or sending data from Windows to Linux over SSH.
---

CRITICAL — When sending data to a remote Linux system via subprocess.run(..., input=...), NEVER use text mode (encoding='utf-8' or text=True). On Windows, text mode converts `\n` to `\r\n`, which introduces stray `\r` characters on Linux and can corrupt filenames and scripts. ALWAYS encode manually and pass bytes.

Wrong:
subprocess.run(ssh + ['bash','-s'], input=script, encoding='utf-8')

Correct:
subprocess.run(ssh + ['bash','-s'], input=script.encode('utf-8'))

Then decode output manually:
result.stdout.decode('utf-8', errors='replace')

This rule applies to ALL subprocess calls that send input to SSH (scripts, config files, deployments, settings).

For read-only SSH commands (no input= parameter), text mode is acceptable, but always explicitly set encoding='utf-8', errors='replace' because Windows defaults to cp1252, which can corrupt UTF-8 output.

When running SSH from Python on Windows, ALWAYS use `ssh -T` to disable pseudo-terminal allocation. Without `-T`, ssh.exe may hang when stdout/stderr are piped due to PTY allocation attempts.

Minimize sequential SSH connections. Rapid back-to-back SSH calls from Windows can intermittently hang. Batch multiple operations into a single bash script, optionally embed file content via base64, transfer once, and execute once.

For file transfers, DO NOT pipe data via:
ssh host "cat > file"

Piping through SSH stdin on Windows can leave stale connections and cause subsequent SSH calls to hang. Instead: write content to a local temporary file, transfer it via SCP or SFTP to remote `/tmp/`, then execute a separate SSH command to move/chmod as required.

For Python-based SSH, SCP, SFTP, FTP, or Telnet connections, use Paramiko rather than shelling out to ssh.exe unless absolutely necessary.