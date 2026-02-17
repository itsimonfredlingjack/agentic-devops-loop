# SEJFA — Final Dokumentation

> **Senast uppdaterad:** 2026-02-15 (PR #403)
> **Status:** Produktionsklar
> **URL:** https://gruppett.fredlingautomation.dev

---

## 1. Vad är SEJFA?

SEJFA (Secure Enterprise Jira Flask Agent) är ett **autonomt Agentic DevOps Loop-system** som demonstrerar hur AI-agenter (Claude Code) kan driva hela utvecklingscykeln: från Jira-ticket till produktion utan mänsklig intervention.

**Kärnan:** En Flask-applikation med newsletter-prenumeration och expense tracking, kopplad till en automatiserad pipeline där:

1. **Jira** skapar tickets
2. **Claude Code** (via Ralph Loop) implementerar, testar, committar
3. **GitHub Actions** kör CI/CD (lint, test, security)
4. **Jules** (Google AI) gör automatisk code review på PRs
5. **Azure Container Apps** deployar till produktion via Docker

---

## 2. Teknikstack

| Komponent | Teknologi | Version |
|-----------|-----------|--------|
| Backend | Flask | 3.0.0+ |
| Databas | SQLAlchemy + SQLite/PostgreSQL | 3.1.0+ |
| Migrations | Flask-Migrate | 4.0.0+ |
| WebSocket | Flask-SocketIO | 5.0.0+ |
| WSGI Server | Gunicorn | 22.0.0+ |
| Linting | Ruff | 0.4.0+ |
| Tester | pytest + pytest-cov | 8.0.0+ |
| Container | Docker (Python 3.12-slim) | — |
| CI/CD | GitHub Actions | — |
| Hosting | Azure Container Apps | — |
| Tunnel | Cloudflare Tunnel | — |
| AI Review | Jules API (Google) | v1alpha |
| Jira | REST API (direkt, ingen MCP) | — |

**Python-versioner som testas:** 3.10, 3.11, 3.12, 3.13

---

## 3. Arkitektur

### 3.1 Clean 3-Layer Architecture

Varje modul följer strikt:

```
┌─────────────────────────────┐
│  Presentation Layer         │  Flask Blueprint + Jinja2 templates
│  (routes.py, templates/)    │  Hanterar HTTP request/response
├─────────────────────────────┤
│  Business Layer             │  Ren Python — INGA Flask-imports
│  (service.py)               │  Validering, affärslogik
├─────────────────────────────┤
│  Data Layer                 │  Modeller + Repository
│  (models.py, repository.py) │  In-memory eller SQLAlchemy ORM
└─────────────────────────────┘
```

**Dependency Injection:** Services får sitt repository via `__init__`:

```python
repository = InMemoryExpenseRepository()
service = ExpenseService(repository)
blueprint = create_expense_blueprint(service)
```

### 3.2 Moduler

| Modul | Sökväg | Persistence |
|-------|--------|-------------|
| Newsflash (newsletter) | `src/sejfa/newsflash/` | SQLAlchemy (SQLite/PostgreSQL) |
| Expense Tracker | `src/expense_tracker/` | In-memory (dataclass) |
| Admin/Auth | `src/sejfa/core/` | Hårdkodad MVP |
| Monitor | `src/sejfa/monitor/` | In-memory |
| Jira-integration | `src/sejfa/integrations/` | — |

---

## 4. Projektstruktur

```
grupp-ett-github/
├── app.py                          # Flask app factory (create_app)
├── requirements.txt
├── pyproject.toml                   # Ruff + pytest + coverage config
├── Dockerfile
│
├── src/
│   ├── sejfa/
│   │   ├── core/
│   │   │   ├── admin_auth.py        # Admin-inloggning (MVP: admin/admin123)
│   │   │   └── subscriber_service.py
│   │   ├── newsflash/
│   │   │   ├── business/
│   │   │   │   └── subscription_service.py
│   │   │   ├── data/
│   │   │   │   ├── models.py        # Subscriber (SQLAlchemy)
│   │   │   │   └── subscriber_repository.py
│   │   │   └── presentation/
│   │   │       ├── routes.py
│   │   │       └── templates/
│   │   │           ├── base.html
│   │   │           └── newsflash/
│   │   │               ├── index.html
│   │   │               ├── subscribe.html
│   │   │               └── thank_you.html
│   │   ├── monitor/
│   │   │   ├── monitor_routes.py    # /api/monitor/* + WebSocket
│   │   │   └── monitor_service.py
│   │   ├── integrations/
│   │   │   └── jira_client.py       # Direkt REST API till Jira
│   │   └── utils/
│   │       ├── health_check.py
│   │       └── security.py
│   │
│   └── expense_tracker/
│       ├── business/
│       │   ├── service.py           # ExpenseService
│       │   └── exceptions.py
│       ├── data/
│       │   ├── models.py            # Expense (dataclass)
│       │   └── repository.py        # InMemoryExpenseRepository
│       └── presentation/
│           ├── routes.py
│           └── templates/expense_tracker/
│               ├── base.html
│               ├── index.html
│               └── summary.html
│
├── scripts/                         # Pipeline-scripts
│   ├── jules_review_api.py          # Anropar Jules API, postar PR-review
│   ├── jules_to_jira.py             # Parsar findings → skapar Jira-tickets
│   ├── jules_payload.py             # Bygger context-payload för Jules
│   ├── classify_failure.py          # Klassificerar CI-failures
│   ├── ci_check.sh                  # Lokal CI-simulering
│   └── preflight.sh                 # Systemkontroll
│
├── tests/                           # 370+ tester
│   ├── test_app.py
│   ├── agent/
│   ├── core/
│   ├── expense_tracker/
│   ├── integrations/
│   ├── newsflash/
│   └── utils/
│
├── static/                          # Fristående filer (EJ Flask-serverade)
│   └── monitor.html                 # Dashboard (nås INTE via Flask-route)
│
├── .claude/                         # Agent-konfiguration
│   ├── CLAUDE.md                    # Agentinstruktioner
│   ├── commands/preflight.md
│   ├── hooks/
│   │   ├── stop-hook.py             # Quality gate (731 rader)
│   │   ├── prevent-push.py          # Blockerar push till main
│   │   ├── monitor_hook.py
│   │   └── monitor_client.py
│   ├── skills/
│   │   ├── start-task/SKILL.md
│   │   └── finish-task/SKILL.md
│   └── ralph-config.json
│
├── .github/workflows/               # CI/CD pipelines
│   ├── ci.yml                       # Lint + test matris (3.10-3.13) + security
│   ├── ci_branch.yml                # Feature branch: Python 3.12
│   ├── deploy.yml                   # Docker → ACR → Azure Container Apps
│   ├── post_deploy_verify.yml       # Health check + auto-rollback
│   ├── jules_review.yml             # AI code review
│   ├── jules_health_check.yml       # Daglig Jules API-kontroll
│   ├── cleanup-branches.yml         # Automatisk branch-cleanup
│   ├── self_healing.yml             # Auto-fix CI failures
│   └── self_heal_pr.yml             # Manuell self-healing per PR
│
├── migrations/                      # SQLAlchemy (Flask-Migrate)
│   └── versions/
│       └── 824b9238428a_add_subscribers_table.py
│
├── docs/                            # Dokumentation
│   ├── FINAL_DOCUMENTATION.md       # ← DENNA FIL (single source of truth)
│   └── jules-playbook.md
│
├── CURRENT_TASK.md                  # Agentens externa minne (aktiv ticket)
├── README.md
├── CONTRIBUTING.md
├── AGENTS.md
└── AGENTS.override.md
```

---

## 5. Alla API-endpoints

### 5.1 Root / Admin

| Endpoint | Metod | Beskrivning | Auth |
|----------|-------|-------------|------|
| `/api` | GET | JSON greeting | Nej |
| `/health` | GET | Health check | Nej |
| `/admin/login` | POST | Inloggning (user/pass i body) | Nej |
| `/admin` | GET | Admin dashboard | Bearer token |
| `/admin/statistics` | GET | Prenumerantstatistik | Bearer token |
| `/admin/subscribers` | GET | Lista prenumeranter | Bearer token |
| `/admin/subscribers` | POST | Skapa prenumerant | Bearer token |
| `/admin/subscribers/<id>` | GET | Hämta prenumerant | Bearer token |
| `/admin/subscribers/<id>` | PUT | Uppdatera prenumerant | Bearer token |
| `/admin/subscribers/<id>` | DELETE | Ta bort prenumerant | Bearer token |
| `/admin/subscribers/search` | GET | Sök prenumeranter | Bearer token |
| `/admin/subscribers/export` | GET | Exportera CSV | Bearer token |

**Admin-credentials (MVP):** `admin` / `admin123`
**Token-format:** `token_<username>_<hash>`

### 5.2 Newsflash (Newsletter)

| Route | Metod | Template | Beskrivning |
|-------|-------|----------|-------------|
| `/` | GET | `newsflash/index.html` | Landningssida |
| `/subscribe` | GET | `newsflash/subscribe.html` | Prenumerationsformulär |
| `/subscribe/confirm` | POST | → redirect | Hantera formulär |
| `/thank-you` | GET | `newsflash/thank_you.html` | Bekräftelsesida |

### 5.3 Expense Tracker

| Route | Metod | Template | Beskrivning |
|-------|-------|----------|-------------|
| `/expenses/` | GET | `expense_tracker/index.html` | Lista utgifter |
| `/expenses/add` | POST | → redirect | Lägg till utgift |
| `/expenses/summary` | GET | `expense_tracker/summary.html` | Sammanfattning |

### 5.4 Monitor API

| Route | Metod | Beskrivning |
|-------|-------|-------------|
| `/api/monitor/state` | GET | Hämta workflow-state |
| `/api/monitor/state` | POST | Uppdatera workflow-state |
| `/api/monitor/reset` | POST | Nollställ monitoring |
| `/api/monitor/task` | POST | Uppdatera task-info |
| WebSocket `/monitor` | — | Real-time state streaming |

---

## 6. Produktionsfilkarta (KRITISK)

### Filer som Azure FAKTISKT serverar

| Route | Template-fil |
|-------|-------------|
| `/` | `src/sejfa/newsflash/presentation/templates/newsflash/index.html` |
| `/subscribe` | `src/sejfa/newsflash/presentation/templates/newsflash/subscribe.html` |
| `/thank-you` | `src/sejfa/newsflash/presentation/templates/newsflash/thank_you.html` |
| Base layout | `src/sejfa/newsflash/presentation/templates/base.html` |
| `/expenses/` | `src/expense_tracker/templates/expense_tracker/index.html` |
| `/expenses/summary` | `src/expense_tracker/templates/expense_tracker/summary.html` |
| Expense base | `src/expense_tracker/templates/expense_tracker/base.html` |

### Filer som INTE serveras av Flask

| Fil | Förklaring |
|-----|------------|
| `static/monitor.html` | Fristående HTML, ingen Flask-route |
| `static/*.png` | Bilder för monitor.html |

**Regel:** Om en ticket säger "ändra UI" eller "produktion" → ändra Flask-templates ovan, INTE `static/`.

---

## 7. Datamodeller

### Subscriber (SQLAlchemy ORM)

```python
class Subscriber(db.Model):
    id: int              # Primary Key
    email: str           # Unique, Indexed (max 255)
    name: str            # Max 255
    subscribed_at: datetime
    active: bool
```

### Expense (dataclass, in-memory)

```python
@dataclass
class Expense:
    id: int
    title: str
    amount: float
    category: str        # "Mat", "Transport", "Boende", "Övrigt"
```

### WorkflowNode (Monitor, in-memory)

```python
class WorkflowNode:
    active: bool
    last_active: str     # ISO timestamp
    message: str
```

Noder: `jira`, `claude`, `github`, `jules`, `actions`

---

## 8. Jules Pipeline (AI Code Review)

### 8.1 Flöde

```
PR skapas → jules_review.yml triggas → jules_review_api.py
    → Skapar Jules session (review-only, INGEN PR-skapning)
    → Pollar tills session klar (max 12 min / 720s)
    → Extraherar findings med multi-strategy deep search:
        1. text-via-key strategy (description/review_text/findings)
        2. structured JSON extraction (Strategy 1b)
        3. messages[].content fallback
        4. session-level text fields
    → Postar review-kommentar på PR

jules_to_jira.py triggas med JULES_REVIEW_BODY
    → Kontrollerar error/timeout FÖRST (_is_error_or_timeout)
    → Strippar review-wrapper (format_review_body header/footer)
    → Parsar findings (5 regex-patterns + JSON fallback)
    → HIGH/CRITICAL/MEDIUM → Standalone Jira Tasks (max 3)
    → LOW → Kommentar på parent ticket
```

### 8.2 Severity-hantering

| Severity | Åtgärd | Destination |
|----------|---------|-----------|
| CRITICAL | Standalone Jira Task | Nytt ticket |
| HIGH | Standalone Jira Task | Nytt ticket |
| **MEDIUM** | **Standalone Jira Task** | **Nytt ticket** |
| LOW | Kommentar | Parent ticket |

**MEDIUM eskaleras till Tasks** — detta var en kritisk buggfix (PR #400).

### 8.3 Extraction & Parsing

#### jules_review_api.py — Review Text Extraction

Fyra strategier i ordning (first match wins):

1. **Strategy 1 (text-via-key):** Söker efter kända nycklar (`description`, `review_text`, `findings`, etc.) i sessions-datan
2. **Strategy 1b (structured JSON):** `_extract_structured_findings()` walkar JSON-trädet rekursivt (max depth 20) och hittar dicts med `severity` + `description`-nycklar. Formaterar som `[SEVERITY] location — description`
3. **Strategy 2 (messages):** Extraherar `content` från `messages[]`-array
4. **Strategy 3 (session text):** Fallback — session-level text-fält

**Strategy 1b detaljer:**
```python
# Matchar dicts som ser ut som findings:
{
    "severity": "HIGH",           # Required: HIGH/MEDIUM/LOW/CRITICAL
    "file": "src/app.py",         # Optional: location/file/path/filename/file_path/filepath
    "description": "SQL injection" # Required: description/message/detail/finding/text/content/summary
}
# → Formateras som: [HIGH] src/app.py — SQL injection
```

#### jules_to_jira.py — Finding Parsing

**Error/Timeout Guard:** Innan parsing körs, kollar `_is_error_or_timeout()` de första 5 raderna efter error-indikatorer:
- Emoji: `⏰`, `❌`, `⚠️`, `🚨`
- Text: `"timed out"`, `"timeout"`, `"error"`, `"failed to"`, `"could not"`, `"no findings"`, `"no review"`, `"unavailable"`

Om error detekteras → loggar varning + returnerar tidigt (inga ghost-tickets).

**Review Wrapper Stripping:** `_strip_review_wrapper()` tar bort `format_review_body()` header/footer innan JSON-parsing, så att structured data inte bryts av wrapping-text.

**Fem regex-mönster** testas i ordning (first match wins):

1. `[SEVERITY] file:line — description` (original bracket)
2. `**SEVERITY** file:line — description` (markdown bold)
3. `SEVERITY: file:line — description` (colon-separated)
4. `N. [SEVERITY] file:line — description` (numbered/bulleted)
5. `SEVERITY file:line — description` (loose)

Om ingen regex matchar → **JSON fallback parser** (`_try_parse_json_findings()`) som:
- Strippar review-wrapper
- Försöker `json.loads()` direkt
- Söker efter `[...]` eller `{...}` substring
- Matchar utökade nycklar: `file`, `filepath`, `file_path`, `path`, `filename`, `location`

### 8.4 Nyckelscripts & Funktioner

| Script | Funktion |
|--------|----------|
| `scripts/jules_review_api.py` | Anropar Jules API, extraherar review-text, postar som PR-kommentar |
| `scripts/jules_to_jira.py` | Parsar findings → skapar Jira Tasks (HIGH/MEDIUM/CRITICAL) + kommentarer (LOW) |
| `scripts/jules_payload.py` | Bygger budget-medveten context-payload för Jules |

**Nyckelfunktioner i jules_review_api.py:**

| Funktion | Syfte |
|----------|-------|
| `extract_review_text()` | Multi-strategy extraction (4 strategier) |
| `_extract_structured_findings()` | Strategy 1b — walkar JSON-träd för structured dicts |
| `_log_session_structure()` | Debug-logging av JSON-nyckelstruktur |
| `poll_session()` | Pollar Jules session (max 720s / 12 min) |
| `format_review_body()` | Formaterar review-text till markdown |

**Nyckelfunktioner i jules_to_jira.py:**

| Funktion | Syfte |
|----------|-------|
| `_is_error_or_timeout()` | Gate — detekterar error/timeout innan parsing |
| `_strip_review_wrapper()` | Tar bort format_review_body header/footer |
| `_try_parse_json_findings()` | JSON fallback med utökad nyckel-matching |
| `parse_findings()` | 5 regex-patterns + JSON fallback |
| `create_jira_task()` | Skapar standalone Jira Task (HIGH/MEDIUM/CRITICAL) |
| `add_jira_comment()` | Lägger till kommentar (LOW findings) |

### 8.5 Pipeline-konfiguration

| Parameter | Värde | Beskrivning |
|-----------|-------|-------------|
| `MAX_POLL_SEC` | 720 (12 min) | Max väntetid på Jules session |
| `MAX_JIRA_TICKETS` | 3 | Max antal tickets per review |
| `SEVERITY_RE` | `HIGH\|MEDIUM\|LOW\|CRITICAL` | Regex för severity-matching |
| Workflow timeout | 20 min | GitHub Actions timeout |

---

## 9. Ralph Loop (Agentic Dev Loop)

### 9.1 Vad är Ralph Loop?

Ralph Loop är en autonom exekveringsloop där Claude Code:

1. Hämtar en Jira-ticket
2. Skapar branch
3. Implementerar med TDD (test first → fail → implement → pass)
4. Kör tester + linting
5. Committar, pushar, skapar PR
6. Uppdaterar Jira-status

### 9.2 External Memory

`CURRENT_TASK.md` fungerar som agentens externa minne.

### 9.3 Completion Signals

| Signal | Betydelse |
|--------|-----------|
| `<promise>DONE</promise>` | Uppgift helt klar |
| `<promise>BLOCKED</promise>` | Kan ej fortsätta |
| `<promise>FAILED</promise>` | Uppgiften kan ej slutföras |

### 9.4 Agent Hooks

| Hook | Fil | Funktion |
|------|-----|----------|
| Stop Hook | `.claude/hooks/stop-hook.py` | Quality gate — blockerar om tester/lint misslyckas |
| Prevent Push | `.claude/hooks/prevent-push.py` | Förhindrar direkt push till main |
| Monitor Hook | `.claude/hooks/monitor_hook.py` | Real-time loop-övervakning |
| Monitor Client | `.claude/hooks/monitor_client.py` | SocketIO-klient för dashboard |

### 9.5 Agent Skills

| Skill | Trigger | Funktion |
|-------|---------|----------|
| `/start-task` | Ny uppgift | Hämta Jira-ticket, skapa branch, init CURRENT_TASK.md |
| `/finish-task` | Uppgift klar | Verifiera, committa, pusha, skapa PR, uppdatera Jira |
| `/preflight` | Före start | Validera system-readiness |

---

## 10. CI/CD Pipelines

### 10.1 ci.yml — Huvudpipeline

**Trigger:** Push till main, PRs mot main

| Jobb | Steg |
|------|------|
| `lint` | `ruff check .` + `ruff format --check .` |
| `test` | pytest med coverage (matris: 3.10, 3.11, 3.12, 3.13) |
| `security` | `pip-audit` / `safety check` |

**Coverage gate:** 80% minimum (CI: 70%)

### 10.2 ci_branch.yml — Feature branches

**Trigger:** Push till alla branches utom main

Kör lint + test med Python 3.12 (ingen fullmatris).

### 10.3 deploy.yml — Deployment

**Trigger:** Push till main (efter CI passerar)

1. Checkout
2. Azure login (OIDC)
3. Bygg Docker-image
4. Push till Azure Container Registry
5. Deploy till Azure Container Apps

### 10.4 jules_review.yml — AI Review

**Trigger:** PR skapad/uppdaterad

1. Kör `jules_review_api.py` — skapar Jules session, pollar (max 12 min), postar review
2. Kör `jules_to_jira.py` — error guard → parsar findings → skapar Jira-tickets

### 10.5 Övriga workflows

| Workflow | Funktion |
|----------|----------|
| `post_deploy_verify.yml` | Health check efter deploy + auto-rollback |
| `cleanup-branches.yml` | Daglig cleanup av mergade branches |
| `jules_health_check.yml` | Daglig kontroll av Jules API |
| `self_healing.yml` | Automatisk CI-fix (OBS: säkerhetsrisk flaggad) |
| `self_heal_pr.yml` | Manuell self-healing per PR |

---

## 11. Deployment

### 11.1 Docker

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
HEALTHCHECK --interval=30s CMD curl -f http://localhost:5000/health
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "app:app"]
```

### 11.2 Infrastruktur

```
GitHub → Docker build → Azure Container Registry → Azure Container Apps
                                                          │
                                              Cloudflare Tunnel
                                                          │
                                          gruppett.fredlingautomation.dev
```

### 11.3 Environment Variables

```bash
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=...

# Jira
JIRA_URL=https://xxx.atlassian.net
JIRA_EMAIL=...
JIRA_API_TOKEN=...

# Databas (default: SQLite)
DATABASE_URL=sqlite:///newsflash.db

# Jules
JULES_API_KEY=...
```

---

## 12. Tester

### 12.1 Köra tester

```bash
# VIKTIGT: Aktivera venv först!
source venv/bin/activate && pytest -xvs

# Med coverage
source venv/bin/activate && pytest --cov=src --cov=app.py --cov-report=term-missing

# Linting
source venv/bin/activate && ruff check .
source venv/bin/activate && ruff format --check .
```

### 12.2 Teststruktur

370+ tester fördelade över:

| Katalog | Testar |
|---------|--------|
| `tests/test_app.py` | Flask app factory |
| `tests/agent/` | Ralph loop integration |
| `tests/core/` | Admin auth, subscriber service |
| `tests/expense_tracker/` | Expense service, routes, models |
| `tests/integrations/` | Jira client, jules_to_jira |
| `tests/newsflash/` | Subscription service |
| `tests/utils/` | Security, health check |

### 12.3 Test Markers

```python
@pytest.mark.unit          # Isolerade komponenter
@pytest.mark.integration   # Med externa beroenden
@pytest.mark.e2e           # End-to-end workflows
@pytest.mark.slow          # Långsamma tester
```

### 12.4 Coverage

- **Minimum:** 80% (pyproject.toml: `fail_under = 80`)
- **CI gate:** 70%
- **Scope:** `src/` och `app.py`
- **Branch coverage:** aktiverat

---

## 13. Kodstil & Ruff

### 13.1 Ruff-konfiguration (pyproject.toml)

- **Linjelangd:** 88 tecken (Black-kompatibel)
- **Regler:** E, F, W, I, N, UP, B, C4
- **Target:** Python 3.10
- **Exkluderar:** `.claude/hooks/*`, `venv`, `.venv`

### 13.2 Konventioner

| Typ | Konvention |
|-----|------------|
| Funktioner/variabler | `snake_case` |
| Klasser | `PascalCase` |
| Konstanter | `SCREAMING_SNAKE_CASE` |
| Privata funktioner | `_prefix` |
| Type hints | Alla funktionssignaturer |
| Docstrings | Google-stil, publika funktioner |
| Imports | stdlib → third-party → local |

### 13.3 Commit-format

```
GE-XXX: Kort beskrivning (max 72 tecken)

- Detaljpunkt 1
- Detaljpunkt 2

Co-Authored-By: Claude Code <noreply@anthropic.com>
```

---

## 14. Jira-integration

### 14.1 Klient

`src/sejfa/integrations/jira_client.py` — Direkt REST API (INTE MCP).

```python
config = JiraConfig.from_env()
client = JiraClient(config)
issue = client.get_issue("GE-35")
client.create_issue(project_key="GE", summary="...", issue_type="Task")
client.add_comment("GE-35", "Kommentar")
```

### 14.2 Ticket-konventioner

- **Projekt:** GE (Grupp Ett)
- **Branch-format:** `feature/GE-XXX-kort-beskrivning`
- **Commit-prefix:** `GE-XXX: `
- **Labels för Jules-tickets:** `jules-review`, `automated`

---

## 15. Teamet

| Namn | Roll |
|------|------|
| Simon | Lead / AI Automation Architect |
| Filippa | Developer |
| Jonas Ö | Developer |
| Emma | Developer |
| Annika | Developer |

---

## 16. Säkerhet

### Tillåtet

- Läsa/skriva kod i `src/`, `tests/`, `docs/`
- Köra tester och linting
- Skapa commits och branches
- Skapa PR via `gh` CLI

### Förbjudet

- Installera paket utan godkännande
- Skriva credentials i kod
- Ändra `.github/CODEOWNERS` eller `.claude/hooks/`
- Köra `rm -rf`, `git reset --hard`, `git push --force`
- Pusha till main direkt (endast via PR)
- Skippa hooks (`--no-verify`)

### Prompt Injection-skydd

Data från Jira omsluts i `<ticket>` taggar i CURRENT_TASK.md och behandlas som DATA, inte instruktioner.

---

## 17. Kända begränsningar

| Begränsning | Beskrivning |
|-------------|-------------|
| Admin-auth | Hårdkodad MVP (admin/admin123) — inte JWT/database |
| Expense data | In-memory — försvinner vid restart |
| Monitor dashboard | `static/monitor.html` ej Flask-serverad — kräver direkt åtkomst |
| self_healing.yml | Säkerhetsrisk flaggad (potentiell RCE) |
| Jules API | Alpha — kan vara instabil |

---

## 18. Snabbreferens

```bash
# Starta nytt arbete
git checkout -b feature/GE-XXX-beskrivning

# Kör tester (ALLTID med venv!)
source venv/bin/activate && pytest -xvs

# Kör linting
source venv/bin/activate && ruff check .
source venv/bin/activate && ruff check --fix .

# Committa
git add [filer]
git commit -m "GE-XXX: Beskrivning"

# Pusha och skapa PR
git push -u origin HEAD
gh pr create --title "GE-XXX: Titel" --body "Beskrivning"

# Kolla Jira-ticket
source venv/bin/activate && python3 -c "
from dotenv import load_dotenv; load_dotenv(dotenv_path='.env')
from src.sejfa.integrations.jira_client import get_jira_client
client = get_jira_client()
issue = client.get_issue('GE-XXX')
print(f'{issue.key}: {issue.summary}')
"
```

---

## 19. Ändringslogg

| PR | Datum | Beskrivning |
|----|-------|-------------|
| #400 | 2026-02-14 | Fix: SEVERITY_RE broadened, multiple parse patterns + JSON fallback, MEDIUM→Task eskalering, CI branch workflow |
| #402 | 2026-02-14 | Docs: Städade 9 outdated doc-filer, skapade FINAL_DOCUMENTATION.md |
| #403 | 2026-02-15 | Fix: Structured JSON extraction (Strategy 1b), error/timeout guard, MAX_POLL_SEC 540→720, review wrapper stripping |
