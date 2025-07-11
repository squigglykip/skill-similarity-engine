# Config Directory Reorganization Proposal
## Aligning Configuration with Src Module Architecture

### 🎯 **Objective**
Reorganize the `/config` directory to clearly align with the `/src/skill_similarity_engine` module structure, following PTH's configuration-driven design philosophy while maintaining all existing functionality.

### 📊 **Current State Analysis**

**Current Config Files (11 files, 74KB total)**:
- `architectural_config.yaml` (39KB, 1398 lines) - **MONOLITHIC** - contains ALL module configs
- `webapp_config.yaml` (9.2KB) - webapp-specific (keep separate)
- `operational_config.yaml` (12KB) - runtime settings
- `data_field_mappings.yaml` (11KB) - data schema mappings
- `data_sources.yaml` (6.1KB) - data source configurations
- `data_validation_schema.yaml` (1.9KB) - validation rules
- `similarity_enhancement_factors.yaml` (6.4KB) - similarity enhancements
- `field_mapping.yaml` (6.3KB) - legacy field mappings
- `config.yaml` (3.4KB) - legacy main config
- Plus legacy and documentation files

**Problems with Current Structure**:
1. **Monolithic `architectural_config.yaml`** - 1398 lines covering ALL modules
2. **Module concerns scattered** across multiple files
3. **No clear src module alignment** - hard to find configs for specific modules
4. **Duplication** between files (e.g., field mappings in multiple places)
5. **Mixed abstraction levels** - core infrastructure mixed with domain logic

### 🏗️ **Proposed Module-Aligned Structure**

```
config/
├── core/                           # Core infrastructure (cross-cutting)
│   ├── directories.yaml           # Path configurations & directory structure
│   ├── processing.yaml             # Memory, performance, parallel processing
│   ├── datetime.yaml               # Date formats & validation rules
│   └── environment.yaml            # Environment settings & feature flags
│
├── modules/                        # Module-specific configurations
│   ├── similarity/
│   │   ├── algorithms.yaml         # Similarity algorithms & parameters
│   │   ├── precompute.yaml         # Precomputation settings
│   │   └── enhancement_factors.yaml # Seniority, role, location weights
│   │
│   ├── models/
│   │   ├── versioning.yaml         # Quarterly versioning & model management
│   │   ├── movement_analysis.yaml  # Movement detection & tracking
│   │   ├── jobs.yaml               # Job architecture & mapping
│   │   ├── skills.yaml             # Skills taxonomy & categorization
│   │   └── employees.yaml          # Employee data & proficiency
│   │
│   ├── utils/
│   │   ├── memory.yaml             # Memory management & monitoring
│   │   ├── chunking.yaml           # Adaptive chunking strategies
│   │   ├── progress.yaml           # Progress tracking & reporting
│   │   └── parallel.yaml           # Parallel processing configuration
│   │
│   ├── analysis/
│   │   ├── gap_analysis.yaml       # Skills gap analysis parameters
│   │   ├── team_analysis.yaml      # Team coverage & reskilling
│   │   └── workforce_analysis.yaml # Workforce planning & reporting
│   │
│   ├── api/
│   │   ├── lightcast.yaml          # Lightcast API configuration
│   │   └── endpoints.yaml          # API endpoint settings
│   │
│   ├── business_context/
│   │   ├── database.yaml           # SQLite database configuration
│   │   ├── schema_builder.yaml     # Schema generation settings
│   │   └── data_loader.yaml        # Data loading & validation
│   │
│   ├── cli/
│   │   └── commands.yaml           # CLI command configuration
│   │
│   ├── logging/
│   │   ├── formatters.yaml         # Log formatting configuration
│   │   ├── handlers.yaml           # Log handler settings
│   │   └── structured.yaml         # Structured logging configuration
│   │
│   ├── error_handling/
│   │   ├── recovery.yaml           # Error recovery strategies
│   │   ├── checkpoints.yaml        # Checkpoint configuration
│   │   └── registry.yaml           # Error tracking & reporting
│   │
│   └── data_validation/
│       ├── schemas.yaml            # Validation schema definitions
│       └── rules.yaml              # Validation rule configuration
│
├── data/                           # Data-specific configurations
│   ├── sources.yaml                # Data source definitions
│   ├── field_mappings.yaml         # Schema field mappings
│   ├── normalization.yaml          # Data normalization settings
│   └── export.yaml                 # Data export configurations
│
├── integration/                    # Integration & legacy configs
│   ├── webapp_config.yaml          # Keep existing webapp config
│   └── legacy/                     # Deprecated configs (for migration)
│       ├── config.yaml             # Legacy main config
│       ├── operational_config.yaml # Legacy operational settings
│       └── field_mapping.yaml      # Legacy field mappings
│
└── README.md                       # Updated configuration documentation
```

