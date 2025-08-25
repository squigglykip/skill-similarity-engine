# Repository Transfer Scripts

These PowerShell scripts allow you to "fold" an entire repository into a single `.txt` file for transfer, then "unfold" it back into the original directory structure.

## Quick Start

### On the Source Computer:

1. Open PowerShell in your repository directory
2. Run the folding script:
   ```powershell
   .\fold-repo.ps1
   ```
3. This creates `repo-folded.txt` - transfer this file to your destination computer

### On the Destination Computer:

1. Copy the folded file and `unfold-repo.ps1` to your desired location
2. Open PowerShell in that directory
3. Run the unfolding script:
   ```powershell
   .\unfold-repo.ps1
   ```

## Detailed Usage

### fold-repo.ps1

Packages your repository into a single text file.

```powershell
# Basic usage (current directory)
.\fold-repo.ps1

# Custom source path and output file
.\fold-repo.ps1 -SourcePath "C:\MyProject" -OutputFile "my-project.txt"

# Specify custom .gitignore file
.\fold-repo.ps1 -GitIgnoreFile "custom.gitignore"
```

**Parameters:**
- `-SourcePath`: Source directory (default: current directory)
- `-OutputFile`: Output filename (default: `repo-folded.txt`)
- `-GitIgnoreFile`: Gitignore file to use (default: `.gitignore`)

### unfold-repo.ps1

Extracts a folded repository back into its original structure.

```powershell
# Basic usage (current directory)
.\unfold-repo.ps1

# Custom input file and output directory
.\unfold-repo.ps1 -InputFile "my-project.txt" -OutputPath "C:\ExtractedProject"

# Force overwrite existing files
.\unfold-repo.ps1 -Force
```

**Parameters:**
- `-InputFile`: Folded repository file (default: `repo-folded.txt`)
- `-OutputPath`: Destination directory (default: current directory)
- `-Force`: Overwrite existing files without prompting

## What Gets Included/Excluded

### ✅ Included:
- All text files (Python, JavaScript, HTML, CSS, YAML, etc.)
- Binary files (images, PDFs, etc.) - encoded as Base64
- Directory structure is preserved
- File modification timestamps
- Files up to 50MB in size

### ❌ Excluded (respects .gitignore + additional patterns):
- **Git repository data**: `.git/`
- **Python cache files**: `__pycache__/`, `*.pyc`, `*.pyo`, `*.pyd`
- **Virtual environments**: `venv/`, `env/`
- **Build artifacts**: `dist/`, `build/`
- **Data files**: `*.csv`, `*.xlsx`, `*.xls`, `*.tsv`
- **Database files**: `*.sqlite`, `*.sqlite3`, `*.db`, `*.mdb`
- **Model/ML files**: `*.joblib`, `*.pkl`, `*.pickle`, `*.h5`, `*.hdf5`, `*.model`
- **Large text files**: `*.txt` (exports, logs, etc.)
- **Entire directories**: `data/`, `models/`, `exports/`
- **Documentation builds**: `docs/_build/`, `docs/*.html`
- **Log files**: `*.log`
- **Local configuration overrides**
- **All patterns in your `.gitignore`**

**Result**: Only source code, configuration files, and documentation markdown are included.

## File Format

The folded file uses a simple text-based format with clear delimiters:

```
=== FOLDED REPOSITORY ===
Generated: 2025-01-27 14:30:00
Source: C:\MyProject
=== BEGIN REPOSITORY DATA ===

=== FILE START ===
PATH: src/main.py
TYPE: TEXT
ENCODING: UTF8
=== CONTENT START ===
[file content here]
=== CONTENT END ===
=== FILE END ===

=== FILE START ===
PATH: images/logo.png
TYPE: BINARY
ENCODING: BASE64
=== CONTENT START ===
[base64 encoded content]
=== CONTENT END ===
=== FILE END ===

=== END REPOSITORY DATA ===
```

## Tips

1. **Large repositories**: The script automatically skips files over 50MB. For very large repos, consider excluding additional directories in your `.gitignore`.

2. **Binary files**: Images, PDFs, and other binary files are base64-encoded, which increases their size by ~33%. Factor this in for transfer limits.

3. **Safety**: The unfold script warns before overwriting existing content. Use `-Force` if you're sure.

4. **Validation**: Both scripts provide detailed output showing what's being processed and any errors encountered.

5. **Cross-platform**: While designed for Windows PowerShell, the folded `.txt` file can be processed on any system that can handle the text format.

## Troubleshooting

**"Execution policy" error**: Run this first:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**"File too large" warnings**: Modify the 50MB limit in `fold-repo.ps1` if needed, or add large files to `.gitignore`.

**Out of memory errors**: For very large repositories, consider excluding more file types or processing in smaller chunks.

**Permission errors**: Ensure you have write permissions to the output directory.
