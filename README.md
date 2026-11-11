````# Pipeline RH multi-agents — Plateforme complète

Plateforme de recrutement automatisée : soumission de candidats, tri de CV,
scoring, préparation d'entretien, décision d'onboarding — avec API REST,
interface web RH, monitoring Prometheus, et gouvernance des données via
OpenMetadata (pipeline, lineage, glossaire, classification RGPD, data
quality, metrics).

**État du projet : noyau fonctionnel complet et testé.** 56/56 tests
passent (unitaires + intégration), Ruff propre, migration Alembic validée
sur SQLite. Voir "Ce qui reste à valider en environnement réel" en fin de
document pour ce qui dépend de Docker/MySQL/OpenMetadata réels.

## Architecture

```
app/
  agents/          4 agents LangGraph (state, graph, un fichier par agent)
  api/v1/           routes FastAPI (candidates, pipeline, decisions, health)
  audit/            pseudonymisation RGPD + logger structuré + persistance DB
  core/             config (Pydantic Settings), règles métier déterministes, erreurs
  db/               modèles SQLAlchemy (10 tables) + session
  llm/              3 providers (anthropic, openai, simulation) + fallback + service
  monitoring/       métriques Prometheus (cardinalité contrôlée)
  openmetadata/     intégration complète OpenMetadata (voir plus bas)
  repositories/     accès DB isolé (aucune logique métier)
  schemas/          schémas Pydantic (API)
  security/         auth par clé API + rate limiting
  services/         logique métier (candidate_service, pipeline_service)
  main.py           application FastAPI

dashboard/          interface Streamlit RH (parle uniquement à l'API HTTP)
tests/unit/          règles, agents, routing, fallback LLM, pseudonymisation, repositories
tests/integration/    API (auth, candidats, pipeline complet), health, métriques, OpenMetadata (mocké)
alembic/              migration initiale (10 tables)
docker/                Dockerfiles API + dashboard
prometheus/            config de scraping
scripts/               seed_demo_data.py
```

## Démarrage rapide (sans Docker, SQLite)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Crée le schéma (10 tables)
alembic upgrade head

# Données de démo (4 candidats, dont 2 retenus / 2 rejetés au tri)
python -m scripts.seed_demo_data

# Lance l'API
uvicorn app.main:app --reload
```

Dans un second terminal, le dashboard RH :
```bash
pip install -r requirements-dashboard.txt
streamlit run dashboard/app.py
```

Ouvrez http://localhost:8501 (dashboard) et http://localhost:8000/docs
(documentation OpenAPI interactive).

**Clé API par défaut (dev)** : `change-me-in-production` (à changer dans `.env`
avant tout usage réel — voir `API_KEY`).

## Démarrage avec Docker Compose (MySQL + API + dashboard + Prometheus)

```bash
cp .env.example .env
# éditez .env : API_KEY, AUDIT_PSEUDONYMIZATION_SALT, MYSQL_ROOT_PASSWORD au minimum

docker compose up --build
```

- API : http://localhost:8000
- Dashboard : http://localhost:8501
- Prometheus : http://localhost:9090
- MySQL : localhost:3306

**OpenMetadata n'est PAS inclus** dans ce `docker-compose.yml` (stack trop
volumineuse pour être embarquée). Déployez-le séparément via [sa propre
stack officielle](https://docs.open-metadata.org/quick-start/local-docker-deployment),
puis renseignez `OPENMETADATA_HOST_PORT` / `OPENMETADATA_JWT_TOKEN` dans
`.env`. Le compose ajoute déjà `host.docker.internal` pour que le conteneur
API puisse joindre une instance OpenMetadata tournant sur votre machine hôte.

Une fois exécuté avec `alembic upgrade head` (fait automatiquement au premier
démarrage du conteneur API si vous l'ajoutez à l'entrypoint — ou lancez-le
manuellement via `docker compose exec api alembic upgrade head`), migrez la
base avant le premier usage.

## Providers LLM

`LLM_PROVIDER` dans `.env` : `none` (défaut, simulation locale — aucune clé
requise), `anthropic`, ou `openai`. **Le LLM ne décide jamais** : les
décisions (retenu/rejeté, score, prêt/non-prêt) viennent exclusivement de
`app/core/rules.py`, déterministe et testé. Le LLM ne génère que du texte
explicatif (notes d'entretien, justifications en langage naturel). En cas
d'absence de clé ou d'échec de l'appel réel, repli automatique et
systématique sur la simulation locale (`app/llm/service.py` /
`app/llm/simulation_provider.py`).

**Prompt injection** : tout texte candidat (CV) est traité comme une donnée
non fiable. `app/llm/service.py::wrap_untrusted()` l'entoure de balises
explicites avec instruction au modèle de ne jamais les traiter comme des
consignes. Testé dans `tests/unit/test_llm_fallback.py`.

## API REST — endpoints principaux

Tous les endpoints (sauf `/health*` et `/metrics`) nécessitent le header
`X-API-Key`. Documentation interactive complète sur `/docs`.

| Méthode | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/candidates` | Créer un candidat |
| GET | `/api/v1/candidates` | Lister (pagination `offset`/`limit`) |
| GET | `/api/v1/candidates/{id}` | Détail d'un candidat |
| POST | `/api/v1/candidates/{id}/run-pipeline` | Lancer le pipeline pour ce candidat |
| GET | `/api/v1/pipeline-runs` | Lister les exécutions |
| GET | `/api/v1/pipeline-runs/{run_id}` | Détail d'une exécution |
| GET | `/api/v1/decisions` | Lister les décisions d'onboarding |
| GET | `/api/v1/decisions/{id}` | Détail d'une décision |
| GET | `/health`, `/health/database`, `/health/openmetadata` | Santé |
| GET | `/metrics` | Métriques Prometheus |

