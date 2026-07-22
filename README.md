# AI Live Streamer

AI Live Streamer is a Python-based commerce assistant for Bakery D'Ver. It processes customer messages, retrieves verified product information, generates concise replies, applies governance policies, maintains conversation context, and optionally speaks approved responses.

## Features

- Product intent and attribute detection
- SQLite product knowledge retrieval
- Conversation memory and product context
- Mock and OpenAI LLM providers
- Response governance and sanitization
- Optional text-to-speech output
- Runtime readiness checks
- Human-readable and JSON health checks
- Safe operational logging
- Automated test coverage

## Requirements

- Python 3.12 or newer
- Windows PowerShell
- A Python virtual environment
- OpenAI API key when using OpenAI or voice output

## Installation

Create and activate a virtual environment:

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1```

Install dependencies:

```powershell
python -m pip install -r .\requirements.txt
```

Create `.env` only when it does not already exist:

```powershell
if (-not (Test-Path .\.env)) {
    Copy-Item .\.env.example .\.env
}

code .\.env
```

If `.env` already exists, do not overwrite it.

Example development configuration:

```env
LLM_PROVIDER=mock
VOICE_ENABLED=false
OPENAI_API_KEY=
```

Use `LLM_PROVIDER=openai` for OpenAI responses. Set `VOICE_ENABLED=true` only when voice output is required.

Do not commit `.env` or expose a real API key.

## Usage

Show available commands:

```powershell
python -m app.main --help
```

Check runtime readiness:

```powershell
python -m app.main --check
```

Return runtime readiness as JSON:

```powershell
python -m app.main --check-json
```

Start the interactive console:

```powershell
python -m app.main
```

Type `exit`, `quit`, or `q` to close the console.
## Runtime Configuration

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `mock` | Selects `mock` or `openai` |
| `VOICE_ENABLED` | `true` | Enables OpenAI text-to-speech |
| `OPENAI_API_KEY` | empty | Required for OpenAI or voice output |

The product database must exist at:

```text
data/products.db
```

## Testing

Run the complete test suite:

```powershell
python -m pytest -q
```

Run focused tests:

```powershell
python -m pytest .\tests\test_main.py -q
python -m pytest .\tests\test_live_controller.py -q
python -m pytest .\tests\test_commerce_service.py -q
```

Check Python syntax:

```powershell
python -m py_compile .\app\main.py
python -m py_compile .\app\live_controller.py
```

Check pending changes before committing:

```powershell
git --no-pager diff --check
git status --short
```

## Application Flow

1. `app.main` validates runtime configuration.
2. `LiveCommerceController` receives the customer message.
3. `CommerceService` prepares search and product knowledge.
4. The configured LLM provider generates a response.
5. `GovernanceEngine` evaluates and sanitizes the response.
6. Conversation memory stores the customer and assistant turns.
7. Approved responses may be sent to the voice callback.

## Operational Safety

- Keep `.env` outside version control.
- Never print or commit a real API key.
- Use `--check` before starting production.
- Use `--check-json` for monitoring and automation.
- Voice failures do not discard an approved text response.
- Operational logs exclude customer messages and generated replies.

## Troubleshooting

If runtime readiness fails:

```powershell
python -m app.main --check
```

Verify that:

- `.env` exists and contains the required configuration.
- `data/products.db` exists and is not empty.
- `OPENAI_API_KEY` is configured when OpenAI or voice is enabled.
- The virtual environment is active.
- Dependencies are installed from `requirements.txt`.

For a safe local test without voice:

```powershell
$env:LLM_PROVIDER = "mock"
$env:VOICE_ENABLED = "false"
python -m app.main --check
Remove-Item Env:LLM_PROVIDER
Remove-Item Env:VOICE_ENABLED
```