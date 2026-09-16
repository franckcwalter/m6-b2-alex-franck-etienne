# Décisions binôme — M6-B2 (À COMPLÉTER)

> **À remplir avant de coder.** Les briques forment une chaîne (feedback →
> stockage → jointure → réentraînement → promotion) : figer les contrats est ce
> qui vous permet d'avancer à deux en parallèle sans vous bloquer.

## Contrats d'interface (à figer en premier)

```text
Feedback   : {request_id: str, true_label: 0|1, comments: str|None}
Stockage   : table feedbacks(request_id PK, true_label, comments,
             created_at, used_for_training=0)
Comptage   : GET /feedback/count → {"count": int, "new": int}
Retrain    : python scripts/retrain.py --min-feedback N → exit 0
Promotion  : decide_promotion(candidate: dict, production: dict)
             → PromotionDecision(promote: bool, reason: str)
```

Modifications apportées à ces contrats en cours de route : _…_

## Trigger de réentraînement

**Seuil retenu : _200_** — justification : cela dépend de la fréquence à laquelle les feedbacks arrivent,
à réadapter en fonction de la fréquence des feedbacks. 
Est-ce pertinent de réentraîner plus souvent mais avec moins de données,
ou de réentrainer moins souvent avec beaucoup plus de données?

**On compte** : _les feedbacks non consommés (`used_for_training = 0`)_ —
pourquoi pas le total ? Pour que le cron ne relance pas un réentrapinement même si de nouveaux feedback ne sont pas arrivés

⭐ Second déclencheur « ou dérive confirmée » (bonus) : _traité / non traité_ —
si traité, quelle fonction de M6-B1 est appelée ? _…_

## Jeu de référence retenu (à figer AVANT tout le reste)

**Jeu adopté** : _reference_set.csv de M5-B2 de ____ (500 lignes, composition ____)

**Pourquoi** : notre plancher et nos tolérances ont été calibrés sur ce jeu.
Mesurer sur un autre jeu reviendrait à comparer deux populations : un modèle inchangé pourrait sembler progresser ou régresser.
Le jeu est équilibré 50/50 volontairement : avec seulement environ 90 défauts, le recall défaut serait trop instable pour arbitrer.

## Politique de promotion

**Notre règle :** on remplace le modèle en prod par le nouveau seulement si :
1. il n'est pas mauvais (il respecte nos minimums de M5-B2) ;
2. il ne détecte pas moins bien les défauts qu'avant ;
3. il est vraiment un peu meilleur, sinon ça ne sert à rien de le déployer.

| Paramètre | Valeur retenue | Justification |
|---|---|---|
| Métriques critiques | `recall_default` et `f1_macro` | Le recall défaut dit combien de mauvais payeurs on repère, c'est ce qui coûte de l'argent à Pyrenex. Le F1 macro vérifie que le modèle reste bon sur les deux classes, et pas seulement sur une. |
| Plancher de qualité | f1_macro ≥ 0,55, f1_default ≥ 0,40, roc_auc ≥ 0,65, recall_default ≥ 0,60 | Ce sont nos seuils de M5-B2. En dessous, le modèle est considéré comme cassé. |
| Tolérance de régression | recall_default : on accepte de perdre 0,01 maximum. f1_macro : 0,02 maximum. | Les scores bougent un peu d'un entraînement à l'autre, même sans vraie différence, donc on tolère une petite baisse. On est plus sévère sur le recall, parce que rater un mauvais payeur coûte cher. |
| Gain minimum exigé | +0,01 sur le recall défaut ou le F1 macro | Si le nouveau modèle n'est pas meilleur, ça ne vaut pas le coup de le mettre en prod. Limite : +0,01, c'est petit, on ne peut pas être sûrs que ce n'est pas juste du hasard. |

**Pourquoi le recall de la classe défaut est-il contraignant ?**
Si le modèle dit « il va rembourser » alors que la personne ne rembourse pas,
Pyrenex prête de l'argent et le perd. Refuser un bon client par erreur coûte
beaucoup moins cher : on perd juste les intérêts qu'on aurait gagnés.

**Pourquoi F1 macro plutôt que l'accuracy ?**
Il y a seulement environ 18 % de défauts dans les données. Un modèle qui répond
« il va rembourser » à tout le monde aurait 82 % d'accuracy, tout en ne repérant
aucun mauvais payeur. Le F1 macro, lui, montre tout de suite que ce modèle est nul.

## Politique de doublon sur les feedbacks

| Cas | Réponse retenue             | Justification                                              |
|---|-----------------------------|------------------------------------------------------------|
| `request_id` inconnu | refusé                      | dossier jamais scoré, donc le feedback ne servirait a rien |
| Même `request_id`, même label | accepté, mais ne rien faire | probablement le même feedback envoyé deux fois             |
| Même `request_id`, label différent | refusé                      | a trancher par un humain                                   |

## Résultat de notre exécution

**Décision obtenue** : _PROMOTE / REJECT_

| Métrique | Production | Candidat | Écart |
|---|---|---|---|
| f1_macro | _…_ | _…_ | _…_ |
| recall_default | _…_ | _…_ | _…_ |
| roc_auc | _…_ | _…_ | _…_ |

**Ce qu'on en conclut, en une phrase défendable devant Sophie Léger** : _…_

**Chemin de rejet démontré ?** _oui / non_ — comment : _…_

## RGPD

_… les feedbacks contiennent-ils de la PII ? 
Possiblement dans les comments, à surveiller

## Point de mi-parcours (jeudi 17h)

- État des briques : _…_
- **Switch des rôles** — qui reprend quoi : _…_
