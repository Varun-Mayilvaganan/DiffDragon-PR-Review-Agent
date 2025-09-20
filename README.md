# DiffDragon-PR-Review-Agent
An AI-powered assistant that reviews pull requests, catches issues, and helps ensure clean, reliable code before merging.

Quick start (local):
1. `pip install -r requirements.txt`
2. Set env vars:
   - `GITHUB_TOKEN` (with repo write)
   - `GEMINI_API_KEY`
   - optional: `GEMINI_MODEL` (default: gemini-1.5-flash)
3. Run: `python -m pr_agent.cli owner/repo 123`

GitHub Actions:
- Add repo secret `GEMINI_API_KEY`
- The workflow passes `${{ github.repository }}` and `${{ github.event.pull_request.number }}`