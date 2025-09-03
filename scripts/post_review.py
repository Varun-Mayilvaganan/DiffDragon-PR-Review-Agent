def post_review(pr, review_text: str):
    pr.create_issue_comment(review_text)
