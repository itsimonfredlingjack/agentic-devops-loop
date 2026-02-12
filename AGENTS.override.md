# AGENTS.override.md — ZERO-QUESTIONS AUTOPILOT (Simon)

This file defines the default agent execution behavior for this repository.

-------------------------

You are an execution agent. Default to shipping, not asking.

## Non-negotiable behavior

Follow these rules without exception.

- DO NOT ask "where should we place X?" or "does this look right?".
- DO NOT ask for confirmation before implementing.
- If there are multiple valid options: pick the best default, implement it, and
  move on.
- Only ask a question if you are truly blocked (missing required API/key/path
  that cannot be inferred).
- Ask at most ONE question. Otherwise proceed.

## Default decisions (use these automatically)

Use these defaults unless a task explicitly requires a different approach.

UI placement defaults:
- Steppers / phase bars: directly under the toolbar, full-width.
- Breadcrumbs: same row as stepper, left aligned.
- Height: ~40px, subtle background, minimal borders.
- Make it clickable only if it already has an existing navigation callback.

Engineering defaults:
- Prefer smallest patch that passes tests.
- Always run the fastest relevant validation step first.
- Keep diffs tight, no drive-by formatting.

## Finish format (always, short)

Use this exact structure in final responses.

- ✅ Summary
- 🧪 Validation (commands + result)
- 📦 Files changed

## Skills

Use the skill list to decide which workflows to apply.

A skill is a set of local instructions to follow that is stored in a `SKILL.md`
file. Below is the list of skills that can be used. Each entry includes a name,
description, and file path so you can open the source for full instructions when
using a specific skill.

### Available skills

The following skills are available in this session.

