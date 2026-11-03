# Analyse des risques et gouvernance

| Risque | Mesure en place | Test / preuve | Limite connue |
|---|---|---|---|
| Reponse non fondee | Seuil de score (`retrieval.min_score`), consigne de refus, references obligatoires | `test_rag.py`, metrique `refusal_accuracy` | Le seuil est calibre sur le jeu d'evaluation : le recalibrer sur un jeu independant. 1 question hors perimetre (q040) recoit quand meme une reponse issue de la FAQ publique. |
| Document obsolete | `status` dans l'inventaire ; les documents obsoletes ne sont pas indexes | `test_obsolete_documents_are_not_indexed` | Un document actif peut etre perime sans etre marque : revue periodique du corpus. |
| Documents contradictoires | Colonne `notes` de l'inventaire, consigne de signaler la contradiction, categorie `contradiction` dans l'evaluation | metrique `keyword_hit_rate` | Le LLM extractif ne signale pas les contradictions ; a verifier manuellement avec un LLM generatif (FAQ : 10 jours / guide : 15 jours). |
| Fuite d'un document reserve | Filtre `access_level` **dans** la requete vectorielle ; refus par defaut des roles inconnus | `test_access.py` (cas autorise, cas refuse, contexte du LLM), metrique `access_violations = 0` | Les roles sont fictifs ; en production, relier a l'authentification reelle. |
| Prompt injection documentaire | Sanitisation a l'ingestion et a la requete (`src/security.py`), consigne de ne pas executer les instructions du contexte, document piege (canari `CANARY-7731`) | `test_injection.py`, questions `injection` | Detection par motifs : une reformulation inedite peut passer. Complete, ne remplace pas, la revue des sources. |
| Dependance aux sources | Inventaire (source, licence, version, date), hash du corpus | `test_data.py`, `corpus_hash` | |
| Secrets exposes | Cle API dans `.env` (ignore par Git), `.env.example` fourni, journaux sans texte de question | revue du depot | |
| Mauvaise lecture des metriques | Metriques par categorie, limites ecrites dans la model card | `docs/model_card.md` | recall@4 vaut 1,0 car l'index ne contient que 22 chunks : non discriminant. |

# Politique de sécurité et exceptions de vulnérabilités

Ce document liste les vulnérabilités volontairement ignorées par `pip-audit`
dans la CI, avec leur justification et la condition de leur révision.

## Contexte

Le pipeline DVC utilise un backend **Google Drive** via l'extension
`dvc-gdrive`, qui dépend de `pydrive2`. Or, `pydrive2` verrouille strictement
`cryptography < 44` et `pyOpenSSL <= 24.2.1` (contrainte maintenue dans toutes
les versions publiées, y compris la dernière `1.21.3`).

Ces versions sont précisément celles signalées comme vulnérables par
`pip-audit`, et il est **techniquement impossible de les mettre à jour** sans
casser la compatibilité avec Google Drive. La seule alternative structurelle
serait de changer de backend de stockage DVC (S3, GCS, Azure, SSH, etc.), ce
qui est hors périmètre à court terme.

Les exceptions ci-dessous sont donc documentées, justifiées et **doivent être
revues à chaque montée de version de `pydrive2` ou de DVC**.

## Liste des exceptions

### Groupe A — `pyOpenSSL 24.2.1` et `cryptography 43.0.3`

Versions bloquées par `pydrive2`. Aucune version corrigée compatible n'existe.

| ID | Paquet | Justification |
|----|--------|---------------|
| `PYSEC-2026-2268` | pyOpenSSL 24.2.1 | Contournement TLS via exception dans `set_tlsext_servername_callback`. `pydrive2` n'utilise pas ce callback (API OAuth de haut niveau uniquement). Risque non exploitable dans notre usage. |
| `PYSEC-2026-2269` | pyOpenSSL 24.2.1 | Débordement de tampon dans le callback cookie DTLS. Même raisonnement : callback non utilisé par `pydrive2`. |
| `PYSEC-2026-1284` | cryptography 43.0.3 | Vulnérabilité OpenSSL incluse dans les wheels. Correctif en 44.0.1, incompatible avec `pydrive2`. |
| `PYSEC-2026-2141` | cryptography 43.0.3 | Correctif en 46.0.5, incompatible avec `pydrive2`. |
| `PYSEC-2026-35` | cryptography 43.0.3 | Correctif en 46.0.6, incompatible avec `pydrive2`. |
| `PYSEC-2026-3553` | cryptography 43.0.3 | Correctif en 49.0.0, incompatible avec `pydrive2`. |
| `PYSEC-2026-3554` | cryptography 43.0.3 | Correctif en 49.0.0, incompatible avec `pydrive2`. |
| `GHSA-537c-gmf6-5ccf` | cryptography 43.0.3 | Correctif en 48.0.1, incompatible avec `pydrive2`. |

