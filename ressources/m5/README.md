# Ressources d'appui — M5 (Pyrenex Prod)

Mini-cours en **lecture juste-à-temps** : ouvrez celui de la tâche en cours,
pas tout d'un coup. Chacun ~20-30 min, avec exemple qui tourne + exercice.

## Ordre de mobilisation

### M5-B1 — architecture, CI/CD, monitoring (sync binôme)

| Quand | Mini-cours | Objectif |
|---|---|---|
| Au démarrage, organisation binôme | [`06_Pair_coding_sync_long`](m5/06_Pair_coding_sync_long_essentiel.md) | Répartir le travail, conventions Git duo |
| Orchestration des 3 services | [`01_Docker_compose_multiservices`](m5/01_Docker_compose_multiservices_essentiel.md) | Compose, réseau interne, healthchecks |
| Exposer les métriques | [`02_FastAPI_metrics_Prometheus`](m5/02_FastAPI_metrics_Prometheus_essentiel.md) | `/metrics`, métriques métier |
| Visualiser | [`04_Grafana_dashboard_custom`](m5/04_Grafana_dashboard_custom_essentiel.md) | Dashboard provisionné, PromQL |
| Pipeline | [`03_GitHub_Actions_CI_CD`](m5/03_GitHub_Actions_CI_CD_essentiel.md) | Tests → build → push, garde-fous |
| Astreinte | [`05_Runbook_astreinte`](m5/05_Runbook_astreinte_essentiel.md) | 4 procédures opérationnelles |

### M5-B2 — évaluation continue + MLflow (async individuel)

| Quand | Mini-cours | Objectif |
|---|---|---|
| Tracer les performances | [`07_MLflow_tracking`](m5/07_MLflow_tracking_essentiel.md) | Runs, params/metrics, UI de comparaison |
| Bloquer les régressions | [`08_Evaluation_continue_seuils`](m5/08_Evaluation_continue_seuils_essentiel.md) | Jeu de référence, seuils, exit code CI |

## Liens externes

[`liens_officiels.md`](liens_officiels.md) — docs officielles vérifiées.
