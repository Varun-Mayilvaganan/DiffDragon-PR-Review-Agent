import sys
from fetch_pr import fetch_pr_diff
from run_analyzer import run_linting
from llm_review import review_with_llm
from post_review import post_review

def main():
    repo_name = sys.argv[1]  
    pr_number = int(sys.argv[2])

    changes, pr = fetch_pr_diff(repo_name, pr_number)

    all_findings = []
    for file, diff in changes.items():
        # Run static analyzers
        lint_results = run_linting(file)
        all_findings.append(f"### Static Analysis for {file}\n{lint_results}")

        # Run LLM review
        llm_review = review_with_llm(diff)
        all_findings.append(f"### LLM Review for {file}\n{llm_review}")

    # Combine and post
    final_review = "\n\n".join(all_findings)
    post_review(pr, final_review)

if __name__ == "__main__":
    main()