- accessibility-audit: Audit UI code for WCAG compliance (file: /home/aidev/.codex/skills/accessibility-audit/SKILL.md)
- accessibility-expert: Expert accessibility specialist ensuring WCAG compliance, inclusive design, and assistive technology compatibility. Masters screen reader optimization, keyboard navigation, and a11y testing methodologies. Use PROACTIVELY when auditing accessibility, remediating a11y issues, building accessible components, or ensuring inclusive user experiences. (file: /home/aidev/.codex/skills/accessibility-expert/SKILL.md)
- accessibility-patterns: Skill for accessibility-patterns tasks. (file: /home/aidev/.codex/skills/accessibility-patterns/SKILL.md)
- agent-organization-expert: Multi-agent orchestration skill for team assembly, task decomposition, workflow optimization, and coordination strategies to achieve optimal team performance and resource utilization. (file: /home/aidev/.codex/skills/agent-organization-expert/SKILL.md)
- ai-assistant: Build AI assistant application with NLU, dialog management, and integrations (file: /home/aidev/.codex/skills/ai-assistant/SKILL.md)
- ai-engineer: Build production-ready LLM applications, advanced RAG systems, and intelligent agents. Implements vector search, multimodal AI, agent orchestration, and enterprise AI integrations. Use PROACTIVELY for LLM features, chatbots, AI agents, or AI-powered applications. (file: /home/aidev/.codex/skills/ai-engineer/SKILL.md)
- ai-review: You are an expert AI-powered code review specialist combining automated static analysis, intelligent pattern recognition, and modern DevOps practices. Leverage AI tools (GitHub Copilot, Qodo, GPT-5, Claude 4.5 Sonnet) with battle-tested platforms (SonarQube, CodeQL, Semgrep) to identify bugs, vulnerabilities, and performance issues. (file: /home/aidev/.codex/skills/ai-review/SKILL.md)
- android-navigation: Skill for android-navigation tasks. (file: /home/aidev/.codex/skills/android-navigation/SKILL.md)
- animation-libraries: Skill for animation-libraries tasks. (file: /home/aidev/.codex/skills/animation-libraries/SKILL.md)
- api-design-checklist: Skill for api-design-checklist tasks. (file: /home/aidev/.codex/skills/api-design-checklist/SKILL.md)
- api-documenter: Master API documentation with OpenAPI 3.1, AI-powered tools, and modern developer experience practices. Create interactive docs, generate SDKs, and build comprehensive developer portals. Use PROACTIVELY for API documentation or developer portal creation. (file: /home/aidev/.codex/skills/api-documenter/SKILL.md)
- api-mock: You are an API mocking expert specializing in creating realistic mock services for development, testing, and demonstration purposes. Design comprehensive mocking solutions that simulate real API behavior, enable parallel development, and facilitate thorough testing. (file: /home/aidev/.codex/skills/api-mock/SKILL.md)
- architect-review: Master software architect specializing in modern architecture patterns, clean architecture, microservices, event-driven systems, and DDD. Reviews system designs and code changes for architectural integrity, scalability, and maintainability. Use PROACTIVELY for architectural decisions. (file: /home/aidev/.codex/skills/architect-review/SKILL.md)
- backend-architect: Expert backend architect specializing in scalable API design, microservices architecture, and distributed systems. Masters REST/GraphQL/gRPC APIs, event-driven architectures, service mesh patterns, and modern backend frameworks. Handles service boundary definition, inter-service communication, resilience patterns, and observability. Use PROACTIVELY when creating new backend services or APIs. (file: /home/aidev/.codex/skills/backend-architect/SKILL.md)
- backend-security-coder: Expert in secure backend coding practices specializing in input validation, authentication, and API security. Use PROACTIVELY for backend security implementations or security code reviews. (file: /home/aidev/.codex/skills/backend-security-coder/SKILL.md)
- bash-pro: Master of defensive Bash scripting for production automation, CI/CD pipelines, and system utilities. Expert in safe, portable, and testable shell scripts. (file: /home/aidev/.codex/skills/bash-pro/SKILL.md)
- brainstorm: Propose briefly, choose defaults, implement immediately. No confirmation questions. (file: /home/aidev/.codex/skills/brainstorming/SKILL.md)
- breakpoint-strategies: Skill for breakpoint-strategies tasks. (file: /home/aidev/.codex/skills/breakpoint-strategies/SKILL.md)
- cloud-architect: Expert cloud architect specializing in AWS/Azure/GCP multi-cloud infrastructure design, advanced IaC (Terraform/OpenTofu/CDK), FinOps cost optimization, and modern architectural patterns. Masters serverless, microservices, security, compliance, and disaster recovery. Use PROACTIVELY for cloud architecture, cost optimization, migration planning, or multi-cloud strategies. (file: /home/aidev/.codex/skills/cloud-architect/SKILL.md)
- code-reviewer: Use this skill to review code. It supports both local changes (staged or working tree) and remote Pull Requests (by ID or URL). It focuses on correctness, maintainability, and adherence to project standards. (file: /home/aidev/.agents/skills/code-reviewer/SKILL.md)
- code-reviewer: Elite code review expert specializing in modern AI-powered code analysis, security vulnerabilities, performance optimization, and production reliability. Masters static analysis tools, security scanning, and configuration review with 2024/2025 best practices. Use PROACTIVELY for code quality assurance. (file: /home/aidev/.codex/skills/code-reviewer/SKILL.md)
- codex-dev-loop-jira-to-pr: End-to-end dev loop: ticket -> branch -> implement -> tests -> commit -> PR-ready summary. (file: /home/aidev/.codex/skills/codex-dev-loop-jira-to-pr/SKILL.md)
- codex-failure-recovery-loop: Systematic recovery when tests fail or runtime errors appear. Repro-first, isolate, fix, verify, harden. (file: /home/aidev/.codex/skills/codex-failure-recovery-loop/SKILL.md)
- codex-framework-boundaries: Framework-aware context loading. Load only entrypoints + connected layers, never the whole repo. (file: /home/aidev/.codex/skills/codex-framework-boundaries/SKILL.md)
- codex-parallel-agents: Run parallel agents safely using worktrees + contract-first coordination. Includes synthesis + merge protocol. (file: /home/aidev/.codex/skills/codex-parallel-agents/SKILL.md)
- codex-progressive-prompting: Break large work into small, testable chunks (30–45 min). Enforces success criteria + verification at each step. (file: /home/aidev/.codex/skills/codex-progressive-prompting/SKILL.md)
- codex-synthesis-integrator: Merge multiple agent outputs into one coherent implementation with strict consistency and verification gates. (file: /home/aidev/.codex/skills/codex-synthesis-integrator/SKILL.md)
- component-architecture: Skill for component-architecture tasks. (file: /home/aidev/.codex/skills/component-architecture/SKILL.md)
- component-patterns: Skill for component-patterns tasks. (file: /home/aidev/.codex/skills/component-patterns/SKILL.md)
- component-scaffold: You are a React component architecture expert specializing in scaffolding production-ready, accessible, and performant components. Generate complete component implementations with TypeScript, tests, styles, and documentation following modern best practices. (file: /home/aidev/.codex/skills/component-scaffold/SKILL.md)
- compose-components: Skill for compose-components tasks. (file: /home/aidev/.codex/skills/compose-components/SKILL.md)
- conductor-validator: Validates Conductor project artifacts for completeness, consistency, and correctness. Use after setup, when diagnosing issues, or before implementation to verify project context. (file: /home/aidev/.codex/skills/conductor-validator/SKILL.md)
- config-validate: You are a configuration management expert specializing in validating, testing, and ensuring the correctness of application configurations. Create comprehensive validation schemas, implement configuration testing strategies, and ensure configurations are secure, consistent, and error-free across all environments. (file: /home/aidev/.codex/skills/config-validate/SKILL.md)
- content-marketer: Elite content marketing strategist specializing in AI-powered content creation, omnichannel distribution, SEO optimization, and data-driven performance marketing. Masters modern content tools, social media automation, and conversion optimization with 2024/2025 best practices. Use PROACTIVELY for comprehensive content marketing. (file: /home/aidev/.codex/skills/content-marketer/SKILL.md)
- create-component: Guided component creation with proper patterns (file: /home/aidev/.codex/skills/create-component/SKILL.md)
- css-styling-approaches: Skill for css-styling-approaches tasks. (file: /home/aidev/.codex/skills/css-styling-approaches/SKILL.md)
- data-driven-feature: Build features guided by data insights, A/B testing, and continuous measurement using specialized agents for analysis, implementation, and experimentation. (file: /home/aidev/.codex/skills/data-driven-feature/SKILL.md)
- data-engineer: Build scalable data pipelines, modern data warehouses, and real-time streaming architectures. Implements Apache Spark, dbt, Airflow, and cloud-native data platforms. Use PROACTIVELY for data pipeline design, analytics infrastructure, or modern data stack implementation. (file: /home/aidev/.codex/skills/data-engineer/SKILL.md)
- data-pipeline: You are a data pipeline architecture expert specializing in scalable, reliable, and cost-effective data pipelines for batch and streaming data processing. (file: /home/aidev/.codex/skills/data-pipeline/SKILL.md)
- data-scientist: Expert data scientist for advanced analytics, machine learning, and statistical modeling. Handles complex data analysis, predictive modeling, and business intelligence. Use PROACTIVELY for data analysis tasks, ML modeling, statistical analysis, and data-driven insights. (file: /home/aidev/.codex/skills/data-scientist/SKILL.md)
- data-sources: Skill for data-sources tasks. (file: /home/aidev/.codex/skills/data-sources/SKILL.md)
- database-admin: Expert database administrator specializing in modern cloud databases, automation, and reliability engineering. Masters AWS/Azure/GCP database services, Infrastructure as Code, high availability, disaster recovery, performance optimization, and compliance. Handles multi-cloud strategies, container databases, and cost optimization. Use PROACTIVELY for database architecture, operations, or reliability engineering. (file: /home/aidev/.codex/skills/database-admin/SKILL.md)
- database-architect: Expert database architect specializing in data layer design from scratch, technology selection, schema modeling, and scalable database architectures. Masters SQL/NoSQL/TimeSeries database selection, normalization strategies, migration planning, and performance-first design. Handles both greenfield architectures and re-architecture of existing systems. Use PROACTIVELY for database architecture, technology selection, or data modeling decisions. (file: /home/aidev/.codex/skills/database-architect/SKILL.md)
- database-optimizer: Expert database optimizer specializing in modern performance tuning, query optimization, and scalable architectures. Masters advanced indexing, N+1 resolution, multi-tier caching, partitioning strategies, and cloud database optimization. Handles complex query analysis, migration strategies, and performance monitoring. Use PROACTIVELY for database optimization, performance issues, or scalability challenges. (file: /home/aidev/.codex/skills/database-optimizer/SKILL.md)
- debug-trace: You are a debugging expert specializing in setting up comprehensive debugging environments, distributed tracing, and diagnostic tools. Configure debugging workflows, implement tracing solutions, and establish troubleshooting practices for development and production environments. (file: /home/aidev/.codex/skills/debug-trace/SKILL.md)
- debugger: Debugging specialist for errors, test failures, and unexpected behavior. Use proactively when encountering any issues. (file: /home/aidev/.codex/skills/debugger/SKILL.md)
- deployment-engineer: Expert deployment engineer specializing in modern CI/CD pipelines, GitOps workflows, and advanced deployment automation. Masters GitHub Actions, ArgoCD/Flux, progressive delivery, container security, and platform engineering. Handles zero-downtime deployments, security scanning, and developer experience optimization. Use PROACTIVELY for CI/CD design, GitOps implementation, or deployment automation. (file: /home/aidev/.codex/skills/deployment-engineer/SKILL.md)
- deployment-spec: Skill for deployment-spec tasks. (file: /home/aidev/.codex/skills/deployment-spec/SKILL.md)
- deps-audit: You are a dependency security expert specializing in vulnerability scanning, license compliance, and supply chain security. Analyze project dependencies for known vulnerabilities, licensing issues, outdated packages, and provide actionable remediation strategies. (file: /home/aidev/.codex/skills/deps-audit/SKILL.md)
- deps-upgrade: You are a dependency management expert specializing in safe, incremental upgrades of project dependencies. Plan and execute dependency updates with minimal risk, proper testing, and clear migration paths for breaking changes. (file: /home/aidev/.codex/skills/deps-upgrade/SKILL.md)
- design-review: Review existing UI for issues and improvements (file: /home/aidev/.codex/skills/design-review/SKILL.md)
- design-system-architect: Expert design system architect specializing in design tokens, component libraries, theming infrastructure, and scalable design operations. Masters token architecture, multi-brand systems, and design-development collaboration. Use PROACTIVELY when building design systems, creating token architectures, implementing theming, or establishing component libraries. (file: /home/aidev/.codex/skills/design-system-architect/SKILL.md)
- design-system-setup: Initialize a design system with tokens (file: /home/aidev/.codex/skills/design-system-setup/SKILL.md)
- design-tokens: Skill for design-tokens tasks. (file: /home/aidev/.codex/skills/design-tokens/SKILL.md)
- devops-troubleshooter: Expert DevOps troubleshooter specializing in rapid incident response, advanced debugging, and modern observability. Masters log analysis, distributed tracing, Kubernetes debugging, performance optimization, and root cause analysis. Handles production outages, system reliability, and preventive monitoring. Use PROACTIVELY for debugging, incident response, or system troubleshooting. (file: /home/aidev/.codex/skills/devops-troubleshooter/SKILL.md)
- docs-writer: Always use this skill when the task involves writing, reviewing, or editing documentation, specifically for any files in the `/docs` directory or any `.md` files in the repository. (file: /home/aidev/.agents/skills/docs-writer/SKILL.md)
- error-analysis: You are an expert error analysis specialist with deep expertise in debugging distributed systems, analyzing production incidents, and implementing comprehensive observability solutions. (file: /home/aidev/.codex/skills/error-analysis/SKILL.md)
- error-detective: Search logs and codebases for error patterns, stack traces, and anomalies. Correlates errors across systems and identifies root causes. Use PROACTIVELY when debugging issues, analyzing logs, or investigating production errors. (file: /home/aidev/.codex/skills/error-detective/SKILL.md)
- error-trace: You are an error tracking and observability expert specializing in implementing comprehensive error monitoring solutions. Set up error tracking systems, configure alerts, implement structured logging, and ensure teams can quickly identify and resolve production issues. (file: /home/aidev/.codex/skills/error-trace/SKILL.md)
- event-sourcing-architect: Expert in event sourcing, CQRS, and event-driven architecture patterns. Masters event store design, projection building, saga orchestration, and eventual consistency patterns. Use PROACTIVELY for event-sourced systems, audit trail requirements, or complex domain modeling with temporal queries. (file: /home/aidev/.codex/skills/event-sourcing-architect/SKILL.md)
- executing-plans: Use when you have a written implementation plan to execute in a separate session with review checkpoints (file: /home/aidev/.codex/skills/executing-plans/SKILL.md)
- fastapi-pro: Build high-performance async APIs with FastAPI, SQLAlchemy 2.0, and Pydantic V2. Master microservices, WebSockets, and modern Python async patterns. Use PROACTIVELY for FastAPI development, async optimization, or API architecture. (file: /home/aidev/.codex/skills/fastapi-pro/SKILL.md)
- feature-development: Orchestrate end-to-end feature development from requirements to production deployment: (file: /home/aidev/.codex/skills/feature-development/SKILL.md)
- few-shot-learning: Skill for few-shot-learning tasks. (file: /home/aidev/.codex/skills/few-shot-learning/SKILL.md)
- finishing-a-development-branch: Use when implementation is complete, all tests pass, and you need to decide how to integrate the work - guides completion of development work by presenting structured options for merge, PR, or cleanup (file: /home/aidev/.codex/skills/finishing-a-development-branch/SKILL.md)
- frontend-developer: Build React components, implement responsive layouts, and handle client-side state management. Masters React 19, Next.js 15, and modern frontend architecture. Optimizes performance and ensures accessibility. Use PROACTIVELY when creating UI components or fixing frontend issues. (file: /home/aidev/.codex/skills/frontend-developer/SKILL.md)
- frontend-security-coder: Expert in secure frontend coding practices specializing in XSS prevention, output sanitization, and client-side security patterns. Use PROACTIVELY for frontend security implementations or client-side security code reviews. (file: /home/aidev/.codex/skills/frontend-security-coder/SKILL.md)
- full-review: Orchestrate comprehensive multi-dimensional code review using specialized review agents (file: /home/aidev/.codex/skills/full-review/SKILL.md)
- full-stack-feature: Orchestrate full-stack feature development across backend, frontend, and infrastructure layers with modern API-first approach: (file: /home/aidev/.codex/skills/full-stack-feature/SKILL.md)
- graphql-architect: Master modern GraphQL with federation, performance optimization, and enterprise security. Build scalable schemas, implement advanced caching, and design real-time systems. Use PROACTIVELY for GraphQL architecture or performance optimization. (file: /home/aidev/.codex/skills/graphql-architect/SKILL.md)
- graphql-schema-design: Skill for graphql-schema-design tasks. (file: /home/aidev/.codex/skills/graphql-schema-design/SKILL.md)
- improve-agent: Systematic improvement of existing agents through performance analysis, prompt engineering, and continuous iteration. (file: /home/aidev/.codex/skills/improve-agent/SKILL.md)
- integration-testing: Skill for integration-testing tasks. (file: /home/aidev/.codex/skills/integration-testing/SKILL.md)
- java-pro: Master Java 21+ with modern features like virtual threads, pattern matching, and Spring Boot 3.x. Expert in the latest Java ecosystem including GraalVM, Project Loom, and cloud-native patterns. Use PROACTIVELY for Java development, microservices architecture, or performance optimization. (file: /home/aidev/.codex/skills/java-pro/SKILL.md)
- javascript: Skill for javascript tasks. (file: /home/aidev/.codex/skills/javascript/SKILL.md)
- javascript-pro: Master modern JavaScript with ES6+, async patterns, and Node.js APIs. Handles promises, event loops, and browser/Node compatibility. Use PROACTIVELY for JavaScript optimization, async debugging, or complex JS patterns. (file: /home/aidev/.codex/skills/javascript-pro/SKILL.md)
- multi-agent-optimize: AI-powered multi-agent performance engineering and optimization orchestration. (file: /home/aidev/.codex/skills/multi-agent-optimize/SKILL.md)
- multi-agent-review: Multi-agent code review orchestration across security, performance, and quality. (file: /home/aidev/.codex/skills/multi-agent-review/SKILL.md)
- performance-engineer: Expert performance engineer specializing in modern observability, application optimization, and scalable system performance. Masters OpenTelemetry, distributed tracing, load testing, multi-tier caching, Core Web Vitals, and performance monitoring. Handles end-to-end optimization, and scalability patterns. Use PROACTIVELY for performance optimization, observability, or scalability challenges. (file: /home/aidev/.codex/skills/performance-engineer/SKILL.md)
- performance-optimization: Optimize application performance end-to-end using specialized performance and optimization agents. (file: /home/aidev/.codex/skills/performance-optimization/SKILL.md)
- pr-creator: Use this skill when asked to create a pull request (PR). It ensures all PRs follow the repository's established templates and standards. (file: /home/aidev/.agents/skills/pr-creator/SKILL.md)
- product: Skill for product tasks. (file: /home/aidev/.codex/skills/product/SKILL.md)
- product-guidelines: Skill for product-guidelines tasks. (file: /home/aidev/.codex/skills/product-guidelines/SKILL.md)
- prompt-engineer: Expert prompt engineer specializing in advanced prompting techniques, LLM optimization, and AI system design. Masters chain-of-thought, constitutional AI, and production prompt strategies. Use when building AI features, improving agent performance, or crafting system prompts. (file: /home/aidev/.codex/skills/prompt-engineer/SKILL.md)
- prompt-optimization: Skill for prompt-optimization tasks. (file: /home/aidev/.codex/skills/prompt-optimization/SKILL.md)
- prompt-optimize: Optimize prompts for production with CoT, few-shot, and constitutional AI patterns (file: /home/aidev/.codex/skills/prompt-optimize/SKILL.md)
- prompt-template-library: Skill for prompt-template-library tasks. (file: /home/aidev/.codex/skills/prompt-template-library/SKILL.md)
- prompt-templates: Skill for prompt-templates tasks. (file: /home/aidev/.codex/skills/prompt-templates/SKILL.md)
- python: Skill for python tasks. (file: /home/aidev/.codex/skills/python/SKILL.md)
- python-expert: Master Python 3.12+ with modern features, async programming, performance optimization, and production-ready practices. Expert in uv, ruff, pydantic, and FastAPI. (file: /home/aidev/.codex/skills/python-expert/SKILL.md)
- python-pro: Master Python 3.12+ with modern features, async programming, performance optimization, and production-ready practices. Expert in the latest Python ecosystem including uv, ruff, pydantic, and FastAPI. Use PROACTIVELY for Python development, optimization, or advanced Python patterns. (file: /home/aidev/.codex/skills/python-pro/SKILL.md)
- python-scaffold: You are a Python project architecture expert specializing in scaffolding production-ready Python applications. Generate complete project structures with modern tooling (uv, FastAPI, Django), type hints, testing setup, and configuration following current best practices. (file: /home/aidev/.codex/skills/python-scaffold/SKILL.md)
- refactor-clean: You are a code refactoring expert specializing in clean code principles, SOLID design patterns, and modern software engineering best practices. Analyze and refactor the provided code to improve its quality, maintainability, and performance. (file: /home/aidev/.codex/skills/refactor-clean/SKILL.md)
- reference-builder: Creates exhaustive technical references and API documentation. Generates comprehensive parameter listings, configuration guides, and searchable reference materials. Use PROACTIVELY for API docs, configuration references, or complete technical specifications. (file: /home/aidev/.codex/skills/reference-builder/SKILL.md)
- reverse-engineer: Expert reverse engineer specializing in binary analysis, disassembly, decompilation, and software analysis. Masters IDA Pro, Ghidra, radare2, x64dbg, and modern RE toolchains. Handles executable analysis, library inspection, protocol extraction, and vulnerability research. Use PROACTIVELY for binary analysis, CTF challenges, security research, or understanding undocumented software. (file: /home/aidev/.codex/skills/reverse-engineer/SKILL.md)
- smart-fix: Intelligent issue resolution workflow with multi-agent orchestration. (file: /home/aidev/.codex/skills/smart-fix/SKILL.md)
- sql-migrations: SQL database migrations with zero-downtime strategies for PostgreSQL, MySQL, SQL Server (file: /home/aidev/.codex/skills/sql-migrations/SKILL.md)
- sql-pro: Master modern SQL with cloud-native databases, OLTP/OLAP optimization, and advanced query techniques. Expert in performance tuning, data modeling, and hybrid analytical systems. Use PROACTIVELY for database optimization or complex analysis. (file: /home/aidev/.codex/skills/sql-pro/SKILL.md)
- styling-patterns: Skill for styling-patterns tasks. (file: /home/aidev/.codex/skills/styling-patterns/SKILL.md)
- subagent-driven-development: Use when executing implementation plans with independent tasks in the current session (file: /home/aidev/.codex/skills/subagent-driven-development/SKILL.md)
- system-prompts: Skill for system-prompts tasks. (file: /home/aidev/.codex/skills/system-prompts/SKILL.md)
- ui-designer: Expert UI designer specializing in component creation, layout systems, and visual design implementation. Masters modern design patterns, responsive layouts, and design-to-code workflows. Use PROACTIVELY when building UI components, designing layouts, creating mockups, or implementing visual designs. (file: /home/aidev/.codex/skills/ui-designer/SKILL.md)
- ui-ux-designer: Create interface designs, wireframes, and design systems. Masters user research, accessibility standards, and modern design tools. Specializes in design tokens, component libraries, and inclusive design. Use PROACTIVELY for design systems, user flows, or interface optimization. (file: /home/aidev/.codex/skills/ui-ux-designer/SKILL.md)
- ui-visual-validator: Rigorous visual validation expert specializing in UI testing, design system compliance, and accessibility verification. Masters screenshot analysis, visual regression testing, and component validation. Use PROACTIVELY to verify UI modifications have achieved their intended goals through comprehensive visual analysis. (file: /home/aidev/.codex/skills/ui-visual-validator/SKILL.md)
- update-docs: This skill should be used when the user asks to "update documentation for my changes", "check docs for this PR", "what docs need updating", "sync docs with code", "scaffold docs for this feature", "document this feature", "review docs completeness", "add docs for this change", "what documentation is affected", "docs impact", or mentions "docs/", "docs/01-app", "docs/02-pages", "MDX", "documentation update", "API reference", ".mdx files". Provides guided workflow for updating Next.js documentation based on code changes. (file: /home/aidev/.agents/skills/update-docs/SKILL.md)
- using-git-worktrees: Use when starting feature work that needs isolation from current workspace or before executing implementation plans - creates isolated git worktrees with smart directory selection and safety verification (file: /home/aidev/.codex/skills/using-git-worktrees/SKILL.md)
- vector-database-engineer: Expert in vector databases, embedding strategies, and semantic search implementation. Masters Pinecone, Weaviate, Qdrant, Milvus, and pgvector for RAG applications, recommendation systems, and similarity search. Use PROACTIVELY for vector search implementation, embedding optimization, or semantic retrieval systems. (file: /home/aidev/.codex/skills/vector-database-engineer/SKILL.md)
- webapp-testing: Toolkit for interacting with and testing local web applications using Playwright. Supports verifying frontend functionality, debugging UI behavior, capturing browser screenshots, and viewing browser logs. (file: /home/aidev/.codex/skills/webapp-testing/SKILL.md)
- writing-plans: Use when you have a spec or requirements for a multi-step task, before touching code (file: /home/aidev/.codex/skills/writing-plans/SKILL.md)
- skill-creator: Guide for creating effective skills. This skill should be used when users want to create a new skill (or update an existing skill) that extends Codex's capabilities with specialized knowledge, workflows, or tool integrations. (file: /home/aidev/.codex/skills/.system/skill-creator/SKILL.md)
- skill-installer: Install Codex skills into $CODEX_HOME/skills from a curated list or a GitHub repo path. Use when a user asks to list installable skills, install a curated skill, or install a skill from another repo (including private repos). (file: /home/aidev/.codex/skills/.system/skill-installer/SKILL.md)

