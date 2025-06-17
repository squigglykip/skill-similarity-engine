# Data Architecture Restructure Plan
## Holistic Elimination of Job Data Duplication

**Created**: 2025-01-18  
**Status**: Planning Phase  
**Goal**: Eliminate data duplication and create a cleaner separation between similarity calculation and business context data

---

## 🎯 **Architecture Vision**

### **Current State (Problematic)**
- **Similarity Calculation**: Uses 3 files (jobs + skills + job-skill mapping)
- **Business Context DB**: Uses 5 files with overlapping job data
- **Data Duplication**: Same job information exists in multiple locations
- **Complexity**: Unnecessary metadata loaded for pure similarity calculations

### **Target State (Clean)**
- **Similarity Calculation**: Uses 2 files only
  - `skill-similarity-engine/data/input_data/job_skill_mapping.csv`
  - `skill-similarity-engine/data/skills_library/lightcast_skills_comprehensive.csv`
- **Business Context DB**: Uses comprehensive data sources
  - Latest precompute matrices (`.parquet` files)
  - Enhanced job architecture with 14-column schema
  - Comprehensive skills library
  - Workforce context data
- **No Duplication**: Single source of truth for each data element

---

## 📋 **Implementation Plan**

### **Phase 1: Core Similarity Calculation Simplification**

#### 1.1 Update JobArchitectureLoader to Support Job-Only Mode
- [ ] **Modify `JobArchitectureLoader.load_from_csv()`** in `src/skill_similarity_engine/data/loaders.py`
  - [ ] Make `jobs_file` parameter optional (None when not provided)
  - [ ] When `jobs_file=None`, auto-generate minimal Job objects from job-skill mapping
  - [ ] Extract unique JobProfileIDs from job_skill_mapping.csv
  - [ ] Create Job objects with minimal metadata: `job_id=JobProfileID, title=JobProfileID, department="Auto-generated"`
  - [ ] Load skills via existing `_load_job_skills()` method

#### 1.2 Update Core Similarity Modules
- [ ] **Verify `AsymmetricCoverageCalculator`** works with minimal Job objects (should already work - only uses `job.skills.keys()`)
- [ ] **Test `SimilarityMatrixPrecomputer`** with simplified job loading
- [ ] **Update error handling** for missing job metadata in downstream modules

#### 1.3 Update main.py Data Loading
- [ ] **Remove default jobs file path** from `main.py`
- [ ] **Update loading logic** to only prompt for:
  - `skills_library/lightcast_skills_comprehensive.csv`
  - `input_data/job_skill_mapping.csv`
- [ ] **Update display messages** to reflect auto-generated jobs

### **Phase 2: Business Context Database Architecture Update**

#### 2.1 Enhance Job Architecture Schema Support
- [ ] **Update `SchemaBuilder._create_jobs_table()`** in `src/skill_similarity_engine/business_context/schema_builder.py`
  - [ ] Add new columns from `job_arch_schema.json`: 
    - `ProfileTitleSuffix`, `ManagementLevel`, `JobSubFunctionID`, `JobSubFunction`
    - `JobCategoryID`, `JobCategory`, `Customer Facing`, `is Banker`
    - `Executive Leadership Group`, `Accountability Scope`
  - [ ] Maintain backward compatibility with existing 6-column schema

#### 2.2 Update Data Loader for Enhanced Job Architecture
- [ ] **Modify `DataLoader._load_job_architecture()`** in `src/skill_similarity_engine/business_context/data_loader.py`
  - [ ] Support loading from `job_architecture/dummy_job_architecture.csv` with 14-column schema
  - [ ] Map new columns with appropriate defaults for missing values
  - [ ] Handle data quality issues (nulls, long descriptions, non-ASCII characters)

#### 2.3 Update Similarity Matrix Integration
- [ ] **Verify `DataLoader._load_similarity_matrix()`** can handle:
  - Latest precompute run detection (find most recent `precompute_*` folder)
  - Both `job_similarity_matrix.parquet` and `career_pathways.parquet` loading
  - Proper foreign key relationships with enhanced job table

### **Phase 3: Data Source Consolidation**

#### 3.1 Remove Dependency on input_data Jobs File
- [ ] **Audit all references** to `input_data/job_data.csv` in codebase
  - [ ] Check test files, configuration files, documentation
  - [ ] Update any hardcoded paths or references
- [ ] **Update field mapping configuration** if it references old job schema
- [ ] **Remove or deprecate** old job data file after verification

#### 3.2 Update Documentation and Configuration
- [ ] **Update `main.py` help text** and prompts to reflect new architecture
- [ ] **Update `PROJECT_PLAN.md`** with new data flow
- [ ] **Regenerate `sqlite_schema_design.md`** with enhanced job table schema
- [ ] **Update test data** and sample files to match new architecture

### **Phase 4: Data Pipeline Validation**

#### 4.1 End-to-End Testing
- [ ] **Test CLI Option 1**: Similarity precomputation with new data sources
  - [ ] Load skills from `skills_library/lightcast_skills_comprehensive.csv`
  - [ ] Auto-generate jobs from `input_data/job_skill_mapping.csv`
  - [ ] Generate similarity matrices successfully
  - [ ] Verify output formats (CSV/Parquet)

