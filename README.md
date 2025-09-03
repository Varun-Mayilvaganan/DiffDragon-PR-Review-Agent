```markdown
# 🤖 DiffDragon: PR Review Agent  

DiffDragon is an **AI-powered Pull Request Reviewer** that automates code review by combining:  
- ✅ **Static analyzers** (linting & style checks)  
- 🤖 **LLM-based reviews** (via LangChain + Gemini/OpenAI)  
- ⚡ **GitHub Actions automation**  

The goal is to **improve code quality** by giving fast, consistent, and intelligent feedback on every PR.  

---

## 🚀 Features
- Fetches **PR diffs & metadata** from GitHub  
- Runs **linting & static analysis** on changed files  
- Uses an **LLM** to check for:
  - Bugs  
  - Security issues  
  - Readability & maintainability  
- Posts a **consolidated review comment** directly on the PR  
- Fully integrated with **GitHub Actions** for automation  

---

## 📂 Project Structure
```

pr-review-agent/
│── scripts/
│   ├── fetch\_pr.py         # Fetch PR diffs & metadata
│   ├── run\_analyzers.py    # Run linting & static checks
│   ├── llm\_review\.py       # LLM-powered code review (LangChain + Gemini/OpenAI)
│   ├── post\_review\.py      # Post consolidated review to GitHub
│   └── main.py             # Orchestration script
│
│── requirements.txt        # Python dependencies
│── .github/
│   └── workflows/
│       └── pr-review\.yml   # GitHub Action for auto-review
│
└── README.md               # Project documentation

````

---

## 🛠️ Setup & Usage

### 1. Clone the repo
```bash
git clone https://github.com/Varun-Mayilvaganan/DiffDragon-PR-Review-Agent.git
cd DiffDragon-PR-Review-Agent
````

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set environment variables

You’ll need:

* `GITHUB_TOKEN` → GitHub Personal Access Token
* `GEMINI_API_KEY` (or `OPENAI_API_KEY`) → for LLM reviews

Example:

```bash
export GITHUB_TOKEN=your_github_token
export GEMINI_API_KEY=your_gemini_key
```

On Windows PowerShell:

```powershell
setx GITHUB_TOKEN "your_github_token"
setx GEMINI_API_KEY "your_gemini_key"
```

### 5. Run locally

```bash
python scripts/main.py <repo_name> <pr_number>
```

Example:

```bash
python scripts/main.py Varun-Mayilvaganan/DiffDragon-PR-Review-Agent 5
```

---

## ⚡ GitHub Actions (Auto Reviews)

This project comes with `.github/workflows/pr-review.yml`.
When a Pull Request is opened, the bot will automatically:

1. Fetch PR changes
2. Run analyzers
3. Call the LLM reviewer
4. Post the review as a comment

---

## 📌 Roadmap

* [ ] Inline PR comments instead of a single block
* [ ] Support for more analyzers (bandit, mypy, etc.)
* [ ] Organization-wide rules enforcement
* [ ] Option to self-host with open-source LLMs

---

## 🤝 Contributing

Contributions are welcome!
Feel free to fork this repo, open issues, or submit PRs.

---