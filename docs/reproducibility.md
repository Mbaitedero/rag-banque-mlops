# Dossier de reproductibilite

## Prerequis
Python 3.11, Git. Versions bornees dans `requirements.txt` (testees avec chromadb 1.5, mlflow 3.17, pytest 8.4, ruff 0.17).

## Reconstruire les resultats (Windows CMD, depuis la racine du depot)
```
py -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pytest tests/ -v --cov=src
python -m scripts.build_index --config A
python -m scripts.run_eval --config A
python -m scripts.run_eval --config B
python -m scripts.promote --config A
python -m scripts.promote --config A --approve
python -m src.app --role agent --question "Quel est le plafond de retrait de la carte Premium ?"
python -m src.monitoring
```
MLflow : `mlflow ui --backend-store-uri sqlite:///mlflow.db` puis http://127.0.0.1:5000

## Identifiants de version a noter dans le rapport
- hash du corpus : champ `corpus_hash` affiche par `scripts.build_index` et tag du run MLflow ;
- configuration de chunking et seuil : `params.yaml` (commit Git) ;
- baseline : `eval/baseline.json` ; metriques : `eval/results/metrics_<config>.json`.

## Versionner le corpus avec DVC (facultatif)
```
pip install -r requirements-optional.txt
dvc init
dvc remote add -d localstore C:\dvc-store\rag-banque
dvc add data/raw
git add data/raw.dvc data/.gitignore .dvc
git commit -m "data: corpus-v1" && git tag corpus-v1
dvc repro
```

## Utiliser un modele d'embeddings semantique
Dans `params.yaml` : `embeddings.provider: "sentence-transformers"` (installer `requirements-optional.txt`, premier lancement avec acces a Internet pour telecharger le modele). **Recalibrez** `retrieval.min_score` et relancez l'evaluation : les scores ne sont pas comparables a ceux du modele lexical. Ce chemin n'a pas ete execute dans l'environnement de test.

## Utiliser un LLM
`llm.provider: "groq"` avec `GROQ_API_KEY` dans `.env` (non commite), ou `"ollama"` avec un modele local. Renseigner `llm.model`. Ces chemins n'ont pas ete executes dans l'environnement de test.
