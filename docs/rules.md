# Kisan Mitra — Engineering and AI Rules

## 1. Grounding Rules

1. Do not present unsupported agricultural claims as facts.
2. Prefer retrieved knowledge over model memory.
3. If the retrieved context does not contain enough evidence, say so.
4. Do not invent doses, dates, crop stages, disease treatments, or weather conditions.
5. Clearly distinguish retrieved facts from general explanatory text.

## 2. Agricultural Safety Rules

1. Agricultural chemical recommendations must be treated as safety-sensitive.
2. Avoid encouraging unsafe or unverified pesticide/fertilizer use.
3. Preserve the application's local KVK/agricultural-expert referral guidance.
4. Do not claim that AI advice replaces an agricultural expert.
5. Weather-sensitive actions should consider the available weather context.

## 3. RAG Rules

1. Retrieve relevant context before generation.
2. Use crop metadata filtering when crop context is known.
3. Preserve source metadata through the retrieval pipeline.
4. Use confidence/quality signals to determine whether an answer is sufficiently grounded.
5. Keep retrieval logic separate from UI logic.

## 4. Language Rules

1. Respect the user's requested language.
2. Support English, Hindi, Punjabi, and Hinglish where supported by the application.
3. Do not translate technical agricultural quantities incorrectly.
4. Preserve important scientific names, units, and product names when translation could reduce clarity.

## 5. Weather Rules

1. Treat Open-Meteo data as contextual information, not as a replacement for agronomic expertise.
2. Do not claim weather conditions that were not actually retrieved.
3. If weather data is unavailable, do not fabricate it.
4. Weather gates should only influence recommendations where weather is materially relevant.

## 6. Software Engineering Rules

1. Keep secrets out of Git.
2. Keep `vector_db/` out of Git when it is generated at runtime.
3. Validate Python syntax before committing.
4. Run `git diff --check` before pushing.
5. Prefer small, descriptive commits.
6. Do not force-push shared branches unless explicitly required and understood.
7. Keep deployment configuration reproducible.

## 7. Documentation Rules

Documentation must describe the current deployed architecture, not abandoned prototypes.

When architecture changes, update:

- README
- PRD
- architecture documentation
- task/status documentation

## 8. Product Integrity

Do not claim:

- guaranteed crop yield improvement
- guaranteed disease diagnosis
- guaranteed agronomic correctness
- replacement of agricultural experts
- production readiness for capabilities that are only prototypes

Use accurate terms such as:

- AI-assisted advisory
- decision-support prototype
- knowledge-grounded response
- weather-aware context
