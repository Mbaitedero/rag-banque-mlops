# Cadrage (section 11 du cahier des charges)

1. **Quel probleme precis ?** Un assistant documentaire pour le personnel d'une banque **fictive** (Banque Atlas) repond a partir de FAQ, guides, tarifs, conditions generales et procedures internes. Il cite ses sources, refuse hors perimetre et ne montre jamais un document reserve a un role non autorise.
2. **Donnees et droits ?** 11 documents **fictifs crees pour le projet** (aucun document reel de banque ou de client). Remplacer ou completer par des documents publics reels n'est possible qu'en verifiant leur licence (colonne `license` de `data/inventory.csv`).
3. **Resultat attendu et evaluation ?** Reponse fondee avec references ; refus propre hors corpus ou sans acces. Evaluation sur `eval/questions.jsonl` (47 questions, 6 categories) : recall@k, references valides, taux de refus correct, violations d'acces, fuites, latence, tokens.
4. **Versions a conserver ?** Corpus (hash + tag DVC ou Git), `params.yaml` (chunking, embeddings, seuils), `eval/questions.jsonl`, index (reconstruit a l'identique), runs MLflow (parametres, metriques, hash du corpus).
5. **Tests anti-regression ?** `tests/` : donnees, chunking, provenance, acces, retrieval, injection, regression contre `eval/baseline.json` (marge 0,05).
6. **Indicateurs apres deploiement ?** `logs/requests.jsonl` (question hachee) resume par `python -m src.monitoring` : erreurs, latence moyenne et P95, taux de refus, tokens, score moyen, phrases d'injection retirees.
7. **Risques principaux ?** Reponse non fondee, document obsolete ou contradictoire, fuite d'un document reserve, injection documentaire, dependance aux sources, secrets exposes (voir `docs/risk_report.md`).

**Hors perimetre de l'assistant :** conseil en placement, donnees de clients individuels, toute operation (virement, ouverture de compte).
**Consequence d'une reponse fausse :** un employe peut communiquer une information erronee a un client (plafond, frais, delai). L'assistant est une aide a la consultation, pas une source d'autorite : la reponse doit toujours renvoyer au document.
