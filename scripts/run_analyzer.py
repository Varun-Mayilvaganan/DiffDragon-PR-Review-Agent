import subprocess

def run_linting(file_path: str):
    results = {}
    # Run flake8
    flake8 = subprocess.run(["flake8", file_path], capture_output=True, text=True)
    results["flake8"] = flake8.stdout.strip()

    # Run pylint
    pylint = subprocess.run(["pylint", file_path, "--score=n"], capture_output=True, text=True)
    results["pylint"] = pylint.stdout.strip()

    # Run bandit (security)
    bandit = subprocess.run(["bandit", "-q", "-r", file_path], capture_output=True, text=True)
    results["bandit"] = bandit.stdout.strip()

    return results
