# AI Triage & Discussion Helper

A professional, context-aware GitHub Action that acts as an intelligent maintainer for your open-source projects. Powered by Google Gemini, it handles smart issue labeling, context-aware community support, and anti-spam lifecycle management.

## Key Features

* **Context-Aware Responses (RAG)**: The bot dynamically reads your repository's root `README.md` before answering any issue. It aligns its answers strictly to your documentation, eliminating AI hallucinations and providing accurate, project-specific support.
* **AI Duplicate Detection**: Automatically identifies if a new issue is a duplicate of a recent one using semantic analysis. It links the related issues and applies the `duplicate` label to keep your repository organized.
* **Conversational Mentions**: Users can mention the bot directly (e.g., `@helperbot`) in an issue, discussion, or pull request to ask technical questions, and it will reply instantly.
* **Silent Multi-Label Triage**: Automatically categorizes newly opened issues with up to 5 accurate labels (`bug`, `documentation`, `enhancement`, etc.) without spamming the thread with generic comments.
* **Zombie Auto-Close**: Keep your repository healthy by automatically closing stale issues, pull requests, and discussions that have been inactive for more than 2 years.
* **Smart PR Silence**: Optimized for code review environments; the bot remains silent in Pull Requests unless explicitly mentioned, respecting developer workflows.
* **Zero Cost Architecture**: Programmed specifically to utilize Google's Generative AI Free Tier boundaries by prioritizing Gemini Flash series models.
* **Multi-Language Support**: Fully supports English (`en`) and Spanish (`es`) system contexts and fallback prompts.

## Setup & Installation

To use this action, you must provide a standard GitHub token and a free Google Gemini API Key.

### 1. Get a Free Gemini API Key
Navigate to Google AI Studio, sign in, and generate a free API key. Add this key as a Repository Secret in your GitHub repository named `AI_API_KEY`.

### 2. Configure the GitHub Workflow
Create a new YAML file in your repository under `.github/workflows/ai-triage.yml` and add the following configuration:

```yaml
name: AI Community Maintainer

on:
  issues:
    types: [opened]
  issue_comment:
    types: [created]
  discussion: 
    types: [created]
  discussion_comment: 
    types: [created]
  pull_request:         
    types: [opened, reopened]
  pull_request_review_comment:
    types: [created]     
    
  # TIME TRIGGERS
  schedule:
    - cron: '0 */3 * * *'  # Standard Triage every 3 hours
    - cron: '0 0 1 * *'    # Monthly Zombie Cleanup (1st day of the month)

jobs:
  ai-maintainer:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Run AI Triage Bot
        uses: LautaroOrellano/ai-triage@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          ai-api-key: ${{ secrets.AI_API_KEY }}
          delay-minutes: '180'
          bot-name: 'helperbot'
          language: 'en'
          # Activates auto-close ONLY when triggered by the monthly cron
          auto-close-stale: ${{ github.event.schedule == '0 0 1 * *' && 'true' || 'false' }}
```

## Inputs Configuration

| Input Name | Description | Default | Required |
| --- | --- | --- | --- |
| `github-token` | Your standard secrets.GITHUB_TOKEN to manage issues | N/A | Yes |
| `ai-api-key` | Google Gemini API key mapped from repository secrets | N/A | false |
| `delay-minutes` | Minutes to wait before the bot auto-responds to an abandoned issue | `180` | false |
| `bot-name` | Custom name used for direct mentions (invocations) in strings | `helperbot` | false |
| `language` | Interface fallback language. Supports `en` and `es` | `en` | false |
| `auto-close-stale` | Set to `true` to close inactive issues/PRs/discussions older than 2 years | `false` | false |

## Architecture & Lifecycle

1. **Silent Phase**: When an issue is opened, the action silently categorizes the text, detects potential duplicates, and applies labels dynamically via API without posting any spam comments. 
2. **Mentoring Phase**: If an issue is left abandoned for longer than `delay-minutes`, the cron job sweeps the repository and generates an educated response based on your README context to mentor the user.
3. **Conversational Phase**: Mentioning the bot (e.g. `@helperbot`) bypasses all queues, providing an immediate technical response across Issues, Discussions, and PRs.
4. **Lifecycle Cleanup**: Once a month (or as configured), the bot performs a deep sweep to close "Zombie" threads inactive for more than 2 years, keeping your repository metrics clean.

## License

This project is open-source and is licensed under the [MIT License](LICENSE).
