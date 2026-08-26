# Seuils d'évaluation continue — Pyrenex scoring v2

> Ce document présente les seuils utilisés pour accepter ou bloquer une release.

Stratégie retenue : **hybride** (plancher absolu et baisse maximale par rapport au golden run).
Jeu de référence : `data/reference_set.csv`, composé de 250 prêts remboursés et 250 défauts tirés du holdout M1 avec `random_state=42`.

## Composition du jeu de référence

Le jeu est équilibré 250/250 afin de mesurer précisément la classe défaut, qui est la plus importante pour le risque crédit. Reproduire la production aurait fourni seulement environ 90 défauts sur 500 lignes et rendu le recall plus instable. Ce jeu est un instrument de mesure, pas une copie de la production.

## Stratégies considérées

- **Absolue** : simple, mais peut laisser passer une forte régression tant que le plancher est respecté.
- **Relative** : détecte une baisse face au golden run, mais ne garantit pas à elle seule une qualité minimale.
- **Hybride** : applique les deux règles. C'est la stratégie retenue pour garantir une qualité minimale tout en détectant les régressions.

## Deux baselines, à ne pas confondre

| | Mesurée sur | Sert à |
|---|---|---|
| **Baseline communiquée** (`metrics_holdout`) | le holdout M1 complet | ce qui a été annoncé au client |
| **Golden run** (`data/reference_baseline.json`) | le jeu de référence figé | arbitrer les releases |

Le garde-fou compare au golden run, jamais à la baseline communiquée : les deux jeux n'ont ni la même taille ni la même composition.

| Métrique | Golden run | Plancher absolu | Baisse max vs golden run | Justification |
|---|---:|---:|---:|---|
| F1 macro | 0,6760 | 0,55 | 0,044 | Refuse une forte baisse de la qualité générale du modèle. |
| F1 défaut | 0,6721 | 0,40 | 0,051 | Refuse que le modèle devienne mauvais spécifiquement sur les défauts. |
| ROC-AUC | 0,7135 | 0,65 | 0,048 | Maintient la capacité à distinguer les dossiers risqués des dossiers sûrs. |
| Recall défaut | 0,6640 | 0,60 | 0,062 | Exige de détecter au moins 60 % des défauts réels. |

## Bruit de mesure

| Métrique | σ bootstrap mesuré | 2 σ | Tolérance retenue |
|---|---:|---:|---:|
| F1 macro | 0,0215 | 0,0431 | 0,044 |
| F1 défaut | 0,0250 | 0,0500 | 0,051 |
| ROC-AUC | 0,0237 | 0,0473 | 0,048 |
| Recall défaut | 0,0307 | 0,0614 | 0,062 |

## Procédure de mise à jour des seuils

- **Qui** : Lead data (Sophie Léger) et/ou le responsable métier/gouvernance IA.
- **Quand** : lorsque le modèle de référence, le jeu de référence ou les exigences métier changent
- **Comment** : régénérer le jeu si nécessaire, regeler le golden run avec l'option --freeze-baseline, refaire le bootstrap, puis mettre à jour les seuils du script et ce document. Vérifier enfin un run normal avec un code retour 0 et un run dégradé avec un code retour 1.
