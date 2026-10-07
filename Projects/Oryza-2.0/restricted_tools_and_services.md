Objective: Refactor and stabilize existing codebase under constrained resource conditions without disrupting current logic flow or future scalability.

Instructions:
1. **Preserve all original code**—leave it intact for future restoration or reintegration.
2. **Identify inaccessible services, APIs, or dependencies**. For each:
   - Comment out usage clearly.
   - Add descriptive notes explaining the service, why it's disabled, and the workaround used.
     Example:
     ```python
     # 🚫 NewsAPI integration disabled due to network limitations.
     # 🛠️ Replaced with local JSON news mock in `mock_data/news.json`.
     ```
3. **Database Layer**:
   - Replace external DBs like PostgreSQL/MongoDB with **SQLite** using local `.db` file.
   - Refactor ORM or DB access logic minimally to support SQLite.
   - Ensure schema remains adaptable for future migration.

4. **Data Sources**:
   - Swap live feeds (e.g., BSE/NSE, financial APIs) with static files.
   - Use consistent data structures to mirror real-time APIs.
   - Include timestamped placeholder datasets to simulate updates.

5. **ML & Analysis Modules**:
   - Stub out large model dependencies (e.g. FinBERT, transformers).
   - Use simple keyword-based sentiment checks or dummy scores.
   - Add `TODO` comments for future enhancement or model restoration.

6. **Minimal Alternative First Approach**:
   - Attempt lightweight libraries or simplified logic before falling back to mocks/stubs.
   - Document decisions with rationale—include commit notes or comments referencing limitations.

7. **Modularity and Reversibility**:
   - Encapsulate refactored logic inside alternate modules/functions.
   - Avoid deep rewrites of core logic.
   - Keep old references commented alongside replacements for traceability.

8. **Final Check**:
   - Ensure entire codebase runs end-to-end in current environment.
   - Include README update listing changed components and fallback mechanisms.


# always use venv 

