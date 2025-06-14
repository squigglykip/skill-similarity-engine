# New Precompute Workflow Architecture

## 🎯 Overview

The precompute workflow has been restructured for better performance, consistency, and maintainability. All heavy computation now happens in **Step 1 (Precompute)**, while **Step 2 (Business Context)** focuses solely on data ingestion.

## 🔄 New Workflow

### **Step 1: Precompute Engine (Option 1)**
**Location**: `main.py` → Option 1 → Option 2  
**Module**: `similarity/precompute.py`

**What it does:**
- ✅ Generates **job-to-job similarity matrix** using chunked/parallel processing
- ✅ Generates **career pathways table** from similarity data
- ✅ Outputs **both as parquet files** for consistent format
- ✅ Uses your performance utilities (`progress.py`, `chunking.py`, `parallel.py`)

**Output Files:**
```
models/2025-Q2/precompute_YYYYMMDD_HHMMSS/
├── job_similarity_matrix.csv          # Primary similarity data
├── job_similarity_matrix.parquet      # Optional compressed format  
├── career_pathways.parquet            # ⭐ NEW: Pre-computed pathways
├── career_pathways.csv                # Human-readable format
├── metadata.json                      # Run information
└── progress.json                      # Progress tracking
```

### **Step 2: Business Context Database (Option 2)**
**Location**: `main.py` → Option 2  
**Module**: `business_context/data_loader.py`

**What it does:**
- ✅ Loads **pre-computed parquet files** into SQLite database
- ✅ **No on-the-fly computation** - just data ingestion
- ✅ Much faster and more reliable

**Input Files:**
```
📥 Loads from Step 1 outputs:
├── job_similarity_matrix.csv         # → job_similarities table
└── career_pathways.parquet           # → career_pathways table
```

## 📊 Benefits

### **🚀 Performance**
- **Consistent output format**: Both similarity matrix and career pathways as parquet
- **Faster Business Context generation**: No heavy computation in Step 2
- **Better memory management**: Chunked processing for both operations

### **🔧 Architecture**
- **Clean separation**: Heavy compute (Step 1) vs. Data ingestion (Step 2)
- **Resumable processing**: If Step 2 fails, no need to recompute Step 1
- **Consistent tooling**: Same progress tracking and chunking for both outputs

### **🎯 Reliability**
- **No more 714→3→2→1 issue**: Pre-computed relationships eliminate on-the-fly limitations
- **Deterministic output**: Same input always produces same career pathways
- **Better error handling**: Failures in one step don't affect the other

## 🛠 Usage

### **Generate Both Parquet Files**
```bash
python main.py
# Select: 1 (Precompute Engine)
# Select: 2 (Generate similarity matrix + career pathways)
```

This creates **both** output files:
- `job_similarity_matrix.csv` 
- `career_pathways.parquet` ⭐

### **Load Into Business Context Database**
```bash
python main.py  
# Select: 2 (Generate Business Context Database)
```

This loads the parquet files into SQLite.

### **Test The New Workflow**
```bash
python test_new_precompute_workflow.py
```

## 🔍 Technical Details

### **Career Pathways Generation** 
**New Location**: `similarity/precompute.py` → `precompute_career_pathways()`

**Key Features:**
- ✅ **Chunked processing** using `AdaptiveChunker`
- ✅ **Progress tracking** with beautiful tqdm bars
- ✅ **Memory management** with garbage collection
- ✅ **Top N similar jobs** per source job (configurable, default: 12)
- ✅ **Career move classification** (lateral, progression, cross_family)
- ✅ **Difficulty scoring** with cross-family penalties

### **Complete Pipeline**
**New Method**: `precompute_all()` 

```python
# Step 1: Generate similarity matrix
output_path = precomputer.precompute_similarity_matrix()

# Step 2: Load similarity data and generate career pathways  
similarity_df = pd.read_csv(output_path / "job_similarity_matrix.csv")
pathways_file = precomputer.precompute_career_pathways(similarity_df, output_path)

# Step 3: Create metadata with both outputs
metadata = {
    'outputs': {
        'similarity_matrix_csv': str(similarity_file),
        'career_pathways_parquet': str(pathways_file),
        'career_pathways_csv': str(csv_file)
    }
}
```

## 📈 Performance Improvements

### **Before (Old Workflow)**
1. **Step 1**: Generate similarity matrix only
2. **Step 2**: Load similarity data → Generate career pathways on-the-fly → Limited by SQL performance

### **After (New Workflow)**  
1. **Step 1**: Generate **both** similarity matrix + career pathways with full performance utilities
2. **Step 2**: Simple parquet file ingestion → No computation

### **Expected Improvements**
- ⚡ **Step 2 speed**: 5-10x faster (no computation, just loading)
- 🧠 **Step 2 memory**: Much lower (no processing, just ingestion)  
- 🎯 **Reliability**: No more tree generation issues (pre-computed relationships)
- 🔄 **Consistency**: Same chunking/parallel infrastructure for both outputs

## 🗂 Migration Notes

### **What Changed**
- ✅ `precompute.py`: Added `precompute_career_pathways()` and `precompute_all()`
- ✅ `data_loader.py`: Replaced `_generate_career_pathways_data()` with `_load_career_pathways_from_parquet()`
- ✅ `main.py`: Updated menu descriptions and uses `precompute_all()`

### **What Stayed The Same**
- ✅ All existing SQL queries and web app functionality
- ✅ Database schema (same tables, same structure)
- ✅ Output file formats (CSV for compatibility, parquet for performance)
- ✅ Configuration and CLI interface

### **Backwards Compatibility**
- ✅ If no parquet file found, business context loader provides helpful error message
- ✅ Existing similarity matrix files are still supported
- ✅ All existing functionality continues to work

## 🚀 Next Steps

1. **Run the new workflow** to generate both parquet files
2. **Test career pathways performance** in the web app (should be much faster!)
3. **Verify tree generation** now shows full relationships (no more 3→2→1 limitation)
4. **Optional**: Set up automated pipeline to regenerate quarterly

---

**🎉 Result**: Clean architecture, better performance, and more reliable career pathway generation! 