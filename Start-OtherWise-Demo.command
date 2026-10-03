#!/bin/zsh
task_repo_dir="$(cd -- "$(dirname -- "$0")" && pwd)"
"$task_repo_dir/.venv/bin/python" "$task_repo_dir/scripts/start_demo.py"
task_exit_code=$?
print "Press Return to close this window."
read -r
exit "$task_exit_code"
