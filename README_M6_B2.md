# M6-B2 — Implémenter la boucle de rétroaction complète (Pyrenex, binôme)

> ⚠️ **Ce repo n'est pas un projet autonome — c'est un layer additif.**
> Il n'a **ni `docker-compose.yml`, ni Prometheus, ni Grafana, ni service model,
> ni backend**. Vous ne pouvez rien démarrer avec lui seul.
>
> **La base, c'est votre repo binôme M5-B1** : c'est lui qui porte la stack, la CI
> vers GHCR et votre `evaluate_model.py`. Travaillez-y sur une branche
> `m6-b2-boucle`, et **déposez-y quatre choses prises ici** : `services/feedback/`,
> `scripts/retrain` + `promotion`, `data/feedbacks_simules.csv`, et le job
> `auto-retrain-trigger` du `ci.yml`.
>
> Vous pouvez aussi faire **« Use this template »** → `M6-B2-pyrenex-boucle-<binome>`
> pour repartir propre, mais il faudra y rapatrier une douzaine d'éléments depuis M5
> (compose, prometheus/, grafana/, les 3 services, `evaluate_model.py`, votre jeu de
> référence et vos seuils) et fusionner les deux `ci.yml`. Comptez une heure.
>
> Vous restez avec le binôme de M6-B1 : vous continuez sur votre diagnostic.

---

## 🧭 Votre brief en un coup d'œil

**Ce README est votre document de pilotage unique.** Les autres supports ont
chacun un rôle précis :

| Support | Rôle |
|---|---|
| **Simplonline** | Le contrat : contexte client, livrables, critères de performance |
| **Ce README** | Le pilotage : quoi faire, quand, avec quel mini-cours |
| [`ressources/`](./ressources/) | Les 5 mini-cours d'appui (index dans [`ressources/README.md`](./ressources/README.md)) |
| **Discord `fil-M6-B2`** | Questions communes (MP binôme pour la coordination) |

### L'async binôme (jeudi + vendredi matin, 6 h)

| Quand | Étape | Durée | Appui |
|---|---|---|---|
| Jeudi | 1. Setup (repo, branche `m6-b2-boucle`) | 15 min | — |
| Jeudi | 2. Discussion stratégique → `decisions.md` (stockage, seuil, interfaces) | 30 min | [`05_Politique_promotion_defendre`](./ressources/05_Politique_promotion_defendre_essentiel.md) |
| Jeudi | 3. Implémentation de la boucle (briques A→E ci-dessous) | ~4h | `01` → `04` |
| Jeudi 17h | 4. **Point binôme + switch des rôles** (collecte ↔ promotion) | 15 min | — |
| Vendredi 9h | 5. Intégration bout en bout (feedbacks injectés → décision journalisée) | 1h | [`04_Reentrainement_auto`](./ressources/04_Reentrainement_auto_essentiel.md) |
| Vendredi 10h | 6. README + démo préparée | 30 min | — |
| Vendredi PM | RDV individuel 30 min — votre politique de promotion | — | — |

> 🎤 **Restitution : on confronte les décisions, pas les démos** — en ouverture
> du module suivant, chaque binôme défend sa politique de promotion. Vous
> n'aurez pas tous le même verdict, et c'est exactement le sujet.

### ✅ Checklist livrables (avant vendredi 17h)

- [ ] `/feedback` accepte ≥ 200 annotations ; `request_id` inconnu → 404 ;
      feedback contradictoire → 409 ; rejeu à l'identique → sans doublon
- [ ] Réentraînement **sur seuil de feedbacks non consommés** (199 → rien, 200 → trigger)
- [ ] Le **candidat** est écrit séparément ; `v2.1.0` n'existe **que** s'il est promu
- [ ] La décision est une **fonction testée sur métriques mockées** (un cas
      promu, un cas rejeté), chaque exécution **journalisée**
- [ ] Chaîne CI/CD M5 récupère le tag → Grafana voit v2.1.0
- [ ] `decisions.md` rempli **avant** de coder (stockage / trigger / seuils / interfaces)
- [ ] **Les deux membres** ont contribué, switch des rôles visible dans les
      commits, **journal de bord**
- [ ] `pytest -q` vert (les tests fournis se durcissent avec vos TODO — ajoutez
      les vôtres sur votre politique)

