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

## Supervision humaine
- Aucune operation metier n'est exposee : l'assistant ne fait que repondre.
- Toute promotion (`scripts/promote.py --approve`) exige que les gates passent **et** une approbation explicite.

## Exceptions pip-audit (a justifier avant remise)
- `PYSEC-2026-1845` (pytest 8.4.2) : dependance de test uniquement, absente d'un deploiement. Correctif en 9.0.3 ; non applique si la borne du cours impose pytest < 9.
- `PYSEC-2026-311`, `3813`, `3814`, `3815` (chromadb) : **lors de mon test, aucune version corrigee n'etait indiquee**. Je n'ai pas analyse le contenu des avis. Lisez-les sur osv.dev : si ils concernent un mode non utilise ici (serveur HTTP au lieu du client local `PersistentClient`), documentez-le ici ; sinon, changez de version ou de base vectorielle. **Ne laissez pas ces exceptions sans analyse dans le rapport final.**
