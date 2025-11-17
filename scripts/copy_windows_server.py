import pathlib
import shutil
import subprocess
import sys
import textwrap

PROJECT_ROOT = pathlib.Path(r"C:\\Users\\393\\Desktop\\Smart AI Trading Strategy Optimizer")
TARGET_ROOT = pathlib.Path(r"D:\\Deployments\\SmartAITradingStrategyOptimizer")
ZIP_PATH = TARGET_ROOT.with_suffix(".zip")

EXCLUDE = {
    "__pycache__",
    ".git",
    ".venv",
    "node_modules",
    ".mypy_cache",
    ".pytest_cache",
    ".idea",
    ".vs",
}


def ignore_dirs(_, names):
    return {name for name in names if name in EXCLUDE}


def ensure_target():
    if TARGET_ROOT.exists():
        raise SystemExit(f"Target '{TARGET_ROOT}' already exists. Remove or choose a new path.")
    TARGET_ROOT.parent.mkdir(parents=True, exist_ok=True)


def copy_project():
    shutil.copytree(PROJECT_ROOT, TARGET_ROOT, ignore=ignore_dirs)
    print(f"Project copied to: {TARGET_ROOT}")


def create_zip():
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    shutil.make_archive(TARGET_ROOT.as_posix(), "zip", root_dir=TARGET_ROOT)
    print(f"Created archive: {ZIP_PATH}")


def write_setup_notes():
    notes = textwrap.dedent(
        f"""
        === Deployment Notes for Windows Server 2022 ===

        1. Prerequisites
           - Install Python 3.11+ from https://www.python.org/downloads/windows/
           - Ensure 'python' and 'pip' are on PATH (check with `python --version`)
           - Install Git if the project depends on submodules (https://git-scm.com/download/win)
           - Install any required system packages listed in documentation

        2. Unpack the archive
           - Copy '{ZIP_PATH}' to the server (e.g. via RDP, SMB, or WinSCP)
           - Extract contents to desired location, e.g. `C:\Apps\SmartAI`

        3. Python Environment
           - Open Windows Terminal (PowerShell) as Administrator if elevated privileges are needed
           - cd into project directory: `cd C:\Apps\SmartAI`
           - Create virtual environment: `python -m venv .venv`
           - Activate it: `.venv\Scripts\Activate`
           - Upgrade pip: `python -m pip install --upgrade pip`
           - Install dependencies: `pip install -r requirements.txt`

        4. Additional Services (optional)
           - If there is a Node.js frontend, install Node.js LTS and run `npm install`
           - For task schedulers or services, use Windows Task Scheduler or NSSM to wrap scripts

        5. Configuration
           - Duplicate `.env.example` to `.env` and adjust values for the server (API keys, DB credentials, etc.)
           - Ensure any external resources (databases, message brokers) are reachable from the server

        6. Running the Application
           - Follow project README instructions (`python main.py`, `uvicorn app:app`, etc.)
           - For production, consider using `pip install gunicorn` (if WSL) or `waitress` for Windows services

        7. Post-Deployment Checklist
           - Configure Windows Firewall rules for required ports
           - Enable backups of the deployment directory and logs
           - Set up monitoring and logging (e.g. Windows Event Viewer, custom log files)

        8. Updating
           - Repeat copy/zip process on development machine or pull from Git on the server
           - Re-run dependency installation if requirements changed

        """
    )
    notes_path = TARGET_ROOT / "WINDOWS_SERVER_2022_SETUP.txt"
    notes_path.write_text(notes, encoding="utf-8")
    print(f"Wrote deployment notes to: {notes_path}")


def main():
    if not PROJECT_ROOT.exists():
        raise SystemExit(f"Project root '{PROJECT_ROOT}' not found.")
    ensure_target()
    copy_project()
    write_setup_notes()
    create_zip()
    print("Done. Transfer the zip to Windows Server 2022 and follow the setup notes.")


if __name__ == "__main__":
    if sys.platform != "win32":
        raise SystemExit("Run this script on a Windows host where the project is located.")
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}")
        subprocess.call("pause", shell=True)