#### 4.2 Business Context Database Testing  
- [ ] **Test CLI Option 2**: Business context database generation
  - [ ] Load enhanced job architecture from `job_architecture/dummy_job_architecture.csv`
  - [ ] Load latest similarity matrices from `models/2025-Q2/precompute_*/`
  - [ ] Load skills from `skills_library/lightcast_skills_comprehensive.csv`
  - [ ] Load workforce context from `workforce_context/dummy_workforce_context.csv`
  - [ ] Generate complete SQLite database
  - [ ] Verify all foreign key relationships
  - [ ] Test webapp functionality with new database

#### 4.3 Performance Validation
- [ ] **Benchmark new data loading approach**
  - [ ] Compare performance vs. old 3-file approach
  - [ ] Verify memory usage within acceptable limits
  - [ ] Test with large datasets (scaling considerations)

### **Phase 5: Clean-up and Optimisation**

#### 5.1 Code Cleanup
- [ ] **Remove unused job metadata handling** in similarity calculations
- [ ] **Simplify Job object creation** paths
- [ ] **Update type hints** and documentation for optional parameters
- [ ] **Remove dead code** related to old job loading approach

#### 5.2 Configuration Updates
- [ ] **Update default paths** in configuration files
- [ ] **Update field mapping** for new data sources
- [ ] **Verify environment setup** scripts and documentation

#### 5.3 Final Validation
- [ ] **Run comprehensive test suite**
- [ ] **Verify webapp functionality** with new data architecture
- [ ] **Performance regression testing**
- [ ] **Documentation accuracy check**

---

## 🔍 **Key Dependencies to Review**

### **Main Module Dependencies** (from `main.py`):
- **`SkillTaxonomyLoader`** - ✅ Already uses skills_library
- **`JobArchitectureLoader`** - 🔄 Needs modification for jobs_file=None
- **`create_precomputer`** - ✅ Should work with minimal jobs
- **`BusinessContextOrchestrator`** - 🔄 May need updates for enhanced schema

### **Business Context Dependencies**:
- **SQLite schema builder** - 🔄 Needs new columns
- **Data loader pipeline** - 🔄 Needs enhanced job architecture support
- **Foreign key validation** - 🔄 Needs updates for new schema

### **Test Dependencies**:
- **Unit tests for Job models** - 🔄 May need updates
- **Integration tests** - 🔄 Need updates for new data flow
- **Sample data files** - 🔄 Need to match new architecture

---

## 📊 **Data Consolidation Evidence**

Based on comprehensive testing with `scripts/test_data_consolidation.py`:

### **Job Data Compatibility**
- ✅ **100% JobProfileID coverage** between old and new job data
- ✅ **No duplicates** in either dataset
- ✅ **Perfect mapping compatibility** with job-skill data

### **Skills Data Enhancement**
- ✅ **99.7% skill coverage** (2,061/2,068 skills matched)
- 📈 **18x more comprehensive** (38,395 vs 2,068 skills)
- ⚡ **Manageable performance impact** (0.109s load time, 23MB memory)

### **Job-Skill Mapping Quality**
- ✅ **100% job coverage** in mapping file
- ✅ **98.5% skill coverage** with new skills library
- ✅ **No duplicate mappings**
- ✅ **No null values**

### **Performance Implications**
- **Skills Loading**: 15x slower but still sub-second (0.109s)
- **Memory Usage**: 35x more (23MB) but acceptable for modern systems
- **Overall Assessment**: **"CONSOLIDATION SAFE TO PROCEED"**

---

## 🎯 **Success Criteria**

### **Functional Requirements**
- [ ] Similarity calculations produce identical results with new architecture
- [ ] Business context database contains all required data and relationships
- [ ] Webapp functionality remains unchanged from user perspective
- [ ] All existing test suites pass

### **Performance Requirements**
- [ ] Similarity calculation performance within 20% of current baseline
- [ ] Database generation completes successfully with enhanced schema
- [ ] Memory usage remains within acceptable limits (< 100MB peak)
- [ ] No regression in webapp query performance

### **Data Quality Requirements**
- [ ] No data loss during migration
- [ ] All foreign key relationships validated
- [ ] Data completeness metrics maintained or improved
- [ ] Schema integrity verified

---

## 🚀 **Benefits of New Architecture**

### **Reduced Complexity**
- **2 files** instead of 3 for similarity calculations
- **Single source of truth** for each data element
- **Cleaner separation** of concerns

### **Enhanced Business Context**
- **14-column job architecture** with rich organizational metadata
- **38K+ comprehensive skills** library
- **Latest precompute results** automatically integrated

### **Improved Maintainability**
- **No data duplication** to keep in sync
- **Logical data flow** from calculation to context
- **Simplified testing** and validation

### **Better Performance**
- **Minimal data loading** for similarity calculations
- **Optimised SQLite schema** for business queries
- **Reduced memory footprint** for core operations

---

## 📝 **Implementation Notes**

1. **Backward Compatibility**: Maintain ability to load from existing data sources during transition
2. **Data Validation**: Implement comprehensive validation at each phase
3. **Performance Monitoring**: Track metrics throughout implementation
4. **Documentation Updates**: Keep all documentation current with changes
5. **Testing Strategy**: Validate both individual components and end-to-end workflows

This restructure will create a more logical, maintainable, and efficient data architecture that eliminates duplication while enhancing the system's capabilities for both similarity calculation and business context analysis. 