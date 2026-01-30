import subprocess

def run_command(cmd):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        return result.stdout.strip() if result.returncode == 0 else f"Error: {result.stderr}"
    except Exception as e:
        return f"Exception: {str(e)}"

def main():
    print("🚀 --- GIT SUMMARY SKILL ---")

    # Aktuální větev
    branch = run_command("git rev-parse --abbrev-ref HEAD")
    print(f"📍 Aktuální větev: {branch}")

    # Posledních 5 commitů (zkráceně)
    print("\n📜 Posledních 5 změn:")
    logs = run_command("git log -5 --pretty=format:'%h - %s (%cr)'")
    print(logs)

    # Stav (unstaged changes)
    print("\n🔍 Status souborů:")
    status = run_command("git status -s")
    if not status:
        print("Vše je čisté.")
    else:
        print(status)

    print("\n--- KONEC PŘEHLEDU ---")

if __name__ == "__main__":
    main()
