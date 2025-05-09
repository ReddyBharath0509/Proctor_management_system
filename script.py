import subprocess
import sys

def run_git_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip()

def has_changes():
    out, _ = run_git_command("git status --porcelain")
    return bool(out)

def has_origin():
    out, _ = run_git_command("git remote")
    return "origin" in out

def main():
    print("🔍 Checking for changes...")

    # Check if in a git repo
    out, err = run_git_command("git rev-parse --is-inside-work-tree")
    if err or out != "true":
        print("❌ Not a Git repository. Please run this inside a Git project folder.")
        sys.exit(1)

    if not has_changes():
        print("✅ No changes to commit.")
        return

    print("📌 Changes detected. Staging...")
    run_git_command("git add .")

    from datetime import datetime
    commit_msg = f"Auto commit at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    run_git_command(f'git commit -m "{commit_msg}"')

    if not has_origin():
        print("❌ No remote repository found.")
        print("💡 Use: git remote add origin <your-repo-url>")
        return

    print("📤 Pulling latest changes...")
    pull_out, pull_err = run_git_command("git pull --no-edit")
    if "CONFLICT" in pull_out or "CONFLICT" in pull_err:
        print("❌ Merge conflict detected. Please resolve manually.")
        return

    print("🚀 Pushing to origin...")
    run_git_command("git push")
    print("✅ Push completed successfully.")

if __name__ == "__main__":
    main()
