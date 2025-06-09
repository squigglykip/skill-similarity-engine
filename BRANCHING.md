# Skill Similarity Engine – Branching Structure

This document outlines the Git branching strategy for the Skill Similarity Engine project, reflecting the current production-ready state and realistic future roadmap.

---

## Main Branches

- **main**
  - Production-ready code only
  - Contains fully functional CLI and core similarity engine
  - Protected: changes via pull request and review only

- **develop**
  - Integration branch for new features
  - Contains the latest completed features, ready for final testing and release

---

## Completed Feature Branches ✅

### Core System (Production Ready)
- **1-feature/core-framework** ✅ **COMPLETED**
- **2-feature/similarity-engine** ✅ **COMPLETED**
- **3-feature/gap-analysis** ✅ **COMPLETED**
- **4-feature/reporting-visualization** ✅ **COMPLETED**
- **5-feature/cli-testing** ✅ **COMPLETED**
- **6-feature/poc-integration** ✅ **COMPLETED**
- **7-feature/data-pipeline** ✅ **COMPLETED**
  - *7.1-feature/data-pipeline/data-export-optimisation* ✅
  - *7.2-feature/data-pipeline/config-management* ✅
  - *7.3-feature/data-pipeline/enhanced-configuration* ✅
  - *7.4-feature/data-pipeline/hris-integration* ✅

### Removed: Section 8 CLI Implementation
> **DELETED**: All `8-feature/cli-production-readiness/*` branches removed as redundant.
> The CLI is already fully functional in `main.py` with all required features.

---

## Active Development Branches 🚧

### Phase 7 Remaining Work
- **7.5-feature/data-pipeline/powerbi-integration** 📋 **PLANNED**
- **7.6-feature/data-pipeline/output-delivery** 📋 **PLANNED**
- **7.7-feature/data-pipeline/production-testing** 📋 **PLANNED**

---

## Future Features 🔮

### Phase 9: Enhanced Functionality
- **9-feature/future-features**
  - *9.1-feature/future-features/interactive-career-pathways*
  - *9.2-feature/future-features/skill-gap-analysis*
  - *9.3-feature/future-features/scenario-planning*
  - *9.4-feature/future-features/advanced-visualisation*
  - *9.5-feature/future-features/powerbi-enhanced*
  - *9.6-feature/future-features/business-tools*
  - *9.7-feature/future-features/local-webapp*

### Phase 10: Employee-Level Analytics (Aspirational)
- **10-feature/employee-insights** 🔮 **ASPIRATIONAL**
  - *10.1-feature/employee-insights/job-matching*
  - *10.2-feature/employee-insights/coaching-marketplace*
  - *10.3-feature/employee-insights/workforce-readiness*
  - *10.4-feature/employee-insights/skill-adjacency-recs*
  - *10.5-feature/employee-insights/talent-pooling*
  - *10.6-feature/employee-insights/org-intelligence*

> **Note**: Phase 10 branches are placeholders for future employee-level analytics and will only be activated if individual skill data becomes available.

---

## Removed Branches 🗑️

### Section 7.3.4-7.3.6: Over-Engineered Weighting Systems
> **REMOVED**: The following branches were removed as they were over-engineered for the current architectural focus on JobProfile similarity:
> - All `7.3.4-feature/*` (seniority implementation)
> - All `7.3.5-feature/*` (role track implementation)  
> - All `7.3.6-feature/*` (location implementation and geocoding)

### Section 8: Redundant CLI Implementation
> **REMOVED**: All `8-feature/cli-production-readiness/*` branches removed because:
> - CLI is already fully functional via `main.py`
> - Menu-driven interface works with all required features
> - Production-ready with proven performance (715 jobs → 510,510 comparisons)

---

## Current Branch Hierarchy

```
main ✅ (Production Ready)
└── develop
    ├── Completed Phases ✅
    │   ├── 1-feature/core-framework ✅
    │   ├── 2-feature/similarity-engine ✅
    │   ├── 3-feature/gap-analysis ✅
    │   ├── 4-feature/reporting-visualization ✅
    │   ├── 5-feature/cli-testing ✅
    │   ├── 6-feature/poc-integration ✅
    │   └── 7-feature/data-pipeline ✅ (core components)
    │
    ├── Active Development 🚧
    │   ├── 7.5-feature/data-pipeline/powerbi-integration 📋
    │   ├── 7.6-feature/data-pipeline/output-delivery 📋
    │   └── 7.7-feature/data-pipeline/production-testing 📋
    │
    ├── Future Features 🔮
    │   └── 9-feature/future-features
    │       ├── 9.1-feature/future-features/interactive-career-pathways
    │       ├── 9.2-feature/future-features/skill-gap-analysis
    │       ├── 9.3-feature/future-features/scenario-planning
    │       ├── 9.4-feature/future-features/advanced-visualisation
    │       ├── 9.5-feature/future-features/powerbi-enhanced
    │       ├── 9.6-feature/future-features/business-tools
    │       └── 9.7-feature/future-features/local-webapp
    │
    └── Aspirational Features 🔮
        └── 10-feature/employee-insights
            ├── 10.1-feature/employee-insights/job-matching
            ├── 10.2-feature/employee-insights/coaching-marketplace
            ├── 10.3-feature/employee-insights/workforce-readiness
            ├── 10.4-feature/employee-insights/skill-adjacency-recs
            ├── 10.5-feature/employee-insights/talent-pooling
            └── 10.6-feature/employee-insights/org-intelligence
```

---

## Production Status Summary

### ✅ **PRODUCTION READY**
- **Core Framework**: Data models, configuration, normalisation
- **Similarity Engine**: Asymmetric coverage calculator with proven performance
- **CLI Interface**: Fully functional menu-driven interface in `main.py`
- **Data Pipeline**: HRIS integration, field mapping, validation framework
- **Model Governance**: Quarterly versioning with audit trails
- **Memory Management**: Handles large datasets efficiently
- **Export System**: CSV/Parquet dual-format outputs for Power BI

### 📋 **REMAINING PLANNED WORK**
- Power BI integration documentation and templates
- Output delivery strategy refinements
- Production testing with real HRIS data

### 🔮 **FUTURE ENHANCEMENTS**
- Interactive career pathway exploration
- Advanced visualisation suite
- Scenario-based organisational planning

---

## Branch Naming Conventions

- ✅ `feature/` - Completed features (merged to main)
- 🚧 `feature/` - Active development features  
- 📋 `feature/` - Planned features (not yet started)
- 🔮 `feature/` - Future/aspirational features
- `bugfix/` - Bug fixes
- `hotfix/` - Urgent production fixes (branch from `main`)
- `release/` - Release preparation branches

---

## Best Practices

- Focus on value delivery over comprehensive planning
- Keep branches aligned with actual business priorities
- Delete redundant branches that don't match current architecture
- Use production testing to validate features before planning extensions
- Maintain clean separation between core engine and future enhancements