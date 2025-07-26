**Brief: Diagnostic Measures for Job Architecture and Skills Taxonomy Health**

**Purpose**
To establish a set of diagnostic methodologies for evaluating the health of the NAB job architecture and associated skills taxonomy. This will enable the Future Skills and Workforce team to identify taxonomic drift, assess functional distinctiveness, and support strategic governance of job-skill relationships over time.

**Scope**

* Primary focus: *Structural* validity of the job architecture and skills taxonomy.
* Secondary focus: *Applied* consistency with the org structure (e.g., BU-level differentiation).
* Tertiary aim: Ensure findings are *actionable and interpretable* by non-technical HR stakeholders.

---

## 1. Silhouette Score Analysis

**What it measures**: Functional cohesion and separation between job profiles based on their skill vectors.

**Key diagnostics**:

* **Overall average silhouette score**: Tracks global taxonomic health.
* **Per-job-profile silhouette score**: Flags individual profiles that are poorly clustered (e.g., < 0.2 or < 0).
* **Per-BU silhouette average + distribution**: Highlights org units with poor differentiation.

**When to use**:

* After updates from Draup (taxonomy changes).
* Post job family redesign or new role intake.
* As part of a quarterly taxonomy health check.

**Interpretation guide**:

* > 0.7: Strong cohesion.
* 0.4 – 0.7: Mixed differentiation.
* < 0.3: Weak taxonomy integrity or overgeneralization.

**Translation for HR Partners**:

* "Roles within each area look distinct and well-structured."
* "These roles may need review—they're not clearly different from others."
* "Some jobs are misaligned or too generic—potential redesign needed."

---

## 2. Skill Similarity Measures

**A. Jaccard Similarity**

* Measures the overlap in skill sets between job profiles.
* Use to detect near-duplicate profiles or excessive standardization.

**B. Cosine Similarity (Skill Embeddings)**

* Computes semantic closeness using embedding vectors.
* Captures subtle redundancies or functional bleed across families.

**Usage**:

* Cluster heatmaps of job-to-job similarity.
* Role overlap matrix for redundancy detection.

**Alerts**:

* Job pairs with Jaccard > 0.85 or cosine similarity > 0.9.
* Role families with internal variance < 0.1 (may be overfitted).

**Translation for HR Partners**:

* "These roles are almost identical—do we need both?"
* "This job family is too homogenous—limited role clarity."

---

## 3. Graph-Based Structural Analysis

**Graph type**: Bipartite graph of jobs and skills.

**Tools**:

* Community detection (e.g., Louvain, Leiden).
* Centrality analysis (degree, betweenness).

**Insights**:

* Emergent functional clusters (unsupervised).
* Skills acting as hubs (assigned to many unrelated jobs).
* Roles with weak community affiliation.

**When to use**:

* To validate the taxonomy against natural structure.
* To uncover latent role families.

**Translation for HR Partners**:

* "These roles naturally group together—they may form a coherent job family."
* "Some skills are overused across the board—this may dilute their meaning."

---

## 4. Entropy and Diversity Metrics

**Metrics**:

* **Skill entropy per job**: Measures specificity vs generality.
* **Skill diversity per BU**: Tracks whether units are skill-rich or homogenous.

**Why it matters**:

* High entropy: role may be unfocused or misaligned.
* Low diversity in BU: risk of monoculture roles or inadequate differentiation.

**Translation for HR Partners**:

* "This role tries to do too many things—we may need to clarify its purpose."
* "This unit may be too skill-narrow—risk of inflexibility."

---

## 5. Drift and Change Detection

**Track over time**:

* Delta in silhouette score (overall + per-BU).
* New profiles with below-average cohesion.
* Roles with skill churn > threshold (e.g., >30% turnover in skill assignments).

**Purpose**:

* Detect unintended erosion of taxonomic integrity.
* Validate impact of role redesigns or Draup updates.

**Translation for HR Partners**:

* "This role has changed too much—time to revisit its structure."
* "We lost clarity in this BU after the last update—investigate further."

---

## 6. Governance and Reporting Framework

**Suggested KPIs**:

* % of roles with silhouette < 0.2.
* Median silhouette score by BU.
* Top 10 most duplicated roles (high similarity).
* Drift alert: silhouette delta > 0.1 post-update.
* Taxonomy entropy trend over time.

**Reporting Cadence**:

* Monthly light-touch dashboard (automated).
* Quarterly in-depth audit and governance review.

**Format**:

* Tableau/PowerBI dashboard.
* Slide pack for HR strategy & transformation teams.

**Insight Framing**:
Every output should map to one of the following HR-friendly calls to action:

* "Health is strong – no action required."
* "There are early signs of taxonomic drift – consider monitoring."
* "These roles/families need targeted review or redesign."
* "This unit's structure may not reflect skill reality – discussion warranted."

---

## Summary

These diagnostics allow NAB to evaluate the structural coherence, differentiation, and semantic integrity of its job and skill architecture. By applying silhouette scoring, similarity metrics, graph-based clustering, and entropy analysis, we can ensure that role design remains functionally meaningful, strategically aligned, and taxonomy drift is proactively managed. Crucially, results must be translated into insights that are accessible, relevant, and actionable for HR partners responsible for workforce planning and design.
