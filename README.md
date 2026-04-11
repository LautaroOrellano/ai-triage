# 🤖 Discussion Helper Bot

Automates responses in GitHub issues when no one replies after a delay or when mentioned.

---

## 🚀 Features

- ⏱ **Auto-response after X minutes**: Scans for abandoned issues.
- 💬 **No-Spam Logic**: Responds only once and uses labels to track interaction.
- 🔔 **Mention Trigger**: Responds immediately when tagged.
- 🧠 **AI Integration**: Detects missing information and suggests solutions.
- 🛠 **Smart Filtering**: Checks for missing logs or code blocks.

---

## 📦 Usage

To use all features (Mentions + Auto-response), we recommend two separate workflow triggers:

```yaml
name: Discussion Bot
on:
  issues:
    types: [opened]
  issue_comment:
    types: [created]
  schedule:
    - cron: '*/30 * * * *' # Every 30 minutes

jobs:
  helper:
    runs-on: ubuntu-latest
    steps:
      - uses: tu-usuario/discussion-helper-bot@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          delay-minutes: 30
          bot-name: helperbot
          ai-api-key: ${{ secrets.AI_API_KEY }} # Optional
```

### ⚙️ Configuration

| Input | Description | Default |
|-------|-------------|---------|
| `github-token` | Your GitHub secret token. | (Required) |
| `delay-minutes` | Time to wait before flagging an issue as "abandoned". | `30` |
| `bot-name` | Name the bot responds to via `@mention`. | `helperbot` |
| `ai-api-key` | Optional API key for advanced AI logic. | `""` |

---

## 🏗 How it works

1. **Mentions**: If someone tags `@{bot-name}`, it replies immediately.
2. **Scheduled Sweep**: Every time the action runs on `schedule`, it looks for issues older than `delay-minutes` with 0 comments.
3. **Labels**: The bot adds a `bot-responded` label to avoid double-posting.
4. **Context Check**: It analyzes the body to see if "Logs" or "Code blocks" are missing and asks for them.