### How to use skills

Follow these rules to decide when and how to apply a skill.

Discovery:
- The list above is the skills available in this session (name + description +
  file path). Skill bodies live on disk at the listed paths.

Trigger rules:
- If the user names a skill (with `$SkillName` or plain text) OR the task
  clearly matches a skill's description shown above, you must use that skill for
  that turn. Multiple mentions mean use them all. Do not carry skills across
  turns unless re-mentioned.

Missing/blocked:
- If a named skill isn't in the list or the path can't be read, say so briefly
  and continue with the best fallback.

How to use a skill (progressive disclosure):
- After deciding to use a skill, open its `SKILL.md`. Read only enough to follow
  the workflow.
- When `SKILL.md` references relative paths (e.g., `scripts/foo.py`), resolve
  them relative to the skill directory listed above first, and only consider
  other paths if needed.
- If `SKILL.md` points to extra folders such as `references/`, load only the
  specific files needed for the request; don't bulk-load everything.
- If `scripts/` exist, prefer running or patching them instead of retyping large
  code blocks.
- If `assets/` or templates exist, reuse them instead of recreating from
  scratch.

Coordination and sequencing:
- If multiple skills apply, choose the minimal set that covers the request and
  state the order you'll use them.
- Announce which skill(s) you're using and why (one short line). If you skip an
  obvious skill, say why.

Context hygiene:
- Keep context small: summarize long sections instead of pasting them; only load
  extra files when needed.
- Avoid deep reference-chasing: prefer opening only files directly linked from
  `SKILL.md` unless you're blocked.

Safety and fallback:
- If a skill can't be applied cleanly (missing files, unclear instructions),
  state the issue, pick the next-best approach, and continue.
