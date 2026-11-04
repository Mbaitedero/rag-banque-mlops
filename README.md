# RAG multi-sources pour une banque (mini-projet MLOps, projet 2)

Assistant documentaire de **MBAITEDERO BANK**, une banque fictive : il répond à partir de plusieurs sources (FAQ, guides, PDF, procédures internes), cite ses références, refuse hors périmètre et applique un **contrôle d'accès avant le retrieval**. Le tout est versionné, évalué, testé, instrumenté (MLflow) et vérifié en CI.

> Tous les documents sont **fictifs**. N'ajoutez jamais de documents internes réels d'une banque ou d'un client.

## Architecture (index vectoriel unique)

```
data/raw (public + internal)
  -> ingest (extraction, provenance) -> clean (en-têtes/pieds, doublons, injection)
  -> chunking (config A/B, métadonnées, chunk_id stable) -> embeddings -> index Chroma unique

question + rôle -> filtre access_level DANS la requête vectorielle -> top-k
  -> seuil de score (sinon refus) -> sanitisation -> LLM -> réponse + références + journal JSON
```

## Démarrage rapide (Windows CMD)

```
py -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt

pytest tests/ -v --cov=src                          :: tests RAG et API
python -m scripts.build_index --config A            :: construit l'index + run MLflow
python -m scripts.run_eval --config A               :: évalue 47 questions + gates
python -m src.app --role agent --question "Quel est le plafond de retrait de la carte Premium ?"
python -m src.app --role agent --question "Quelle est la procédure KYC renforcée ?"      :: refusé
python -m src.app --role conformite --question "Quelle est la procédure KYC renforcée ?" :: autorisé
python -m src.monitoring                            :: résumé du journal
mlflow ui --backend-store-uri sqlite:///mlflow.db
```

Par défaut le projet fonctionne **sans réseau ni API** : embeddings lexicaux déterministes (`hash`) et LLM extractif. Ce mode sert à la CI et à mesurer le retrieval. Pour un usage réel, voir `docs/reproducibility.md` (embeddings sémantiques, Groq ou Ollama).

## Lancer le frontend et l'API FastAPI

Depuis la racine du dépôt, après avoir activé `.venv` et installé `requirements.txt`, construire l'index une seule fois s'il n'existe pas encore :

```
python -m scripts.build_index --config A
```

Puis démarrer l'API :

```
uvicorn src.api:app --reload --host 127.0.0.1 --port 8000
```

Dans un second terminal :

```
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Ouvrir `http://localhost:3000`. Le frontend utilise `frontend/.env.local` pour appeler `http://127.0.0.1:8000`; le mode mock est désactivé par défaut. L'API expose `POST /api/chat` (JSON ou SSE), `POST /api/feedback` et `GET /api/health`. Elle appelle le pipeline RAG existant sans modifier le retrieval, les seuils ou les permissions. CORS est limité par défaut aux origines locales `localhost:3000` et `127.0.0.1:3000`; `FRONTEND_ORIGINS` permet de remplacer cette liste.

Le sélecteur Agent/Conformité sert uniquement à la démonstration et n'est pas une authentification. Ne publiez pas cette API comme service de production sans ajouter une authentification serveur et un contrôle de rôle fiable. Le prénom d'affichage facultatif reste en mémoire dans la page et n'est pas envoyé au backend.

## Rôle des fichiers

| Chemin | Rôle |
|---|---|
| `params.yaml` | Source unique des paramètres (chunking A/B, embeddings, seuils, gates) |
| `data/raw/` | Corpus : `public/` et `internal/` |
| `data/inventory.csv` | Inventaire : doc_id, source, licence, version, date, type, access_level, status |
| `data/users.yaml` | Rôles fictifs (`agent`, `conformite`) et niveaux d'accès |
| `src/ingest.py` `clean.py` | Extraction (MD, PDF) avec provenance ; nettoyage reproductible |
| `src/chunking.py` | Découpage, métadonnées héritées, `chunk_id` déterministe |
| `src/embeddings.py` `index.py` | Embeddings (hash ou sentence-transformers), index Chroma |
| `src/access.py` `retriever.py` | Table rôle → niveaux ; retrieval avec filtre dans la requête |
| `src/security.py` | Détection et retrait des phrases d'injection |
| `src/prompts.py` `llm.py` `rag.py` | Prompt, fournisseurs LLM, pipeline complet avec refus |
| `src/api.py` | API FastAPI : chat JSON/SSE, feedback et état de santé |
| `src/evaluation.py` | Métriques et quality gates |
| `src/monitoring.py` `logging_utils.py` | Journal JSON (question hachée) et résumé |
| `src/tracking.py` | Journalisation MLflow (SQLite local par défaut) |
| `scripts/` | `build_index`, `run_eval`, `promote` |
| `eval/questions.jsonl` | 47 questions annotées (standard, ambiguës, hors corpus, accès refusé, contradiction, injection) |
| `eval/baseline.json` | Baseline de la configuration A (référence de non-régression) |
| `tests/` | Données, chunking, provenance, accès, retrieval, injection, régression |
| `docs/` | Cadrage, risques, fiche de version, reproductibilité |
| `.github/workflows/ci.yml` | CI : ruff, pytest + couverture, bandit, pip-audit |
| `dvc.yaml` | Pipeline reproductible (facultatif) |

## État de validation (mesuré avant remise)

- `ruff check .` : OK. `bandit -r src scripts` : aucun problème.
- `pytest` : tests backend et API (48 tests dans la dernière suite complète).
- Évaluation (config A) : recall@4 1,00 ; refus correct 0,98 ; références valides 1,00 ; 0 violation d'accès ; 0 fuite du canari.
- `pip-audit` : signale pytest (borne du cours) et **chromadb (4 avis sans version corrigée lors du test)**. À analyser : voir `docs/risk_report.md`.

## Ce qui n'a pas été exécuté ici
Embeddings `sentence-transformers`, appels Groq/Ollama, DVC, GitHub Actions réel, et exécution sous Windows. Le code correspondant est fourni mais non testé.

## Limites à assumer dans le rapport
Corpus petit et fictif (recall trivial), jeu d'évaluation et seuil calibrés par le même auteur, aucun LLM génératif évalué, contradictions non traitées automatiquement. Voir `docs/model_card.md`.
