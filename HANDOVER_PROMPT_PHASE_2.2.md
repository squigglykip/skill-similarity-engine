# Phase 2.2 ML Model Training - Comprehensive Handover Prompt

## **🎯 PROJECT CONTEXT & CURRENT STATUS**

You are taking over the **NAB Workforce Intelligence Platform** project, specifically to implement **Phase 2.2: Movement Analysis ML Model Training**. This is a production-grade workforce analytics system that has successfully completed Phase 2.1 (Movement Pattern Population) and is ready for ML model training implementation.

### **✅ WHAT HAS BEEN COMPLETED (Phase 2.1)**

**Movement Pattern Population - FULLY WORKING:**
- ✅ **25,608 movement patterns** successfully populated in `analytics_movement_patterns` table
- ✅ **26,738 individual movements** detected from **197,224 employees** across **49 months** (July 2021 - July 2025)
- ✅ **Database integration** complete with SQLite queries replacing CSV file loading
- ✅ **CLI integration** working with user-friendly menu system in `main.py`
- ✅ **Data quality validated** - zero null positions, zero duplicates, realistic seasonal patterns
- ✅ **Performance optimized** - 18.4s movement detection, 433MB peak memory usage

**Technical Infrastructure Ready:**
- ✅ **MovementPatternPopulationCommand** fully implemented in `src/skill_similarity_engine/cli/commands/precompute_commands.py`
- ✅ **Analytics orchestrator** integrated with `execute_movement_pattern_analysis()` method working
- ✅ **Database schema** complete with proper indexes and relationships
- ✅ **Progress tracking** and structured logging throughout the pipeline
- ✅ **Memory-aware processing** with adaptive chunking for large datasets

### **🎯 YOUR MISSION: Phase 2.2 - ML Model Training**

**GOAL:** Implement machine learning model training that consumes the populated movement patterns data to create predictive models for career pathway feasibility and transition likelihood.

**DELIVERABLES:**
1. **ML Training Command** - `MovementMLTrainingCommand` class
2. **Model Training Pipeline** - Port notebook ML logic to production architecture  
3. **Model Persistence** - Save trained models as `.joblib` files for webapp consumption
4. **CLI Integration** - Connect to existing menu system
5. **Analytics Orchestrator** - Implement `execute_movement_ml_training()` method

---

## **📊 DATA AVAILABLE FOR ML TRAINING**

### **Primary Data Source: `analytics_movement_patterns` Table**
**Location:** `models/2025-Q3/business_context.sqlite`
**Records:** 25,608 validated movement patterns
**Schema:**
```sql
CREATE TABLE analytics_movement_patterns (
    movement_pattern_id TEXT PRIMARY KEY,
    movement_month TEXT,                    -- e.g., "2024-01"
    from_position TEXT,                     -- Source position number
    to_position TEXT,                       -- Destination position number  
    from_job_profile_id TEXT,              -- Source job profile (for enrichment)
    to_job_profile_id TEXT,                -- Destination job profile (for enrichment)
    movement_count INTEGER,                 -- Number of movements in this pattern
    unique_employees INTEGER,               -- Number of unique people
    avg_days_between REAL,                 -- Average duration (92.6 days avg)
    pct_total_movements REAL,              -- Percentage of monthly movements
    movement_type TEXT,                     -- Movement classification
    skill_similarity_score REAL,           -- For ML features (currently NULL)
    difficulty_score REAL,                 -- For ML features (currently NULL)  
    success_rate REAL,                     -- For ML features (currently NULL)
    created_timestamp TEXT
);
```

### **Supporting Data for Feature Engineering:**
- **`core_position_timeline`** (482K records) - Position details with JobProfileID
- **`core_colleague_positions_history`** (2M records) - Individual employee movements
- **`core_job_architecture`** - Job profiles with skill requirements
- **`core_skills_taxonomy`** - Skills definitions and relationships

### **Data Quality Confirmed:**
- **Seasonal patterns** realistic (July peaks: 1089 patterns, Holiday lows: 238 patterns)
- **Movement volumes** distributed: 24,512 single movements, 1,096 multi-movements (2-5 range)
- **Duration spread** healthy: 50% < 1 month, 26% 6-12 months, avg 92.6 days
- **Position networks** identified: Hub positions with 16-19 outbound patterns

---

## **🔬 ML PIPELINE REQUIREMENTS (From Research Notebook)**

### **Source Material: `movement_analysis_engine.py`**
**Location:** `skill-similarity-engine/notebook/movement_analysis_engine.py`
**Size:** 1,147 lines of research code to be ported to production

