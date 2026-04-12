# AI Triage & Discussion Helper

A professional, context-aware GitHub Action that acts as an intelligent maintainer for your open-source projects. Powered by Google Gemini, it handles smart issue labeling, context-aware community support, and anti-spam lifecycle management.

## Key Features

* **Context-Aware Responses (RAG)**: The bot dynamically reads your repository's root `README.md` before answering any issue. It aligns its answers strictly to your documentation, eliminating AI hallucinations and providing accurate, project-specific support.
* **Conversational Mentions**: Users can mention the bot directly (e.g., `@helperbot`) in an issue or discussion comment to ask technical questions, and it will reply instantly. Custom bot names are fully supported.
* **Silent Multi-Label Triage**: Automatically categorizes newly opened issues with up to 5 accurate labels (`bug`, `documentation`, `enhancement`, `question`, `good first issue`) without spamming the thread with generic comments.
* **Anti-Spam & Delay Strategy**: Prevents community noise by only stepping in when human maintainers are unavailable. Configurable delays ensure the bot only relies to stale, unanswered issues.
* **Zero Cost Architecture**: Programmed specifically to utilize Google's Generative AI Free Tier boundaries by prioritizing Gemini 3.1 Flash Lite and 2.0 Flash series models. This grants thousands of free, lightweight daily queries.
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
  schedule:
    - cron: '0 */3 * * *' # Sweeps for unanswered issues every 3 hours

jobs:
  triage:
    runs-on: ubuntu-latest
    steps:
      # REQUIRED: Checkout is necessary so the AI can read your README.md context
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
```

## Inputs Configuration

| Input Name | Description | Default | Required |
| --- | --- | --- | --- |
| `github-token` | Your standard secrets.GITHUB_TOKEN to manage issues | N/A | Yes |
| `ai-api-key` | Google Gemini API key mapped from repository secrets | N/A | false |
| `delay-minutes` | Minutes to wait before the bot auto-responds to an abandoned issue | `180` | false |
| `bot-name` | Custom name used for direct mentions (invocations) in strings | `helperbot` | false |
| `language` | Interface fallback language. Supports `en` and `es` | `en` | false |

## Architecture & Lifecycle

1. **Silent Phase**: When an issue is opened, the action silently categorizes the text and applies native GitHub labels dynamically via API without posting any comments. 
2. **Mentoring Phase**: If an issue is left abandoned for longer than `delay-minutes`, the cron job sweeps the repository, detects the inactivity, reads your root README repository context, and generates an educated response aiming to mentor the user, often requesting logs or environment details to speed up human resolution.
3. **Conversational Phase**: If a user mentions the bot by its configured `bot-name` (e.g. `@helperbot please verify the docs`), it bypasses regular queues and cron schedules, providing an immediate technical response based on the repository documentation.

## License

This project is open-source and is licensed under the [MIT License](LICENSE).
