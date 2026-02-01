# PR Review Findings

## 1. Security Vulnerabilities

### Critical: Missing File Extension Validation
**File:** `document_upload_app/app.py`
**Line:** 37-59 (upload_file function)

**Issue:** The application accepts any file type without validation. This allows attackers to upload executable files (e.g., `.py`, `.php`, `.exe`) which could lead to Remote Code Execution (RCE).

**Suggested Fix:**
Validate the file extension against a strict allowlist.

```python
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    # ...
    file = request.files['file']
    if file and allowed_file(file.filename):
        # ... proceed with upload
```

### Critical: Script Injection in GitHub Actions
**File:** `.github/workflows/jules-review.yml`
**Line:** 20-23

**Issue:** The workflow directly interpolates user input (`github.event.pull_request.title`) into a shell command. A malicious PR title could execute arbitrary commands in the runner.

```yaml
run: |
  echo "branch=${{ github.head_ref }}" >> $GITHUB_OUTPUT
  echo "pr_number=${{ github.event.pull_request.number }}" >> $GITHUB_OUTPUT
  echo "pr_title=${{ github.event.pull_request.title }}" >> $GITHUB_OUTPUT
```

**Suggested Fix:**
Map inputs to environment variables.

```yaml
env:
  PR_TITLE: ${{ github.event.pull_request.title }}
run: |
  echo "branch=${{ github.head_ref }}" >> $GITHUB_OUTPUT
  echo "pr_number=${{ github.event.pull_request.number }}" >> $GITHUB_OUTPUT
  echo "pr_title=$PR_TITLE" >> $GITHUB_OUTPUT
```

### High: Cross-Site Scripting (XSS) in Monitor
**File:** `docs/monitor/index.html`
**Line:** 1066 (addEventToLog) and 936 (handleTaskUpdate)

**Issue:** The application uses `innerHTML` to render event messages and task status, which are potentially unsafe inputs (e.g., from WebSocket). This allows XSS if the backend sends malicious scripts.

**Suggested Fix:**
Use `textContent` for text content or properly sanitize HTML.

```javascript
// Instead of:
// li.innerHTML = `... ${event.message} ...`;

// Use:
li.className = 'event-item';
const marker = document.createElement('span');
marker.className = 'event-marker';
// ... set styles ...
marker.textContent = icon;

const messageSpan = document.createElement('span');
messageSpan.style.flex = '1';
messageSpan.textContent = event.message; // Safe

li.appendChild(marker);
li.appendChild(messageSpan);
// ...
```

### Medium: Debug Mode Enabled in Production
**File:** `document_upload_app/app.py`
**Line:** 74

**Issue:** `app.run(debug=True)` is used. If this code is deployed, it exposes the interactive debugger, which is a major security risk.

**Suggested Fix:**
Use `debug=False` or control via environment variables.

```python
if __name__ == '__main__':
    app.run(debug=False, host='localhost', port=5000)
```

## 2. Performance Problems

### High: Inefficient DOM Querying
**File:** `src/timestamp-display.js`
**Line:** 122-123 (updateTimestamp)

**Issue:** `querySelector` is called every second inside `updateTimestamp`. This causes unnecessary DOM traversal overhead.

**Suggested Fix:**
Cache the DOM elements in the constructor or `connectedCallback`.

```javascript
constructor() {
  super();
  // ...
  this.render();
  this.dateElement = this.shadowRoot.querySelector('[data-role="date"]');
  this.timeElement = this.shadowRoot.querySelector('[data-role="time"]');
}

updateTimestamp() {
  // ...
  if (this.dateElement) this.dateElement.textContent = dateStr;
  if (this.timeElement) this.timeElement.textContent = timeStr;
}
```

## 3. Code Quality & Best Practices

### Medium: Use of innerHTML
**File:** `src/timestamp-display.js`
**Line:** 92

**Issue:** Using `innerHTML` for dynamic updates is generally discouraged due to security risks (XSS) and performance (re-parsing), even if current inputs are safe.

**Suggested Fix:**
Use `textContent` as suggested in the Performance fix above.

### Low: Python Test Command
**File:** `.github/workflows/ci.yml`
**Line:** 91

**Issue:** Using `pytest` directly may use the wrong Python environment wrapper.

**Suggested Fix:**
Use `python3 -m pytest` or `python -m pytest`.

```yaml
- name: Run pytest
  run: python -m pytest -q
```

### Low: Broken Linting Configuration
**File:** `eslint.config.js`, `package.json`
**Line:** 1

**Issue:** `eslint.config.js` imports `@eslint/js` which is missing from `devDependencies`. Also, the file uses ES Module syntax (`import`/`export`) but has `.js` extension in a project that seems to be CommonJS (implied by `package.json` lacking `"type": "module"`).

**Suggested Fix:**
1. Install `@eslint/js`: `npm install --save-dev @eslint/js`
2. Rename `eslint.config.js` to `eslint.config.mjs`.