**Key ML Components to Port:**
1. **Feature Engineering Pipeline** - Transform movement patterns into ML features
2. **Model Training** - Random Forest, XGBoost, Gradient Boosting ensemble
3. **Pathway Prediction** - Generate feasibility scores for career transitions
4. **Model Evaluation** - Cross-validation and performance metrics
5. **Model Persistence** - Save models and metadata for webapp consumption

### **Expected Model Architecture:**
```python
# Models to implement:
- RandomForestClassifier (pathway feasibility)
- XGBClassifier (transition likelihood) 
- GradientBoostingClassifier (success prediction)
- Ensemble voting classifier (combined predictions)

# Output files expected:
- random_forest_model.joblib
- xgboost_model.joblib  
- gradient_boosting_model.joblib
- ensemble_model.joblib
- feature_engineering_pipeline.joblib
- pathway_predictions.parquet
- model_metadata.json
```

### **Feature Engineering Requirements:**
- **Position Features** - Job profile similarities, skill overlaps
- **Temporal Features** - Seasonal patterns, duration trends
- **Network Features** - Position connectivity, hub analysis
- **Historical Features** - Success rates, transition frequencies

---

## **🏗️ IMPLEMENTATION ARCHITECTURE**

### **Target Files to Create/Modify:**

#### **1. ML Training Command**
**File:** `src/skill_similarity_engine/cli/commands/precompute_commands.py`
**Action:** Add `MovementMLTrainingCommand` class
**Pattern:** Follow existing `MovementPatternPopulationCommand` structure

```python
class MovementMLTrainingCommand(BaseCommand):
    """Train ML models from populated movement patterns data."""
    
    def execute(self, **kwargs) -> CommandResult:
        # 1. Load movement patterns from database
        # 2. Engineer features for ML training
        # 3. Train ensemble of models (RF, XGB, GB)
        # 4. Evaluate model performance
        # 5. Save models and metadata
        # 6. Generate pathway predictions
        pass
```

#### **2. Analytics Orchestrator Integration**
**File:** `src/skill_similarity_engine/business_context/analytics_orchestrator.py`
**Action:** Implement `execute_movement_ml_training()` method
**Pattern:** Follow existing `execute_phase_1_enhanced_similarity()` structure

#### **3. CLI Menu Integration**  
**File:** `main.py`
**Action:** Connect "Train Predictive Movement Models" menu option
**Current Status:** Menu option exists but shows "not yet implemented"

#### **4. Model Training Pipeline**
**File:** `src/skill_similarity_engine/models/movement_ml_trainer.py` (NEW)
**Action:** Create modular ML training pipeline
**Responsibilities:** Feature engineering, model training, evaluation, persistence

### **Configuration Integration:**
- **Use existing** `ArchitecturalConfigManager` for ML hyperparameters
- **Follow patterns** from `enhanced_similarity.yaml` for configuration structure
- **Create** `movement_ml_training.yaml` configuration file

---

## **🔧 TECHNICAL PATTERNS TO FOLLOW**

### **Established Patterns (CRITICAL - Must Follow):**
1. **Progress Tracking** - Use `ProgressTracker` for all long-running operations
2. **Memory Management** - Use `AdaptiveChunker` for large dataset processing  
3. **Structured Logging** - Use `self.logger.info()` with performance metrics
4. **Error Handling** - Return `CommandResult` with success/failure status
5. **Configuration** - Use `get_config_manager()` for externalized parameters
6. **Database Connections** - Use established connection patterns with transactions

### **Code Quality Standards:**
- **Type Hints** - All function signatures must include type annotations
- **Docstrings** - Comprehensive documentation for all classes and methods
- **Error Recovery** - Graceful handling of missing data or model training failures
- **Performance Metrics** - Track training time, memory usage, model performance
- **Validation** - Verify data quality before training, validate model outputs

### **Integration Points:**
- **Import existing modules** - Reuse `MovementTracker`, `MovementFactBuilder` logic where applicable
- **Database integration** - Use existing `DatabaseIntegrator` for data access
- **Model versioning** - Use existing `ModelVersionManager` for output directory management
- **CLI architecture** - Inherit from `BaseCommand`, integrate with `CommandFactory`

---

## **📁 PROJECT STRUCTURE REFERENCE**

```
skill-similarity-engine/
├── src/skill_similarity_engine/
│   ├── cli/commands/precompute_commands.py     # Add MovementMLTrainingCommand here
│   ├── business_context/analytics_orchestrator.py  # Add execute_movement_ml_training()
│   ├── models/                                 # Create movement_ml_trainer.py here
│   ├── config/                                # Add movement_ml_training.yaml here
│   └── utils/                                 # Use progress.py, parallel.py, chunking.py
├── main.py                                    # CLI integration point
├── notebook/movement_analysis_engine.py       # Source ML code to port
├── models/2025-Q3/business_context.sqlite     # Database with populated patterns
└── docs/PRECOMPUTE_ENGINE_REDESIGN_PLAN.md    # Complete project documentation
```

