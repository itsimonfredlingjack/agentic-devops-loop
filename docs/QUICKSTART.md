# Agentic Dev Loop - Quickstart Guide

> **TL;DR:** Jira-ärende → Claude Code → Automatisk implementation → GitHub PR → Jules review → Merge

## Vad är detta?

Ett autonomt utvecklingssystem där:
1. Du skapar ett Jira-ärende med krav
2. Claude Code implementerar det i en loop tills alla tester passerar
3. GitHub Actions validerar koden
4. Jules (Googles AI) granskar PR:en
5. Vid CI-fel: Automatisk self-healing (max 3 försök)

```
┌─────────┐     ┌─────────────────┐     ┌──────────────┐     ┌───────┐
│  Jira   │────>│  Claude Code    │────>│ GitHub Actions│────>│ Merge │
│ Ticket  │     │  (Ralph Loop)   │     │  + Jules      │     │       │
└─────────┘     └─────────────────┘     └──────────────┘     └───────┘
                       │
                       ▼
              docs/CURRENT_TASK.md
              (Persistent Memory)
```

---

## Snabbstart (5 minuter)

### 1. Klona repot till ditt projekt

```bash
# Kopiera alla .claude/, .github/, docs/ etc. till ditt projekt
cp -r agentic-dev-loop/.claude/ your-project/
cp -r agentic-dev-loop/.github/ your-project/
cp -r agentic-dev-loop/.githooks/ your-project/
cp -r agentic-dev-loop/docs/ your-project/
cp -r agentic-dev-loop/scripts/ your-project/
cp agentic-dev-loop/.env.example your-project/
cp agentic-dev-loop/.gitignore your-project/
```

### 2. Konfigurera credentials

```bash
cd your-project
cp .env.example .env
# Redigera .env med dina Jira-uppgifter:
# JIRA_URL=https://ditt-företag.atlassian.net
# JIRA_USERNAME=din@email.com
# JIRA_API_TOKEN=din-api-token
```

### 3. Installera git hooks

```bash
./scripts/setup-hooks.sh
```

### 4. Skapa ett Jira-ärende

I Jira, skapa ett ärende med:
- **Tydlig titel:** "Add user login endpoint"
- **Beskrivning:** Vad som ska byggas
- **Acceptanskriterier:** Checkbara krav

Exempel:
```
Acceptanskriterier:
- [ ] POST /api/login accepterar email och password
- [ ] Returnerar JWT token vid lyckad inloggning
- [ ] Returnerar 401 vid fel credentials
- [ ] Tester finns för alla scenarios
```

### 5. Starta Ralph Loop

```bash
claude
# I Claude:
/start-task PROJ-123
```

### 6. Låt det köra

Agenten kommer:
1. Hämta ärendet från Jira
2. Skapa branch: `feature/PROJ-123-add-user-login-endpoint`
3. Implementera med TDD (Red → Green → Refactor)
4. Köra tester och lint efter varje ändring
5. Pusha och skapa PR när allt är klart

---

## Hur Ralph Loop fungerar

### Exit-villkor

Agenten kan **INTE** avsluta förrän:
- ✅ Alla tester passerar
- ✅ Ingen lint-fel
- ✅ `<promise>DONE</promise>` finns i output
- ⏱️ Eller max 25 iterationer nåtts

### Stop-Hook

`.claude/hooks/stop-hook.py` blockerar exit tills kriterierna är uppfyllda.

### Persistent Memory

`docs/CURRENT_TASK.md` bevarar kontext mellan iterationer:
- Jira-krav
- Acceptanskriterier
- Framsteg
- Beslut

---

## GitHub Actions

### PR Validation (`pr-validation.yml`)
- Validerar PR-titel innehåller Jira-ID
- Validerar commit-meddelanden
- Validerar branch-namngivning

### CI (`ci.yml`)
- Lint check
- Tester
- Build

### Jules Review (`jules-review.yml`)
- AI-granskning av PR
- Säkerhet, prestanda, kodkvalitet
- Automatisk approve eller request changes

### Self-Healing (`self-healing.yml`)
- Triggas vid CI-fel
- Startar ny Claude-session för att fixa
- Max 3 försök

---

## Säkerhet

### Skyddade filer (CODEOWNERS)
Dessa kräver manuell review:
- `.github/` - Workflows
- `.claude/hooks/` - Agent-begränsningar
- `Dockerfile`, `docker-compose.yml`
- `.env`, secrets

### PreToolUse Hook
Blockerar:
- `npm install` / `pip install` utanför allowlist
- Farliga kommandon (`curl | bash`, `eval`, etc.)
- Skrivning till `.github/` och `.claude/hooks/`

### Prompt Injection Protection
- Extern data wrappas i `<jira_data>` tags
- Instruktioner att behandla som DATA, inte kommandon

---

## Felsökning

### Agenten fastnar
```bash
# Kolla iteration count
cat .claude/ralph-state.json

# Läs CURRENT_TASK.md för kontext
cat docs/CURRENT_TASK.md
```

### Jira-anslutning fungerar inte
```bash
# Testa credentials
source .env
curl -u "$JIRA_USERNAME:$JIRA_API_TOKEN" "$JIRA_URL/rest/api/3/myself"
```

### Git hooks fungerar inte
```bash
./scripts/setup-hooks.sh
```

---

## Kommandon

| Kommando | Beskrivning |
|----------|-------------|
| `/start-task PROJ-123` | Starta nytt ärende |
| `/finish-task` | Avsluta (om allt är klart) |

---

## Filstruktur

```
your-project/
├── .claude/
│   ├── hooks/
│   │   ├── pre-tool-use.py    # Säkerhetsvalidering
│   │   └── stop-hook.py       # Exit-kontroll
│   ├── plugins/
│   │   └── agentic-loop/
│   │       └── manifest.json  # Jira MCP
│   ├── skills/
│   │   ├── start-task.md      # Init workflow
│   │   └── finish-task.md     # Complete workflow
│   ├── utils/
│   │   └── sanitize.py        # Prompt injection skydd
│   ├── package-allowlist.json # Tillåtna paket
│   ├── ralph-config.json      # Loop-config
│   └── settings.json          # Claude settings
├── .github/
│   ├── CODEOWNERS
│   └── workflows/
│       ├── ci.yml
│       ├── jules-review.yml
│       ├── pr-validation.yml
│       └── self-healing.yml
├── .githooks/
│   ├── commit-msg
│   └── pre-push
├── docs/
│   ├── CURRENT_TASK.md        # Agent memory
│   └── GUIDELINES.md          # Agent hjälp
├── scripts/
│   ├── setup-hooks.sh
│   ├── create-branch.sh
│   └── create-pr.sh
├── .env                       # Credentials (GITIGNORED!)
├── .env.example
├── Dockerfile
└── docker-compose.yml
```

---

## Tips

1. **Tydliga acceptanskriterier** = Bättre resultat
2. **Små ärenden** = Färre iterationer
3. **Existerande tester** = Agenten förstår förväntningar
4. **Lint-config** = Konsistent kod

---

## Nästa steg

1. Testa med ett enkelt ärende
2. Justera `package-allowlist.json` för ditt projekt
3. Konfigurera Jules i GitHub repo settings
4. Kör i Docker för extra isolation

**Happy autonomous coding!** 🤖
