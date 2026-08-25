# Runbook d'astreinte — Pyrenex Prod

> Pour l'équipe SRE Pyrenex. 4 procédures : déclenchement → actions →
> qui appeler → ce qu'on NE fait PAS.

---

## 1. Service KO (un conteneur down)

**Déclenchement** : `docker compose ps` montre un service `exited`,
ou panel « Vie » Grafana (`up{job=~"backend|model"}` = 0).

**Actions** :
1. `docker compose logs --tail=100 <service>` — lire l'erreur.
2. `docker compose restart <service>`.
3. Si KO après 2 essais : escalade.

**Qui appeler** : Astreinte FastIA.

**On NE fait PAS** : `docker compose down -v` (détruit les volumes).

---

## 2. Latence p95 dégradée

**Déclenchement** : panel « Vitesse » Grafana — p95 > 200 ms sur 5 min.
> Baseline mesurée à 95 ms en p95 via Prometheus sur l'endpoint `/score`
> du backend (20 requêtes de référence). Seuil fixé à 2× la baseline :
> au-delà, la dégradation est significative et nécessite intervention.

**Actions** :
1. `docker stats` — vérifier CPU/RAM des conteneurs.
2. `git log --oneline -5` — identifier un déploiement récent suspect.
3. `docker compose restart backend` si la charge est anormale.

**Qui appeler** : Astreinte FastIA.

**On NE fait PAS** : redéployer une version non testée en prod.

---

## 3. Métrique modèle qui s'écarte (distribution des prédictions anormale)

**Déclenchement** : panel « Comportement » Grafana — ratio
défaut/non-défaut s'écarte de > 20% de la baseline observée
(cf. `pyrenex_predictions_total{predicted_class=...}`).

**Actions** :
1. `docker compose logs --tail=100 model` — vérifier les erreurs.
2. Comparer les entrées récentes avec le jeu de référence
   (`data/reference_set.csv`).
3. Vérifier qu'aucun drift de données n'a été introduit
   (changement de schéma, valeurs hors bornes).

**Qui appeler** : Astreinte FastIA.

**On NE fait PAS** : modifier le modèle en prod sans évaluation continue (B2),
rollback possible.

---

## 4. Rollback de release

**Déclenchement** : taux d'erreurs 5xx > 5% sur 5 min,
ou tag de release défectueux identifié.

**Actions** :
1. `git tag --sort=-v:refname | head -5` — identifier le dernier tag stable.
2. `docker pull ghcr.io/<repo>-model:<tag>` puis `docker compose up --build`
   avec l'image du tag précédent.
3. Vérifier les healthchecks (`docker compose ps`) et `/metrics`.

**Qui appeler** : Astreinte FastIA.

**On NE fait PAS** : hotfix en prod sans test, `docker compose down -v`.
