# Agent Registry - SOSConn x OpenInfra

## 1) Skill Subagents (5)

1. `skills/system-architecture.skill.agent.md`
2. `skills/backend-coding.skill.agent.md`
3. `skills/frontend-coding.skill.agent.md`
4. `skills/integration-workflow.skill.agent.md`
5. `skills/deployment.skill.agent.md`

## 2) Tester Subagents (2)

1. `testers/api-integration.tester.agent.md`
2. `testers/ui-e2e.tester.agent.md`

## 3) Developer Subagents (10)

1. `developers/dev01-domain-model.agent.md`
2. `developers/dev02-emergency-api.agent.md`
3. `developers/dev03-data-ingest-vector.agent.md`
4. `developers/dev04-ai-eop-rag.agent.md`
5. `developers/dev05-realtime-map.agent.md`
6. `developers/dev06-notification-orchestrator.agent.md`
7. `developers/dev07-datacollector-sync.agent.md`
8. `developers/dev08-command-center-ui.agent.md`
9. `developers/dev09-security-rbac-audit.agent.md`
10. `developers/dev10-performance-reliability.agent.md`

## 4) DevOps Subagent (1)

1. `devops/devops-cloudflare-tunnel.agent.md`

## Parallel Execution Matrix

- Song song A: `dev01`, `dev02`, `dev03`, `dev04`.
- Song song B: `dev05`, `dev06`, `dev07`, `dev08`.
- Song song C: `dev09`, `dev10`, `devops`.
- QA song song: `api-integration tester` + `ui-e2e tester`.

## Handoff Rules

- Tester -> Developer: dùng bug report template YAML trong từng tester file.
- Developer -> Team: dùng patch handoff template YAML trong từng developer file.
- DevOps -> Team: dùng deployment report template trong devops file.
