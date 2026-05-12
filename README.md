# JavaScript Extractor

A fast and flexible JavaScript extraction and regex scanning tool for security research, bug bounty hunting, and web application analysis.

`js-extractor` crawls JavaScript files from a target website, applies configurable YAML-based regex groups, and exports structured extraction results.

---

## Features

- ✅ Extract JavaScript files from webpages
- ✅ Supports Playwright browser mode
- ✅ Supports authenticated crawling with persistent sessions
- ✅ YAML-based regex pattern groups
- ✅ Match API endpoints, secrets, tokens, keys, URLs, and custom patterns
- ✅ JSON export support
- ✅ Relative + absolute JavaScript URL handling
- ✅ Headless and browser automation modes
- ✅ Verbose/debug logging
- ✅ Custom extraction context (`--before`, `--after`)
- ✅ Custom Playwright storage state support
- ✅ Reusable Python API
- ✅ Installable via `pip`

---

## Installation

### Install from PyPI

```bash
pip install js-extractor
```

### Install Playwright browser

```bash
playwright install chromium
```

---

## Usage

### Basic Scan

```bash
js-extractor https://example.com
```

### Using Named Arguments

```bash
js-extractor -u https://example.com
```

### Using Custom Regex Group Directory

```bash
js-extractor -u https://example.com -g ./groups
```

### Enable Verbose Logging

```bash
js-extractor -u https://example.com -v
```

### Browser Mode

```bash
js-extractor -u https://example.com --browser
```

---

## Authentication / Login Mode

Interactive login mode allows authenticated JavaScript extraction using Playwright persistent sessions.

### Login Example

```bash
js-extractor -u https://example.com \
    --browser \
    --login \
    --login-url https://example.com/login \
    --login-success-indicator Logout
```

### Force Re-login

```bash
js-extractor -u https://example.com \
    --browser \
    --login \
    --force-relogin
```

### Custom Storage State File

```bash
js-extractor -u https://example.com \
    --browser \
    --login \
    --storage-state ./states/admin.json
```

---

## Match Extraction Context

Show surrounding content around matches.

### Example

```bash
js-extractor -u https://example.com \
    --before 50 \
    --after 50
```

---

## Regex Group Configuration

Regex groups are defined using YAML files.

### Example Structure

```yaml
js-extractor:
  name: Group Name
  patterns:
    - regex: "pattern1"
      description: "What this pattern matches"

    - regex: "pattern2"
      description: "Another pattern"
```

---

## Predefined Regex Groups

A collection of community-maintained regex groups is available here:

- [js-extractor-groups](https://github.com/rdzsp/js-extractor-groups?utm_source=chatgpt.com)

The repository contains predefined regex groups for:
- API endpoints and URLs
- Environment variables and frontend configuration
- Secrets, tokens, and sensitive text
- `postMessage` communication patterns
- Dependency confusion related modules/libraries
- Additional JavaScript reconnaissance patterns
- And more

### Example Usage

```bash
js-extractor -u https://example.com \
    -g ./js-extractor-groups
```

### Clone Regex Groups Repository

```bash
git clone https://github.com/rdzsp/js-extractor-groups.git
```

---

## Example Endpoint Patterns

```yaml
js-extractor:
  name: Endpoints / URLs
  patterns:
    - regex: >-
        `((?:\/(?:v3|v4|v5|ads)(?:\/[^`\/\s]+)+(?:\/)?))`
      description: Template literal API endpoints

    - regex: >-
        "((?:\/(?:v3|v4|v5|ads)(?:\/[^"\/\s]+)+(?:\/)?))"
      description: Double-quoted API endpoints

    - regex: >-
        '((?:\/(?:v3|v4|v5|ads)(?:\/[^'\/\s]+)+(?:\/)?))'
      description: Single-quoted API endpoints
```

---

## Output Format

Results are exported as JSON.

### Example

```json
[
  {
    "value": "/v3/users/get",
    "group_name": "Endpoints / URLs",
    "description": "Template literal API endpoints",
    "url": "https://example.com/assets/app.js"
  }
]
```

Default output file:

```text
extraction_results.json
```

---

## Command-Line Arguments

| Argument | Description |
|---|---|
| `-u`, `--url` | Target URL |
| `-g`, `--group` | Regex group directory |
| `-b`, `--browser` | Enable Playwright browser mode |
| `-l`, `--login` | Enable interactive login |
| `-lu`, `--login-url` | Login page URL |
| `-lsi`, `--login-success-indicator` | Successful login indicator text |
| `-fr`, `--force-relogin` | Force new login session |
| `-ss`, `--storage-state` | Custom Playwright storage state file |
| `-af`, `--after` | Characters after match |
| `-be`, `--before` | Characters before match |
| `-o`, `--output` | Output JSON file |
| `-v`, `--verbose` | Enable verbose logging |
| `-t`, `--timeout` | Request timeout |

---

## Python API Usage

```python
from js_extractor.extractor import extract

results = extract(
    target_url="https://example.com",
    browser=True,
    verbose=True
)

print(results)
```

---

## Project Structure

```text
js-extractor/
├── pyproject.toml
├── README.md
├── src/
│   └── js_extractor/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── extractor.py
│       ├── auth.py
│       └── utils.py
```

---

## Troubleshooting

### Install Playwright Browsers

```bash
playwright install chromium
```

### Enable Browser Mode for Login

Authentication requires browser mode:

```bash
js-extractor -u https://example.com \
    --browser \
    --login
```

### No Display Detected

Interactive login requires a graphical display.

Linux users may need:
- X11
- Wayland
- Desktop environment
- X forwarding

---

## Security Notice

Use responsibly and only on systems you own or are authorized to test.

This project is intended for:
- Security research
- Bug bounty hunting
- Web application analysis
- Authorized penetration testing

---

## License

MIT License