## 🚀 Démarrage

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -q tests                                   # vert dès le clone ; se durcit avec vos TODO
python scripts/retrain.py --min-feedback 200      # une fois retrain.py complété
```

> Variante `uv` : `uv venv .venv && source .venv/bin/activate` puis
> `uv pip install -r requirements.txt`.
> Dépannage : `No module named pip` → vous êtes dans un venv créé par `uv`,
> utilisez `uv pip install …` (pas `pip install`).

Données fournies : `data/feedbacks_simules.csv` (200 à injecter), `prod_scored.csv`,
`lending_club_train.csv`, `reference_set.csv`. Modèle de base : `models/pyrenex_risk_v2.joblib`.

> ⚠️ **Premier geste : trancher le jeu de référence.** Le `data/reference_set.csv`
> livré ici fait **1500 lignes (17,5 % de défauts)** — ce n'est **pas** celui de
> votre M5-B2 (500 lignes). Or le plancher de votre politique de promotion vient
> de vos **seuils M5-B2**, calibrés sur *votre* jeu. Par défaut : **remplacez ce
> fichier par le vôtre**. Sinon, regelez le golden run et refaites le bootstrap.
> Décision + raison dans `decisions.md` (section « Jeu de référence retenu »).

## 🧭 Ce que vous construisez

Vous construisez **la boucle entière**, à deux. Répartissez-vous les briques,
mais **switchez à mi-parcours** : à la fin, chacun doit avoir écrit la partie
qui compte — la **décision de promotion**. En soutenance de certification, vous
serez seul·e à expliquer cette boucle.

| | Brique | Dépend de | Fichier | Mini-cours |
|---|---|---|---|---|
| **A** | **La décision de promotion** — `decide_promotion()`, la règle qui autorise le déploiement | **rien** — testable sur des métriques inventées | `scripts/promotion_TEMPLATE.py` | `04`, `05` |
| **B** | Endpoint `POST /feedback` : valide, stocke, 404 / 409 / idempotent | rien | `services/feedback/` | `01` |
| **C** | Stockage SQLite + `used_for_training` + comptage des **non consommés** | B | (idem) | `02` |
| **D** | Réentraînement : données → **candidat** → évaluation → appelle A | C et A | `scripts/retrain_TEMPLATE.py` | `04` |
| **E** | Trigger cron / `workflow_dispatch` + CI/CD | D | `crontab_TEMPLATE.txt`, `.github/workflows/ci.yml` | `03` |

> 🧭 **L'ordre des lettres est l'ordre de construction — pas celui du schéma
> d'architecture.** Le schéma décrit un flux ; on construit **du plus testable au
> plus dépendant**. La décision de promotion ne dépend de rien : ni base, ni modèle,
> ni feedback. Commencez par elle, et **chacun de vous deux** doit l'avoir écrite.

> ❓ **« Comment figer un seuil avant d'avoir vu le résultat du réentraînement ? »**
> Votre seuil ne vient pas du résultat. Le plancher absolu vient de vos **seuils
> M5-B2** ; la tolérance et le gain minimum viennent du **coût métier** d'une
> régression chez Pyrenex. Un seuil fixé après coup n'est plus un garde-fou, c'est
> une justification.

> ⚠️ **Deux questions distinctes.** Le **trigger** répond à *« pourquoi
> réentraîner ? »*. La **promotion** répond à *« pourquoi déployer ? »*. Un
> réentraînement déclenché n'implique aucune mise en production : rejeter un
> candidat est une issue normale, tracée et défendable.

> Contrats d'interface, seuils et politique de promotion : à figer dans
> `decisions_TEMPLATE.md` **avant** de coder.

## ⭐ Extension (non notée, si socle bouclé) — l'écart est-il du bruit ?

Votre politique compare candidat et prod sur le **même** jeu de référence —
mais un écart de 0,004 en F1 est-il un **vrai** gain ou du bruit
d'échantillonnage ? **Bootstrapez le jeu de référence** (≥ 500 rééchantillons)
pour attacher un écart-type σ à chaque métrique, puis ré-exprimez votre
`TOLERANCE` et votre `MIN_GAIN` **en unités de σ** (rappel M5-B2 : une
tolérance relative se cale à ≥ 2 σ). Votre `reason` de promotion doit alors
dire si l'écart observé est **distinguable du bruit** — et votre plancher
absolu, lui, reste un choix **métier** : ce sont deux justifications de
natures différentes, à documenter toutes les deux dans `decisions.md`.

## 📚 Ressources

Voir [`./ressources/`](./ressources/) — 5 mini-cours + `liens_officiels.md`.
