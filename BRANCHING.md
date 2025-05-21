# Skill Similarity Engine – Branching Structure

This document outlines the Git branching strategy for the Skill Similarity Engine project, reflecting the structure and workflow described in the project plan. **Numbering is used to match phases/features/subfeatures to the project plan for easy cross-reference.**

---

## Main Branches

- **main**
  - Production-ready code only
  - Only updated from `develop` after all features for a release are complete
  - Protected: changes via pull request and review only

- **develop**
  - Integration branch for all feature branches
  - Contains the latest completed features, ready for final testing and release
  - Merges from feature branches (after all subfeatures are complete)

---

## Feature Branches (Numbered by Project Phase)

- **1-feature/core-framework**
- **2-feature/similarity-engine**
  - *2.1-feature/similarity-engine/tf-idf*
  - *2.2-feature/similarity-engine/parallel-processing*
- **3-feature/gap-analysis**
- **4-feature/reporting-visualization**
- **5-feature/cli-testing**
  - *5.1-feature/cli-testing/logging*
  - *5.2-feature/cli-testing/error-handling*
- **6-feature/poc-integration**
  - *6.2-feature/poc-integration/memory-management*
  - *6.3-feature/poc-integration/performance-optimization*
  - 6.4-feature/poc-integration/error-handling
  - 6.5-feature/poc-integration/core-data-loading
  - 6.6-feature/poc-integration/tfidf-skill-processing
  - 6.7-feature/poc-integration/precomputation-strategy
    - 6.7.1-feature/poc-integration/input-vectorisation
    - 6.7.2-feature/poc-integration/similarity-matrix-precomp
  - 6.8-feature/poc-integration/job-context-metadata
  - 6.9-feature/poc-integration/similarity-enhancements
  - 6.10-feature/poc-integration/advanced-optimisation
  - 6.11-feature/poc-integration/query-interface
  - 6.12-feature/poc-integration/config-transparency
  - 6.13-feature/poc-integration/cli-precomp-query
  - 6.14-feature/poc-integration/focused-exports
  - 6.15-feature/poc-integration/examples-testing
  - 6.16-feature/poc-integration/memory-aware-processing
- **7-feature/data-pipeline**
  - 7.1-feature/data-pipeline/data-export-optimisation
  - 7.2-feature/data-pipeline/config-management
  - 7.3-feature/data-pipeline/skill-affinity-analyser
    - 7.3.6-feature/data-pipeline/location-implementation
      - 7.3.6.4-feature/data-pipeline/geocoding-distance
      - 7.3.6.5-feature/data-pipeline/commute-similarity
      - 7.3.6.6-feature/data-pipeline/address-validation
      - 7.3.6.7-feature/data-pipeline/edge-cases
      - 7.3.6.8-feature/data-pipeline/intl-banking-context
  - 7.4-feature/data-pipeline/hris-integration
  - 7.5-feature/data-pipeline/powerbi-integration
  - 7.6-feature/data-pipeline/output-delivery
  - 7.7-feature/data-pipeline/realworld-testing
- **8-feature/cli-production-readiness**
  - 8.1-feature/cli-production-readiness/cli-framework
  - 8.2-feature/cli-production-readiness/local-prod-prep
  - 8.3-feature/cli-production-readiness/data-workflow
  - 8.4-feature/cli-production-readiness/adhoc-toolkit
  - 8.5-feature/cli-production-readiness/ux-docs
  - 8.6-feature/cli-production-readiness/testing-qa
  - 8.7-feature/cli-production-readiness/prod-transition
  - 8.8-feature/cli-production-readiness/config-driven-model

- **9-feature/future-features**
  - 9.1-feature/future-features/career-pathways
  - 9.2-feature/future-features/skill-gap-devplans
  - 9.3-feature/future-features/scenario-planning
  - 9.4-feature/future-features/visualisation-suite
  - 9.5-feature/future-features/powerbi-enhanced
  - 9.6-feature/future-features/query-api
  - 9.7-feature/future-features/user-tools
  - 9.8-feature/future-features/local-webapp  # Python-based local web application for improved UX, no server required
  - 9.9-feature/future-features/skill-adjacency-explorer  # Optional/aspirational: skill-level upskilling explorer
  - 9.10-feature/future-features/capability-impact-modeller  # Optional/aspirational: capability what-if analysis

#
# Section 10: Potential employee-level features (not currently planned)
#
  - 10.1-feature/employee-insights/job-matching
  - 10.2-feature/employee-insights/coaching-marketplace
  - 10.3-feature/employee-insights/workforce-readiness
  - 10.4-feature/employee-insights/skill-adjacency-recs
  - 10.5-feature/employee-insights/talent-pooling
  - 10.6-feature/employee-insights/org-intelligence
#
# These branches are placeholders for future employee-level analytics and will only be used if individual skill data becomes available.

#
# These branches are placeholders for future aspirational features and will be fleshed out as the project progresses.

- Subfeatures are merged into their parent feature branch when complete
- Feature branches are merged into `develop` when all subfeatures are complete and tested

---

## Release Process

1. Complete all subfeatures for a feature branch
2. Merge subfeatures into the parent feature branch
3. When all features for a release are complete, merge feature branches into `develop`
4. After final testing, merge `develop` into `main` for a new production release (e.g., v1)

