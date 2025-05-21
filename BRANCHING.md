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
  - **2.1-feature/similarity-engine/tf-idf**
  - **2.2-feature/similarity-engine/parallel-processing**
- **3-feature/gap-analysis**
- **4-feature/reporting-visualization**
- **5-feature/cli-testing**
  - **5.1-feature/cli-testing/logging**
  - **5.2-feature/cli-testing/error-handling**
- **6-feature/poc-integration**
  - **6.2-feature/poc-integration/memory-management**
  - **6.3-feature/poc-integration/performance-optimization**
  - **6.13-feature/poc-integration/error-handling**
- **7-feature/data-pipeline**
- **8-feature/cli-production-readiness**

- Subfeatures are merged into their parent feature branch when complete
- Feature branches are merged into `develop` when all subfeatures are complete and tested

---

## Release Process

1. Complete all subfeatures for a feature branch
2. Merge subfeatures into the parent feature branch
3. When all features for a release are complete, merge feature branches into `develop`
4. After final testing, merge `develop` into `main` for a new production release (e.g., v1)

---

## Example Branch Hierarchy (Numbered)

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
    │   └── 6.4-feature/poc-integration/error-handling
    ├── 7-feature/data-pipeline
    └── 8-feature/cli-production-readiness
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