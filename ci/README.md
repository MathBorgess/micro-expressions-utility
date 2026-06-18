# CI — Gates do Harness (execução local)

Os gates rodam localmente (decisão de setup). Migração para GitHub Actions é possível depois.

| Script | O que faz | Gate |
|---|---|---|
| `ci/validate_requirements.py` | Valida deps diretas contra a allowlist | REQ-010 |
| `ci/run_tests.sh` | allowlist → ruff → ruff format → mypy strict → pytest+cobertura | REQ-002/003 |
| `ci/mprof_check.sh` | Telemetria de memória (stub até o Sprint 2) | REQ-006 |

## Rodar tudo

```bash
bash ci/run_tests.sh
```

## Sandbox restrita (4 GB / 2 CPUs)

```bash
docker compose -f docker-compose.harness.yml up --build
```

Critérios (matriz Go/No-Go): `mypy --strict` zero erros · cobertura ≥ 70% · 100% dos testes ·
CI < 5 min · E2E < 3 min (Sprint 4) · RAM < 2.5 GB (Sprint 2) · deps na allowlist.