---

## **🎯 IMMEDIATE NEXT STEPS**

### **Step 1: Analyze Source Material**
1. **Read** `notebook/movement_analysis_engine.py` to understand ML pipeline
2. **Review** `docs/PRECOMPUTE_ENGINE_REDESIGN_PLAN.md` Phase 2.2 section for detailed requirements
3. **Examine** existing `MovementPatternPopulationCommand` for architectural patterns

### **Step 2: Create ML Training Infrastructure**
1. **Create** `MovementMLTrainingCommand` class following established patterns
2. **Implement** feature engineering pipeline from notebook research
3. **Port** model training logic with proper error handling and progress tracking

### **Step 3: Integrate with Existing System**
1. **Add** `execute_movement_ml_training()` to analytics orchestrator
2. **Connect** CLI menu option to new command
3. **Test** end-to-end pipeline from menu selection to model file generation

### **Step 4: Model Persistence & Validation**
1. **Save** trained models using established model versioning patterns
2. **Generate** pathway predictions for webapp consumption
3. **Validate** model outputs against business logic expectations

---

## **⚠️ CRITICAL SUCCESS FACTORS**

### **Must-Have Requirements:**
1. **Follow existing patterns** - Don't reinvent architecture, extend it
2. **Maintain performance** - Process 25K patterns efficiently with progress tracking
3. **Ensure data quality** - Validate inputs, handle edge cases gracefully
4. **Generate usable outputs** - Models must be consumable by webapp layer
5. **Comprehensive logging** - Track performance metrics and business KPIs

### **Quality Gates:**
- **Models train successfully** without memory issues or crashes
- **CLI integration works** seamlessly with existing menu system  
- **Model files generated** in correct format for webapp consumption
- **Performance acceptable** - training completes in reasonable time (<10 minutes)
- **Business validation** - Model predictions make sense for career transitions

### **Testing Strategy:**
- **Unit tests** for feature engineering pipeline
- **Integration tests** for end-to-end ML training workflow
- **Performance tests** for memory usage and training time
- **Business validation** of model predictions against known career patterns

---

## **📚 KEY REFERENCE FILES**

### **Must Read (in order):**
1. `docs/PRECOMPUTE_ENGINE_REDESIGN_PLAN.md` - Complete project context and Phase 2.2 requirements
2. `notebook/movement_analysis_engine.py` - Source ML pipeline to port (1,147 lines)
3. `src/skill_similarity_engine/cli/commands/precompute_commands.py` - Existing command patterns
4. `src/skill_similarity_engine/business_context/analytics_orchestrator.py` - Integration patterns
5. `main.py` - CLI menu integration point

### **Architecture Reference:**
- `src/skill_similarity_engine/models/movement_fact_builder.py` - Data transformation patterns
- `src/skill_similarity_engine/utils/progress.py` - Progress tracking implementation
- `src/skill_similarity_engine/config/architectural_config_manager.py` - Configuration patterns

---

## **🚀 SUCCESS DEFINITION**

**You will have succeeded when:**
1. ✅ User can select "Train Predictive Movement Models" from main menu
2. ✅ ML training executes with proper progress tracking and logging
3. ✅ Model files are generated in `models/2025-Q3/` directory
4. ✅ Training completes without memory issues or crashes
5. ✅ Model predictions are generated and saved for webapp consumption
6. ✅ Performance metrics are logged (training time, model accuracy, etc.)

**Final validation:** The user should be able to run the complete workflow:
`main.py` → "Generate Career Intelligence" → "Train Predictive Movement Models" → Success message with model file locations

---

## **💡 IMPLEMENTATION HINTS**

### **Start Small:**
- Begin with basic feature engineering from the database
- Implement one model (Random Forest) first, then expand to ensemble
- Use existing progress tracking patterns for user feedback

### **Leverage Existing Code:**
- The `MovementPatternPopulationCommand` is an excellent template
- Reuse database connection and transaction patterns
- Follow the same error handling and logging approach

### **Focus on Integration:**
- Ensure CLI menu integration works seamlessly
- Use established configuration management patterns
- Generate outputs in expected locations for webapp consumption

**Good luck! The foundation is solid and the path forward is clear. The movement patterns data is high-quality and ready for ML training.** 🎯