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

    # --- GRAPHQL ADDITIONS FOR DISCUSSIONS ---
    def graphql_query(self, query, variables=None):
        import requests
        import os
        url = "https://api.github.com/graphql"
        headers = {
            "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
            "Content-Type": "application/json"
        }
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        response = requests.post(url, json=payload, headers=headers)
        return response.json()

    def comment_discussion(self, node_id, message):
        query = """
        mutation($discussionId: ID!, $body: String!) {
          addDiscussionComment(input: {discussionId: $discussionId, body: $body}) {
            clientMutationId
          }
        }
        """
        self.graphql_query(query, {"discussionId": node_id, "body": message})

    def get_label_node_id(self, label_name):
        owner, repo_name = self._get_repo().split('/')
        query = """
        query($owner: String!, $repo: String!, $query: String!) {
          repository(owner: $owner, name: $repo) {
            labels(query: $query, first: 1) {
              nodes { id }
            }
          }
        }
        """
        res = self.graphql_query(query, {"owner": owner, "repo": repo_name, "query": label_name})
        nodes = res.get("data", {}).get("repository", {}).get("labels", {}).get("nodes", [])
        if nodes:
            return nodes[0]["id"]
            
        try:
            label = self.repo.create_label(name=label_name, color="0052cc")
            return label.node_id
        except:
            return self.repo.get_label(label_name).node_id

    def add_label_to_node(self, target_node_id, label_name):
        label_node_id = self.get_label_node_id(label_name)
        query = """
        mutation($labelableId: ID!, $labelIds: [ID!]!) {
          addLabelsToLabelable(input: {labelableId: $labelableId, labelIds: $labelIds}) {
            clientMutationId
          }
        }
        """
        self.graphql_query(query, {"labelableId": target_node_id, "labelIds": [label_node_id]})

    def get_open_discussions(self):
        owner, repo_name = self._get_repo().split('/')
        query = """
        query($owner: String!, $repo: String!) {
          repository(owner: $owner, name: $repo) {
            discussions(first: 50, states: OPEN) {
              nodes {
                id
                title
                body
                createdAt
                comments(first: 50) {
                  nodes { author { login } }
                }
                labels(first: 20) {
                  nodes { name }
                }
              }
            }
          }
        }
        """
        res = self.graphql_query(query, {"owner": owner, "repo": repo_name})
        try:
            return res["data"]["repository"]["discussions"]["nodes"]
        except:
            return []
