from github import Github

class GitHubClient:
    def __init__(self, token):
        self.gh = Github(token)
        self.repo = self.gh.get_repo(self._get_repo())

    def _get_repo(self):
        import os
        return os.getenv("GITHUB_REPOSITORY")

    def get_open_issues(self):
        return self.repo.get_issues(state='open')

    def add_label(self, issue_number, label_name):
        # Create label if it doesn't exist
        try:
            self.repo.get_label(label_name)
        except:
            self.repo.create_label(name=label_name, color="0052cc")
            
        issue = self.repo.get_issue(issue_number)
        issue.add_to_labels(label_name)

    def has_label(self, issue_number, label_name):
        issue = self.repo.get_issue(issue_number)
        labels = [l.name for l in issue.get_labels()]
        return label_name in labels

    def get_comments(self, issue_number):
        issue = self.repo.get_issue(issue_number)
        return list(issue.get_comments())

    def get_bot_username(self):
        try:
            return self.gh.get_user().login
        except:
            # Fallback for GITHUB_TOKEN which can't access /user
            return "github-actions[bot]"

    def already_commented(self, issue_number):
        bot_user = self.get_bot_username()
        comments = self.get_comments(issue_number)
        return any(c.user.login == bot_user for c in comments)

    def comment(self, issue_number, message):
        issue = self.repo.get_issue(issue_number)
        issue.create_comment(message)
