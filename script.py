import subprocess
import sys
import os
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox

def run_git_command(command, cwd):
    result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip()

def has_origin(cwd):
    out, _ = run_git_command("git remote", cwd)
    return "origin" in out

def has_changes(cwd):
    out, _ = run_git_command("git status --porcelain", cwd)
    return bool(out)

def remote_has_updates(cwd):
    run_git_command("git fetch", cwd)
    local, _ = run_git_command("git rev-parse @", cwd)
    remote, _ = run_git_command("git rev-parse @{u}", cwd)
    base, _ = run_git_command("git merge-base @ @{u}", cwd)

    if local == remote:
        return False
    elif local == base:
        return True
    else:
        return False  # diverged

def sync_git_repo(path, log_fn):
    def log(msg):
        log_fn(msg)

    log(f"📂 Selected repo: {path}")

    # Step 1: Validate Git repo
    out, err = run_git_command("git rev-parse --is-inside-work-tree", path)
    if err or out != "true":
        log("❌ Not a Git repository.")
        return

    # Step 2: Check for remote
    if not has_origin(path):
        log("❌ No remote 'origin' found.")
        log("💡 Use: git remote add origin <repo-url>")
        return

    # Step 3: Fetch and check for updates
    log("🌐 Checking for remote changes...")
    try:
        if remote_has_updates(path):
            log("🔄 Remote has updates. Pulling...")
            pull_out, pull_err = run_git_command("git pull --no-edit", path)
            log(pull_out or pull_err)
            if "CONFLICT" in pull_out or "CONFLICT" in pull_err:
                log("❌ Merge conflict detected. Resolve manually.")
                return
        else:
            log("✅ Remote is up to date.")
    except Exception as e:
        log(f"⚠️ Error checking remote: {e}")
        return

    # Step 4: Local changes?
    if not has_changes(path):
        log("✅ No local changes to commit.")
        return

    log("📌 Local changes detected. Staging files...")
    run_git_command("git add .", path)
    commit_msg = f"Auto commit at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    run_git_command(f'git commit -m "{commit_msg}"', path)

    log("🚀 Pushing to remote...")
    push_out, push_err = run_git_command("git push", path)
    log(push_out or push_err)
    log("✅ Sync completed successfully.")

# --- GUI Code ---
def browse_folder():
    path = filedialog.askdirectory()
    if path:
        repo_path.set(path)

def sync_action():
    path = repo_path.get()
    if not path or not os.path.isdir(path):
        messagebox.showerror("Error", "Please select a valid Git repository folder.")
        return
    log_area.delete('1.0', tk.END)
    sync_git_repo(path, lambda msg: log_area.insert(tk.END, msg + "\n"))

# --- Tkinter GUI ---
root = tk.Tk()
root.title("Git Auto Commit & Push")
root.geometry("700x500")

repo_path = tk.StringVar()

frame = tk.Frame(root)
frame.pack(pady=10)

tk.Label(frame, text="Git Repo Folder:").pack(side=tk.LEFT)
tk.Entry(frame, textvariable=repo_path, width=60).pack(side=tk.LEFT, padx=5)
tk.Button(frame, text="Browse", command=browse_folder).pack(side=tk.LEFT)

tk.Button(root, text="Sync Now", command=sync_action, bg="green", fg="white", padx=20, pady=5).pack(pady=10)

log_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=20)
log_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

root.mainloop()

