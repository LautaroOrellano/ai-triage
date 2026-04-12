# Contributing to AI Triage & Discussion Helper

We welcome contributions! This document covers the essentials for contributing to the AI Triage bot. Whether you are fixing bugs, improving the AI prompt, or writing documentation, your help is incredibly valuable.

## Non-Code Contributions
Not a Python coder? You can still help this project grow:
* **Write about the bot** - Blog posts, tutorials, or dev.to articles.
* **Test edge cases** - Try to break the AI Context (RAG) and open detailed issues.
* **Translations** - Map new languages into our `LOCALIZATION` dictionary in `src/bot.py`.
* **Share on Social Media** - Twitter/X, LinkedIn, or Reddit.

## Quick Start (Development)

### Prerequisites
* Python 3.10 or higher.
* A standard GitHub Account & Personal Access Token (`GITHUB_TOKEN`).
* A free Google Gemini API Key (`AI_API_KEY`).

### Setup Commands
```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/ai-triage.git
cd ai-triage

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt
```

### Running Locally
To test the bot locally without running a full GitHub Action yaml, you can mock environment variables:
```bash
# macOS / Linux
export GITHUB_TOKEN="ghp_yourtoken..."
export AI_API_KEY="AIzaSy..."
export GITHUB_REPOSITORY="YOUR_USERNAME/your-test-repo"
export DELAY_MINUTES="180"

# Run the sweep logically
python src/bot.py
```

## Good First Issues
New contributors are encouraged to start with issues labelled `good-first-issue`.
Typical tasks include:
* Adding new fallback translation languages to `bot.py`.
* Parsing new file types in `ai_handler.py` (e.g. `CONTRIBUTING.md`) to increase RAG context.
* Fixing small Python typos or optimizing REST calls.

## Commit Message Format
We follow **Conventional Commits** to enable automated semantic versioning and changelog generation.

### Format
`<type>(<scope>): <subject>`

### Types
* `feat`: A new feature (e.g. adding a new AI model fallback)
* `fix`: A bug fix (e.g. fixing GraphQL variable passing)
* `docs`: Documentation only changes
* `style`: Code formatting (pep8/black)
* `refactor`: A code change that neither fixes a bug nor adds a feature
* `chore`: Changes to build process, workflow actions, etc.

**Examples:**
```bash
git commit -m "feat(ai): integrate gemini-2.0-flash-lite as fallback"
git commit -m "fix(graphql): resolve node_id parsing explicitly"
git commit -m "docs: update CODEOWNERS configuration"
```

## Pull Request Checklist
Before making a PR, please ensure:
- [ ] You tested the action workflow in a private test repo.
- [ ] No hardcoded tokens or secrets are committed.
- [ ] Commit messages follow the Conventional Commits format.
- [ ] Code follows standard PEP8 styles.

## Architectural & API Strategy (Rest vs GraphQL)
Our bot is required to be performant while using minimal API boundaries.

* **Issues API**: We exclusively use REST via `PyGithub`, as it efficiently handles bulk labeling, issue parsing, and REST sweeps.
* **Discussions API**: Since PyGithub natively lacks full Discussion support, we bypass it and use raw **GraphQL Queries** (`requests.post`) for responding to community discussions.

When contributing, ensure you query the correct API endpoint based on the target (Issue vs Discussion).

## Branch Protection & Review
The `main` branch is strictly protected.
All Pull Requests require manual approval by the Code Owner (**@LautaroOrellano**) via the `.github/CODEOWNERS` ruleset before they can be merged. No force-pushes are allowed on `main`.

## Releasing
Releases are seamlessly automated for GitHub Marketplace consumption.

1. Create a `fix` or `feat` commit and push to `main`.
2. Go to GitHub Releases and draft a new version (e.g. `v1.2.0`).
3. Once published, the automated `.github/workflows/release.yml` will automatically move the floating major tag (e.g. `v1`) to the newest commit. 
4. Users using `@v1` in their setups receive the update automatically.
