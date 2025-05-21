# Skill Similarity Engine – Branching Structure

This document outlines the Git branching strategy for the Skill Similarity Engine project, reflecting the structure and workflow described in the project plan.

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

## Feature Branches

- **feature/feature-name**
  - Used for developing a specific feature or major enhancement
  - Branches from `develop`
  - Example: `feature/similarity-engine`, `feature/cli-testing`
  
- **feature/feature-name/subfeature-name**
  - Used for subcomponents or tasks within a feature
  - Branches from the parent feature branch
  - Example: `feature/poc-integration/error-handling`, `feature/cli-testing/logging`
  
- Subfeatures are merged into their parent feature branch when complete
- Feature branches are merged into `develop` when all subfeatures are complete and tested

---

## Release Process

1. Complete all subfeatures for a feature branch
2. Merge subfeatures into the parent feature branch
3. When all features for a release are complete, merge feature branches into `develop`
4. After final testing, merge `develop` into `main` for a new production release (e.g., v1)

---

## Example Branch Hierarchy

```
main
└── develop
    ├── feature/core-framework
    ├── feature/similarity-engine
    │   ├── feature/similarity-engine/tf-idf
    │   └── feature/similarity-engine/parallel-processing
    ├── feature/gap-analysis
    ├── feature/reporting-visualization
    ├── feature/cli-testing
    │   ├── feature/cli-testing/logging
    │   └── feature/cli-testing/error-handling
    ├── feature/poc-integration
    │   ├── feature/poc-integration/memory-management
    │   ├── feature/poc-integration/performance-optimization
    │   └── feature/poc-integration/error-handling
    └── feature/data-pipeline
```

---
****
## Branch Naming Conventions

- Use `feature/` for new features or enhancements
- Use `bugfix/` for bug fixes
- Use `hotfix/` for urgent production fixes (branch from `main`)
- Use `release/` for release branches if needed
- Use descriptive names for clarity (e.g., `feature/cli-production-readiness`)

---

## Best Practices

- Keep branches focused and short-lived
- Delete branches after merging
- Use pull requests for all merges to `develop` and `main`
- Reference issues in branch names or pull requests when possible
- Follow the commit and PR guidelines in the project plan 