**Condition de révision** : dès qu'une version de `pydrive2` publie des
contraintes assouplies (`cryptography >= 44` ou `pyOpenSSL >= 26`),
mettre à jour et retirer ces exceptions.

Référence à suivre : https://github.com/iterative/PyDrive2/issues

### Groupe B — `asyncssh 2.19.0`

Version bloquée pour rester compatible avec `cryptography 43.0.3`. `asyncssh`
est une dépendance transitive de `scmrepo` (utilisée par DVC pour les remotes
SSH), mais **nous n'utilisons pas de remote SSH** (uniquement Google Drive).
La bibliothèque n'est donc jamais sollicitée à l'exécution.

| ID | Paquet | Justification |
|----|--------|---------------|
| `PYSEC-2026-3808` | asyncssh 2.19.0 | Non utilisé en runtime (pas de remote SSH). Correctif en 2.23.1 nécessiterait `cryptography >= 48`, incompatible avec `pydrive2`. |
| `PYSEC-2026-4026` | asyncssh 2.19.0 | Même justification. Correctif en 2.24.0 incompatible avec `pydrive2`. |

**Condition de révision** : si un remote SSH est ajouté, ou si `pydrive2`
assouplit ses contraintes, mettre à jour `asyncssh`.

### Groupe C — `diskcache 5.6.3`

| ID | Paquet | Justification |
|----|--------|---------------|
| `PYSEC-2026-2447` | diskcache 5.6.3 | Aucune version corrigée disponible à ce jour. Dépendance transitive de `dvc-data`. Pas de mitigation possible sans fork. |

**Condition de révision** : surveiller la publication d'une version
corrigée de `diskcache`.

### Groupe D — Exceptions préexistantes

| ID | Justification |
|----|---------------|
| `PYSEC-2026-1845` | Exception historique documentée avant ce fichier. À revoir. |
| `PYSEC-2026-311` | Exception historique documentée avant ce fichier. À revoir. |
| `PYSEC-2026-3813` | Exception historique documentée avant ce fichier. À revoir. |
| `PYSEC-2026-3814` | Exception historique documentée avant ce fichier. À revoir. |
| `PYSEC-2026-3815` | Exception historique documentée avant ce fichier. À revoir. |

## Procédure de révision trimestrielle

1. Vérifier les dernières versions de `pydrive2`, `dvc-gdrive`, `dvc`.
2. Exécuter localement `pip-audit` sans les `--ignore-vuln` pour lister
   les vulnérabilités réellement présentes.
3. Pour chaque exception levée, retirer la ligne correspondante dans
   `.github/workflows/ci.yml` et mettre à jour les versions dans l'étape
   `Install DVC with compatible Google Drive dependencies`.
4. Mettre à jour ce fichier `SECURITY.md`.

## Alternatives structurelles envisagées

- **Migrer vers S3 / GCS / Azure / SSH** : supprime la dépendance à
  `pydrive2` et permet d'utiliser `cryptography` et `pyOpenSSL` à jour.
  Solution recommandée à moyen terme.
- **Isoler DVC dans un venv dédié** : confine les dépendances à risque
  hors de l'environnement principal audité.

## Supervision humaine
- Aucune operation metier n'est exposee : l'assistant ne fait que repondre.
- Toute promotion (`scripts/promote.py --approve`) exige que les gates passent **et** une approbation explicite.

## Exceptions pip-audit (a justifier avant remise)
- `PYSEC-2026-1845` (pytest 8.4.2) : dependance de test uniquement, absente d'un deploiement. Correctif en 9.0.3 ; non applique si la borne du cours impose pytest < 9.
- `PYSEC-2026-311`, `3813`, `3814`, `3815` (chromadb) : **lors de mon test, aucune version corrigee n'etait indiquee**. Je n'ai pas analyse le contenu des avis. Lisez-les sur osv.dev : si ils concernent un mode non utilise ici (serveur HTTP au lieu du client local `PersistentClient`), documentez-le ici ; sinon, changez de version ou de base vectorielle. **Ne laissez pas ces exceptions sans analyse dans le rapport final.**