---

## Branch Hierarchy (Numbered)

```
main
└── develop
    ├── 1-feature/core-framework
    ├── 2-feature/similarity-engine
    │   ├── 2.1-feature/similarity-engine/tf-idf
    │   └── 2.2-feature/similarity-engine/parallel-processing
    ├── 3-feature/gap-analysis
    ├── 4-feature/reporting-visualization
    ├── 5-feature/cli-testing
    │   ├── 5.1-feature/cli-testing/logging
    │   └── 5.2-feature/cli-testing/error-handling
    ├── 6-feature/poc-integration
    │   ├── 6.2-feature/poc-integration/memory-management
    │   ├── 6.3-feature/poc-integration/performance-optimization
    │   ├── 6.4-feature/poc-integration/error-handling
    │   ├── 6.5-feature/poc-integration/core-data-loading
    │   ├── 6.6-feature/poc-integration/tfidf-skill-processing
    │   ├── 6.7-feature/poc-integration/precomputation-strategy
    │   │   ├── 6.7.1-feature/poc-integration/input-vectorisation
    │   │   └── 6.7.2-feature/poc-integration/similarity-matrix-precomp
    │   ├── 6.8-feature/poc-integration/job-context-metadata
    │   ├── 6.9-feature/poc-integration/similarity-enhancements
    │   ├── 6.10-feature/poc-integration/advanced-optimisation
    │   ├── 6.11-feature/poc-integration/query-interface
    │   ├── 6.12-feature/poc-integration/config-transparency
    │   ├── 6.13-feature/poc-integration/cli-precomp-query
    │   ├── 6.14-feature/poc-integration/focused-exports
    │   ├── 6.15-feature/poc-integration/examples-testing
    │   └── 6.16-feature/poc-integration/memory-aware-processing
    ├── 7-feature/data-pipeline
    │   ├── 7.1-feature/data-pipeline/data-export-optimisation
    │   ├── 7.2-feature/data-pipeline/config-management
    │   ├── 7.3-feature/data-pipeline/skill-affinity-analyser
    │   │   └── 7.3.6-feature/data-pipeline/location-implementation
    │   │       ├── 7.3.6.4-feature/data-pipeline/geocoding-distance
    │   │       ├── 7.3.6.5-feature/data-pipeline/commute-similarity
    │   │       ├── 7.3.6.6-feature/data-pipeline/address-validation
    │   │       ├── 7.3.6.7-feature/data-pipeline/edge-cases
    │   │       └── 7.3.6.8-feature/data-pipeline/intl-banking-context
    │   ├── 7.4-feature/data-pipeline/hris-integration
    │   ├── 7.5-feature/data-pipeline/powerbi-integration
    │   ├── 7.6-feature/data-pipeline/output-delivery
    │   └── 7.7-feature/data-pipeline/realworld-testing
    ├── 8-feature/cli-production-readiness
    │   ├── 8.1-feature/cli-production-readiness/cli-framework
    │   ├── 8.2-feature/cli-production-readiness/local-prod-prep
    │   ├── 8.3-feature/cli-production-readiness/data-workflow
    │   ├── 8.4-feature/cli-production-readiness/adhoc-toolkit
    │   ├── 8.5-feature/cli-production-readiness/ux-docs
    │   ├── 8.6-feature/cli-production-readiness/testing-qa
    │   ├── 8.7-feature/cli-production-readiness/prod-transition
    │   └── 8.8-feature/cli-production-readiness/config-driven-model
    ├── 9-feature/future-features
    │   ├── 9.1-feature/future-features/career-pathways
    │   ├── 9.2-feature/future-features/skill-gap-devplans
    │   ├── 9.3-feature/future-features/scenario-planning
    │   ├── 9.4-feature/future-features/visualisation-suite
    │   ├── 9.5-feature/future-features/powerbi-enhanced
    │   ├── 9.6-feature/future-features/query-api
    │   ├── 9.7-feature/future-features/user-tools
    │   ├── 9.8-feature/future-features/local-webapp
    │   ├── 9.9-feature/future-features/skill-adjacency-explorer
    │   └── 9.10-feature/future-features/capability-impact-modeller
    └── 10-feature/employee-insights
        ├── 10.1-feature/employee-insights/job-matching
        ├── 10.2-feature/employee-insights/coaching-marketplace
        ├── 10.3-feature/employee-insights/workforce-readiness
        ├── 10.4-feature/employee-insights/skill-adjacency-recs
        ├── 10.5-feature/employee-insights/talent-pooling
        └── 10.6-feature/employee-insights/org-intelligence
```

---

## Branch Naming Conventions

- Use `feature/` for new features or enhancements, prefixed with the phase number
- Use `bugfix/` for bug fixes
- Use `hotfix/` for urgent production fixes (branch from `main`)
- Use `release/` for release branches if needed
- Use descriptive names for clarity (e.g., `8-feature/cli-production-readiness`)

---

## Best Practices

- Keep branches focused and short-lived
- Delete branches after merging
- Use pull requests for all merges to `develop` and `main`
- Reference issues in branch names or pull requests when possible
- Follow the commit and PR guidelines in the project plan