Chaque réponse porte un header `X-Correlation-ID` (généré si absent de la
requête, ou repris de `X-Correlation-ID` si fourni). Rate limiting simple
en mémoire (`RATE_LIMIT_PER_MINUTE`, 120/min par défaut — voir
`app/security/rate_limit.py` pour la limite en déploiement multi-instance :
remplacer par un backend partagé type Redis en production).

## Audit RGPD

`app/audit/pseudonymize.py` : hash SHA-256 salé (`AUDIT_PSEUDONYMIZATION_SALT`)
de `candidate_ref`, jamais l'inverse. Chaque décision est journalisée
(stdout JSON + table `audit_events`) avec : référence pseudonymisée, agent,
décision, justification, règles appliquées, **noms** de champs utilisés
(jamais leurs valeurs), correlation ID, run ID, date. Jamais journalisés :
nom complet, adresse, téléphone, email, contenu complet du CV, clés API,
tokens.

## Monitoring Prometheus

`app/monitoring/metrics.py`. Aucun label à forte cardinalité (pas de
`candidate_id` en label — vérifié par
`tests/integration/test_metrics.py::test_metrics_never_expose_high_cardinality_labels`).
Métriques : runs totaux/par statut, durée pipeline, exécutions/latence/erreurs
par agent, tokens et coût LLM par provider, profondeur de file.

## OpenMetadata — toutes les fonctionnalités couvertes

`app/openmetadata/` (réutilise et étend un module déjà validé contre une
instance OpenMetadata réelle en version 1.13.x) :

- `client.py` — connexion (JWT), désactivable via `OPENMETADATA_ENABLED=false`
- `pipeline_service.py` — Pipeline Service + Pipeline + 4 Tasks (un par agent) + statuts d'exécution
- `lineage.py` — assets CV/décision + lineage CV → Pipeline → Décision onboarding
- `glossary.py` — glossaire RH (Candidat, CV, Score de screening, Préparation entretien, Décision onboarding, Pipeline de recrutement)
- `classification.py` — tags Confidentiel/Public (RGPD) sur les colonnes
- `data_quality.py` — Test Suite + Test Cases
- `metrics.py` — entités Metric (taux de rétention, score moyen, taux d'onboarding)
- `test_results.py` — pousse de vrais résultats de test après chaque run (alimente le dashboard Observability sans attendre un profiling manuel)
- `setup.py` — `python -m app.openmetadata.setup` configure TOUT en une commande, idempotent (uniquement des `create_or_update`, **aucune opération destructive**)

Toute indisponibilité d'OpenMetadata est absorbée (warning loggé, jamais
d'exception qui casserait le pipeline RH) — voir
`tests/integration/test_openmetadata_mocked.py`.

Pour profiler de vraies tables (au lieu des assets "catalogue" créés par
`lineage.py`), connectez le **connecteur MySQL natif** d'OpenMetadata
(Settings > Services > Databases > Add New Service > MySQL) sur la même
base que celle utilisée par l'API.

## Tests

```bash
pytest                    # 56 tests (unit + integration)
ruff check app/ scripts/  # lint
mypy app/                 # typage (voir note ci-dessous)
```

Les tests ne dépendent d'aucune vraie clé Anthropic/OpenAI (provider
`simulation` forcé via `conftest.py`) ni d'une vraie instance OpenMetadata
(mocks dans `test_openmetadata_mocked.py`). Base SQLite temporaire, créée et
nettoyée automatiquement.

**Note MyPy** : `app/openmetadata/` a des faux positifs de typage résiduels
non filtrés par l'exclusion configurée (le SDK `openmetadata-ingestion`
utilise des types Pydantic RootModel qui acceptent des `str`/`int` bruts à
l'exécution — comportement confirmé par nos tests réels contre le SDK — mais
les stubs stricts ne le reflètent pas). Sans impact fonctionnel : ces
fichiers passent tous les tests.

## Ce qui reste à valider en environnement réel

Le sandbox de développement n'a pas d'accès Docker ni à une instance
OpenMetadata/MySQL de production. Ont été validés dans le sandbox :
Alembic sur SQLite, l'API complète via `TestClient`, le dashboard Streamlit
démarré et interrogé en HTTP, la syntaxe YAML du `docker-compose.yml`. **À
valider chez vous** :

- `docker compose up --build` de bout en bout (build des images, healthchecks, réseau)
- Migration Alembic contre un vrai MySQL (`DATABASE_URL=mysql+pymysql://...`)
- Connexion à une vraie instance OpenMetadata (`python -m app.openmetadata.setup`)
- Appels LLM réels (Anthropic/OpenAI) avec une vraie clé API

## Configuration (.env)

Voir `.env.example` pour la liste complète et commentée. Ne jamais committer
de `.env` réel — `.gitignore` l'exclut déjà.
````