### 🔄 **Migration Strategy**

#### **Phase 1: Extract Module Configs from Monolithic File**
1. **Parse `architectural_config.yaml`** into module-specific sections
2. **Create module directories** under `config/modules/`
3. **Extract configurations** for each src module:
   - `utils:` → `modules/utils/`
   - `similarity_module:` → `modules/similarity/`
   - `models:` → `modules/models/`
   - `gap_analysis:` → `modules/analysis/gap_analysis.yaml`
   - `api:` → `modules/api/`
   - `business_context:` → `modules/business_context/`
   - `logging:` → `modules/logging/`
   - `error_handling:` → `modules/error_handling/`
   - `data_validation:` → `modules/data_validation/`

#### **Phase 2: Update Configuration Manager**
1. **Extend `ArchitecturalConfigManager`** to support module-based loading
2. **Add module discovery** capabilities
3. **Create module-specific config loaders**
4. **Maintain backward compatibility** with existing monolithic structure

#### **Phase 3: Consolidate Data Configurations**
1. **Merge data-related configs** into `config/data/`
2. **Eliminate duplication** between field mapping files
3. **Standardize data source definitions**

#### **Phase 4: Clean Up Legacy**
1. **Move deprecated configs** to `config/integration/legacy/`
2. **Update documentation** and README files
3. **Create migration guide** for configuration users

### 🔧 **Implementation Benefits**

#### **Developer Experience**
- **Module-specific configs** - easy to find relevant settings
- **Logical grouping** - related configurations co-located
- **Reduced file size** - smaller, focused configuration files
- **Clear ownership** - each module owns its configuration

#### **Maintenance Benefits**
- **Isolated changes** - modify one module's config without affecting others
- **Easier testing** - test module configs independently
- **Better versioning** - track changes per module
- **Reduced merge conflicts** - smaller files, fewer concurrent edits

#### **Architectural Benefits**
- **Separation of concerns** - infrastructure vs domain configs
- **Scalability** - easy to add new modules
- **Configuration discoverability** - clear mapping to src structure
- **PTH compliance** - follows enterprise configuration patterns

### 📝 **Configuration Manager Updates**

#### **Enhanced ArchitecturalConfigManager**
```python
class ArchitecturalConfigManager:
    def __init__(self, config_root="config"):
        self.config_root = config_root
        self.core_configs = self._load_core_configs()
        self.module_configs = self._load_module_configs()
        self.data_configs = self._load_data_configs()
    
    def get_module_config(self, module_name: str) -> Dict:
        """Get configuration for a specific module"""
        return self.module_configs.get(module_name, {})
    
    def get_similarity_config(self) -> Dict:
        """Get similarity module configuration"""
        return self.get_module_config("similarity")
    
    def get_utils_config(self) -> Dict:
        """Get utils module configuration"""
        return self.get_module_config("utils")
    
    # Additional module-specific methods...
```

#### **Module-Specific Config Loaders**
```python
class SimilarityConfigLoader:
    """Dedicated loader for similarity module configs"""
    
class UtilsConfigLoader:
    """Dedicated loader for utils module configs"""
    
class ModelsConfigLoader:
    """Dedicated loader for models module configs"""
```

### 🚀 **Migration Timeline**

#### **Week 1: Planning & Extraction**
- [ ] Analyze current `architectural_config.yaml` sections
- [ ] Create module directory structure
- [ ] Extract configurations into module-specific files

#### **Week 2: Configuration Manager Updates**
- [ ] Extend `ArchitecturalConfigManager` for module loading
- [ ] Create module-specific config loaders
- [ ] Implement backward compatibility layer

#### **Week 3: Data Configuration Consolidation**
- [ ] Merge duplicate field mapping configurations
- [ ] Standardize data source definitions
- [ ] Update data loading processes

#### **Week 4: Testing & Documentation**
- [ ] Test all existing functionality with new structure
- [ ] Update configuration documentation
- [ ] Create migration guide for users

### ✅ **Success Criteria**

1. **Zero Functional Regression** - All existing features work unchanged
2. **Module Alignment** - Each src module has dedicated config directory
3. **Configuration Discoverability** - Easy to find configs for specific modules
4. **Reduced Complexity** - Smaller, focused configuration files
5. **PTH Compliance** - Follows enterprise configuration patterns
6. **Developer Experience** - Improved config management workflow

### 🎯 **Expected Outcomes**

- **15-20 focused config files** instead of 1 monolithic file
- **Clear src module alignment** - easy config discovery
- **50%+ reduction** in individual config file size
- **Enhanced maintainability** - isolated module concerns
- **Improved testing** - module configs testable independently
- **Better documentation** - module-specific config guides

This reorganization transforms the config system from a monolithic structure to a modular, enterprise-grade configuration architecture that directly mirrors your src module organization while maintaining all existing functionality. 