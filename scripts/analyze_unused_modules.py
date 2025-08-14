#!/usr/bin/env python3
"""
Unused Module Analyzer
======================

Industry-standard dependency analysis tool for Python projects.
Identifies unused modules by building a dependency tree from entry points.

This script uses multiple approaches:
1. Static AST analysis to find imports
2. Dependency tree construction from entry points
3. Dead code detection using industry-standard patterns

Usage:
    python scripts/analyze_unused_modules.py
    python scripts/analyze_unused_modules.py --entry-points main.py run_webapp.py
    python scripts/analyze_unused_modules.py --format json
    python scripts/analyze_unused_modules.py --include-tests

Features:
- Builds dependency trees from entry points (main.py, run_webapp.py)
- Identifies unused modules in src/ directory
- Supports multiple output formats (tree, json, summary)
- Handles dynamic imports and conditional imports
- Provides actionable recommendations for cleanup

Industry Standards:
- Follows patterns from tools like vulture, unimport, and dead
- Uses AST parsing for accurate import detection
- Implements graph traversal for dependency analysis
"""

import ast
import argparse
import json
import os
import sys
from collections import defaultdict, deque
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Union
from dataclasses import dataclass, field
import importlib.util


@dataclass
class ModuleInfo:
    """Information about a Python module."""
    path: Path
    name: str
    imports: Set[str] = field(default_factory=set)
    imported_by: Set[str] = field(default_factory=set)
    is_entry_point: bool = False
    is_test: bool = False
    is_used: bool = False
    lines_of_code: int = 0


@dataclass
class AnalysisResult:
    """Results of the unused module analysis."""
    total_modules: int
    used_modules: int
    unused_modules: int
    unused_module_list: List[str]
    dependency_tree: Dict[str, List[str]]
    entry_points: List[str]
    recommendations: List[str]


class ImportVisitor(ast.NodeVisitor):
    """Enhanced AST visitor to extract import statements including dynamic ones."""
    
    def __init__(self, current_module: str = ""):
        self.imports = set()
        self.from_imports = set()
        self.dynamic_imports = set()
        self.string_imports = set()
        self.current_module = current_module
        self.function_level_imports = set()
        self.conditional_imports = set()
        self._in_function = False
        self._in_try_except = False
    
    def visit_FunctionDef(self, node):
        """Track when we're inside a function."""
        old_in_function = self._in_function
        self._in_function = True
        self.generic_visit(node)
        self._in_function = old_in_function
    
    def visit_AsyncFunctionDef(self, node):
        """Track async functions too."""
        old_in_function = self._in_function
        self._in_function = True
        self.generic_visit(node)
        self._in_function = old_in_function
    
    def visit_Try(self, node):
        """Track when we're inside a try/except block."""
        old_in_try = self._in_try_except
        self._in_try_except = True
        self.generic_visit(node)
        self._in_try_except = old_in_try
    
    def visit_Import(self, node):
        """Handle 'import module' statements."""
        for alias in node.names:
            import_name = alias.name
            self.imports.add(import_name)
            
            # Track context
            if self._in_function:
                self.function_level_imports.add(import_name)
            if self._in_try_except:
                self.conditional_imports.add(import_name)
    
    def visit_ImportFrom(self, node):
        """Handle 'from module import name' statements."""
        if node.module:
            self.from_imports.add(node.module)
            
            # Track context
            if self._in_function:
                self.function_level_imports.add(node.module)
            if self._in_try_except:
                self.conditional_imports.add(node.module)
            
            # Also add the full module path for relative imports
            for alias in node.names:
                if alias.name != '*':
                    full_name = f"{node.module}.{alias.name}"
                    self.from_imports.add(full_name)
                    if self._in_function:
                        self.function_level_imports.add(full_name)
                    if self._in_try_except:
                        self.conditional_imports.add(full_name)
    
    def visit_Call(self, node):
        """Detect dynamic imports like importlib.import_module(), __import__()."""
        # Check for importlib.import_module()
        if (isinstance(node.func, ast.Attribute) and
            isinstance(node.func.value, ast.Name) and
            node.func.value.id == 'importlib' and
            node.func.attr == 'import_module'):
            if node.args and isinstance(node.args[0], ast.Str):
                module_name = node.args[0].s
                self.dynamic_imports.add(module_name)
        
        # Check for __import__()
        elif (isinstance(node.func, ast.Name) and
              node.func.id == '__import__'):
            if node.args and isinstance(node.args[0], ast.Str):
                module_name = node.args[0].s
                self.dynamic_imports.add(module_name)
        
        # Check for exec() and eval() with import strings (less reliable but worth checking)
        elif (isinstance(node.func, ast.Name) and
              node.func.id in ('exec', 'eval')):
            if node.args and isinstance(node.args[0], ast.Str):
                code_str = node.args[0].s
                if 'import ' in code_str:
                    # Basic pattern matching for imports in strings
                    import re
                    import_matches = re.findall(r'(?:from\s+(\S+)\s+)?import\s+(\S+)', code_str)
                    for from_module, import_name in import_matches:
                        if from_module:
                            self.string_imports.add(from_module)
                        self.string_imports.add(import_name)
        
        self.generic_visit(node)
    
    def visit_Str(self, node):
        """Look for module names in string literals (heuristic)."""
        # This is a heuristic approach - look for strings that look like module names
        # in the context of our project
        string_value = getattr(node, 'value', getattr(node, 's', ''))
        if (self.current_module and 
            'skill_similarity_engine' in string_value and
            '.' in string_value and
            not ' ' in string_value):
            self.string_imports.add(string_value)
        self.generic_visit(node)
    
    def visit_Constant(self, node):
        """Handle string constants in newer Python versions."""
        if isinstance(node.value, str):
            if (self.current_module and 
                'skill_similarity_engine' in node.value and
                '.' in node.value and
                not ' ' in node.value):
                self.string_imports.add(node.value)
        self.generic_visit(node)
    
    def get_all_imports(self) -> set:
        """Get all imports found by this visitor."""
        return (self.imports | self.from_imports | 
                self.dynamic_imports | self.string_imports)


class UnusedModuleAnalyzer:
    """Analyzes Python codebase for unused modules using industry-standard techniques."""
    
    def __init__(self, project_root: Path, src_dir: str = "src"):
        self.project_root = project_root
        self.src_dir = project_root / src_dir
        self.modules: Dict[str, ModuleInfo] = {}
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_deps: Dict[str, Set[str]] = defaultdict(set)
        
        if not self.src_dir.exists():
            raise FileNotFoundError(f"Source directory not found: {self.src_dir}")
    
    def discover_modules(self, include_tests: bool = False) -> None:
        """Discover all Python modules in the source directory."""
        print(f"🔍 Discovering modules in {self.src_dir}...")
        
        for py_file in self.src_dir.rglob("*.py"):
            # Calculate relative path from src directory
            relative_path = py_file.relative_to(self.src_dir)
            module_name = str(relative_path.with_suffix("")).replace(os.sep, ".")
            
            # Skip test files unless explicitly included
            is_test = any(part.startswith("test") for part in relative_path.parts)
            if is_test and not include_tests:
                continue
            
            # Count lines of code (excluding comments and empty lines)
            lines_of_code = self._count_lines_of_code(py_file)
            
            # Determine if this is an __init__.py file
            is_init_file = py_file.name == "__init__.py"
            
            module_info = ModuleInfo(
                path=py_file,
                name=module_name,
                is_test=is_test,
                lines_of_code=lines_of_code
            )
            
            # Mark __init__.py files as always used (they're required for Python packages)
            if is_init_file:
                module_info.is_used = True
                module_info.imported_by.add("PACKAGE_STRUCTURE")
            
            self.modules[module_name] = module_info
        
        print(f"📊 Found {len(self.modules)} modules")
    
    def _count_lines_of_code(self, file_path: Path) -> int:
        """Count non-empty, non-comment lines of code."""
        try:
            # Handle BOM and various encodings
            encodings = ['utf-8-sig', 'utf-8', 'utf-16', 'cp1252']
            content = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                return 0
            
            lines = content.splitlines()
            loc = 0
            for line in lines:
                stripped = line.strip()
                if stripped and not stripped.startswith('#'):
                    loc += 1
            return loc
        except Exception:
            return 0
    
    def analyze_imports(self) -> None:
        """Analyze import statements in all modules."""
        print("🔗 Analyzing import relationships...")
        
        for module_name, module_info in self.modules.items():
            try:
                # Handle BOM and various encodings
                encodings = ['utf-8-sig', 'utf-8', 'utf-16', 'cp1252']
                content = None
                
                for encoding in encodings:
                    try:
                        with open(module_info.path, 'r', encoding=encoding) as f:
                            content = f.read()
                        break
                    except UnicodeDecodeError:
                        continue
                
                if content is None:
                    print(f"⚠️  Warning: Could not read {module_info.path}: encoding issues")
                    continue
                
                # Parse AST to extract imports
                tree = ast.parse(content)
                visitor = ImportVisitor(current_module=module_name)
                visitor.visit(tree)
                
                # Process all types of imports
                all_imports = visitor.get_all_imports()
                for import_name in all_imports:
                    # Normalize import to match our module naming
                    normalized_import = self._normalize_import(import_name, module_name)
                    if normalized_import and normalized_import in self.modules:
                        module_info.imports.add(normalized_import)
                        self.dependency_graph[module_name].add(normalized_import)
                        self.reverse_deps[normalized_import].add(module_name)
                        
                        # Track the type of import for better reporting
                        import_type = "STATIC"
                        if import_name in visitor.dynamic_imports:
                            import_type = "DYNAMIC"
                        elif import_name in visitor.function_level_imports:
                            import_type = "FUNCTION_LEVEL"
                        elif import_name in visitor.conditional_imports:
                            import_type = "CONDITIONAL"
                        elif import_name in visitor.string_imports:
                            import_type = "STRING_BASED"
                        
                        self.modules[normalized_import].imported_by.add(f"{module_name}:{import_type}")
                
            except Exception as e:
                print(f"⚠️  Warning: Could not analyze {module_info.path}: {e}")
    
    def _normalize_import(self, import_name: str, current_module: str) -> Optional[str]:
        """Normalize import names to match our module naming convention."""
        # Handle relative imports
        if import_name.startswith('.'):
            parts = current_module.split('.')
            level = 0
            for char in import_name:
                if char == '.':
                    level += 1
                else:
                    break
            
            if level > len(parts):
                return None
            
            base_parts = parts[:-level] if level > 0 else parts
            remaining_import = import_name[level:]
            if remaining_import:
                return '.'.join(base_parts + [remaining_import])
            else:
                return '.'.join(base_parts)
        
        # Handle absolute imports within our package
        if import_name.startswith('skill_similarity_engine'):
            return import_name
        
        # Check if it's a submodule of current module
        current_package = '.'.join(current_module.split('.')[:-1])
        if current_package:
            potential_module = f"{current_package}.{import_name}"
            if potential_module in self.modules:
                return potential_module
        
        return import_name if import_name in self.modules else None
    
    def find_entry_points(self, entry_point_files: List[str]) -> None:
        """Identify entry point modules."""
        print(f"🚀 Identifying entry points: {entry_point_files}")
        
        for entry_file in entry_point_files:
            entry_path = self.project_root / entry_file
            if entry_path.exists():
                # For files in project root, we need to analyze their imports
                # into the src directory
                self._analyze_entry_point(entry_path, entry_file)
    
    def _analyze_entry_point(self, entry_path: Path, entry_name: str) -> None:
        """Analyze an entry point file and mark its dependencies as used."""
        try:
            # Handle BOM and various encodings
            encodings = ['utf-8-sig', 'utf-8', 'utf-16', 'cp1252']
            content = None
            
            for encoding in encodings:
                try:
                    with open(entry_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                print(f"⚠️  Warning: Could not read entry point {entry_path}: encoding issues")
                return
            
            tree = ast.parse(content)
            visitor = ImportVisitor(current_module=f"ENTRY_POINT:{entry_name}")
            visitor.visit(tree)
            
            # Mark entry point dependencies as used
            all_imports = visitor.get_all_imports()
            for import_name in all_imports:
                if import_name.startswith('skill_similarity_engine'):
                    # Find matching module in our src directory
                    for module_name in self.modules:
                        if module_name == import_name or import_name.startswith(module_name + '.'):
                            self.modules[module_name].is_used = True
                            
                            # Track the type of import from entry point
                            import_type = "STATIC"
                            if import_name in visitor.dynamic_imports:
                                import_type = "DYNAMIC"
                            elif import_name in visitor.function_level_imports:
                                import_type = "FUNCTION_LEVEL"
                            elif import_name in visitor.conditional_imports:
                                import_type = "CONDITIONAL"
                            elif import_name in visitor.string_imports:
                                import_type = "STRING_BASED"
                            
                            self.modules[module_name].imported_by.add(f"ENTRY_POINT:{entry_name}:{import_type}")
            
            print(f"✅ Analyzed entry point: {entry_name}")
            
        except Exception as e:
            print(f"⚠️  Warning: Could not analyze entry point {entry_path}: {e}")
    
    def build_dependency_tree(self, entry_points: List[str]) -> None:
        """Build dependency tree starting from entry points using BFS."""
        print("🌳 Building dependency tree from entry points...")
        
        # Mark entry points as used
        for entry_point in entry_points:
            if entry_point in self.modules:
                self.modules[entry_point].is_entry_point = True
                self.modules[entry_point].is_used = True
        
        # BFS to mark all reachable modules as used
        queue = deque()
        visited = set()
        
        # Start from entry points and their direct imports
        for module_name, module_info in self.modules.items():
            if module_info.is_used:
                queue.append(module_name)
                visited.add(module_name)
        
        while queue:
            current_module = queue.popleft()
            
            # Mark all imported modules as used
            for imported_module in self.dependency_graph[current_module]:
                if imported_module in self.modules and imported_module not in visited:
                    self.modules[imported_module].is_used = True
                    queue.append(imported_module)
                    visited.add(imported_module)
        
        print(f"📊 Marked {len(visited)} modules as used")
    
    def identify_unused_modules(self) -> List[str]:
        """Identify modules that are not used by any entry point."""
        unused = []
        
        for module_name, module_info in self.modules.items():
            if not module_info.is_used and not module_info.is_test:
                # Additional checks for modules that might be used in ways we can't detect
                if self._is_likely_used_module(module_name, module_info):
                    module_info.is_used = True
                    module_info.imported_by.add("HEURISTIC_DETECTION")
                else:
                    unused.append(module_name)
        
        return sorted(unused)
    
    def _is_likely_used_module(self, module_name: str, module_info: ModuleInfo) -> bool:
        """Check if a module is likely used based on common patterns."""
        # Always keep __init__.py files (already handled in discover_modules)
        if module_info.path.name == "__init__.py":
            return True
        
        # Keep modules that are commonly imported dynamically or by external tools
        dynamic_import_patterns = [
            'main',          # Entry point modules
            'cli',           # Command-line interfaces
            '__main__',      # Python -m execution
            'app',           # Flask/web applications
            'config',        # Configuration modules
            'settings',      # Settings modules
        ]
        
        module_basename = module_name.split('.')[-1]
        if module_basename in dynamic_import_patterns:
            return True
        
        # Keep modules that might be imported by external scripts or tools
        if module_name.endswith('.webapp.app'):
            return True
        
        # Project-specific patterns for skill-similarity-engine
        if self._has_project_specific_usage_patterns(module_name, module_info):
            return True
        
        return False
    
    def _has_project_specific_usage_patterns(self, module_name: str, module_info: ModuleInfo) -> bool:
        """Check for project-specific usage patterns that indicate a module is used."""
        try:
            content = self._read_file_content(module_info.path)
            if not content:
                return False
            
            # Pattern 1: Modules that are likely imported in try/except blocks
            # Look for modules that are imported elsewhere in conditional imports
            for other_module_name, other_module_info in self.modules.items():
                if other_module_name != module_name:
                    other_content = self._read_file_content(other_module_info.path)
                    if other_content:
                        # Look for dynamic import patterns
                        import re
                        
                        module_basename = module_name.split('.')[-1]
                        
                        # Pattern: from ..api.skills_updater import prompt_skills_update
                        relative_import_pattern = rf"from\s+\.\.api\.{module_basename}\s+import"
                        if re.search(relative_import_pattern, other_content):
                            return True
                        
                        # Pattern: from ...api.skills_updater import prompt_skills_update  
                        triple_relative_pattern = rf"from\s+\.\.\.api\.{module_basename}\s+import"
                        if re.search(triple_relative_pattern, other_content):
                            return True
                        
                        # Pattern: import skill_similarity_engine.api.lightcast_client
                        full_import_pattern = rf"import\s+{re.escape(module_name)}"
                        if re.search(full_import_pattern, other_content):
                            return True
            
            # Pattern 2: API client modules (often used dynamically)
            if 'client' in module_name.lower() or 'api' in module_name.lower():
                # Check if it defines client classes
                if 'class ' in content and ('Client' in content or 'API' in content):
                    return True
            
            # Pattern 3: Modules with factory patterns or plugin interfaces
            factory_patterns = ['factory', 'builder', 'creator', 'manager']
            if any(pattern in module_name.lower() for pattern in factory_patterns):
                return True
            
            # Pattern 4: Command modules (often imported dynamically by CLI)
            if 'command' in module_name.lower() and 'class ' in content:
                return True
            
            # Pattern 5: Modules that define important base classes
            if any(pattern in content for pattern in ['class.*Base', 'class.*Abstract', '@abstractmethod']):
                return True
            
        except Exception:
            pass
        
        return False
    
    def _read_file_content(self, file_path: Path) -> Optional[str]:
        """Read file content with encoding handling."""
        encodings = ['utf-8-sig', 'utf-8', 'utf-16', 'cp1252']
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        return None
    
    def generate_recommendations(self, unused_modules: List[str]) -> List[str]:
        """Generate actionable recommendations for cleanup."""
        recommendations = []
        
        if not unused_modules:
            recommendations.append("✅ No unused modules detected! Your codebase is clean.")
            return recommendations
        
        recommendations.append(f"🧹 Found {len(unused_modules)} potentially unused modules")
        recommendations.append("")
        recommendations.append("📋 Recommended Actions:")
        
        # Group by directory for better organization
        by_directory = defaultdict(list)
        total_loc = 0
        
        for module_name in unused_modules:
            module_info = self.modules[module_name]
            directory = str(module_info.path.parent.relative_to(self.src_dir))
            by_directory[directory].append((module_name, module_info.lines_of_code))
            total_loc += module_info.lines_of_code
        
        for directory, modules in sorted(by_directory.items()):
            recommendations.append(f"\n📁 {directory}/")
            for module_name, loc in sorted(modules):
                recommendations.append(f"   • {module_name} ({loc} lines)")
        
        recommendations.append(f"\n💾 Potential savings: {total_loc} lines of code")
        recommendations.append("")
        recommendations.append("⚠️  Before deleting:")
        recommendations.append("   1. Double-check for dynamic imports (importlib, __import__)")
        recommendations.append("   2. Verify no external scripts import these modules")
        recommendations.append("   3. Check for entry points not analyzed (scripts, tests)")
        recommendations.append("   4. Consider if modules are imported by external packages")
        
        return recommendations
    
    def analyze(self, entry_point_files: List[str], include_tests: bool = False) -> AnalysisResult:
        """Perform complete unused module analysis."""
        print("🔍 Starting unused module analysis...")
        print(f"📂 Project root: {self.project_root}")
        print(f"📦 Source directory: {self.src_dir}")
        print()
        
        # Step 1: Discover all modules
        self.discover_modules(include_tests)
        
        # Step 2: Analyze import relationships
        self.analyze_imports()
        
        # Step 3: Find and analyze entry points
        self.find_entry_points(entry_point_files)
        
        # Step 4: Build dependency tree
        entry_points_in_src = [name for name in self.modules if self.modules[name].is_entry_point]
        self.build_dependency_tree(entry_points_in_src)
        
        # Step 5: Identify unused modules
        unused_modules = self.identify_unused_modules()
        
        # Step 6: Generate recommendations
        recommendations = self.generate_recommendations(unused_modules)
        
        # Build dependency tree for output
        dependency_tree = {}
        for module_name, deps in self.dependency_graph.items():
            if self.modules[module_name].is_used:
                dependency_tree[module_name] = sorted(list(deps))
        
        return AnalysisResult(
            total_modules=len(self.modules),
            used_modules=sum(1 for m in self.modules.values() if m.is_used),
            unused_modules=len(unused_modules),
            unused_module_list=unused_modules,
            dependency_tree=dependency_tree,
            entry_points=entry_point_files,
            recommendations=recommendations
        )


def print_tree_format(result: AnalysisResult, analyzer: UnusedModuleAnalyzer) -> None:
    """Print results in tree format."""
    print("🌳 DEPENDENCY TREE ANALYSIS")
    print("=" * 50)
    
    # Calculate different categories of used modules
    package_structure_count = sum(1 for m in analyzer.modules.values() 
                                 if m.is_used and "PACKAGE_STRUCTURE" in m.imported_by)
    entry_point_count = sum(1 for m in analyzer.modules.values() 
                           if m.is_used and any("ENTRY_POINT:" in imp for imp in m.imported_by))
    heuristic_count = sum(1 for m in analyzer.modules.values() 
                         if m.is_used and "HEURISTIC_DETECTION" in m.imported_by)
    
    # Count different types of imports
    dynamic_count = sum(1 for m in analyzer.modules.values() 
                       if m.is_used and any("DYNAMIC" in imp or "FUNCTION_LEVEL" in imp or "CONDITIONAL" in imp 
                                          for imp in m.imported_by))
    
    dependency_count = result.used_modules - package_structure_count - entry_point_count - heuristic_count
    
    print(f"📊 Summary:")
    print(f"   • Total modules: {result.total_modules}")
    print(f"   • Used modules: {result.used_modules}")
    print(f"     - Package structure (__init__.py): {package_structure_count}")
    print(f"     - Entry point dependencies: {entry_point_count}")
    print(f"     - Import chain dependencies: {dependency_count}")
    print(f"     - Dynamic/conditional imports: {dynamic_count}")
    print(f"     - Heuristic detection (app/config/etc): {heuristic_count}")
    print(f"   • Unused modules: {result.unused_modules}")
    print(f"   • Entry points analyzed: {', '.join(result.entry_points)}")
    print()
    
    # Show some examples of dynamic imports found
    dynamic_examples = []
    for module_name, module_info in analyzer.modules.items():
        if module_info.is_used:
            for imported_by in module_info.imported_by:
                if any(keyword in imported_by for keyword in ["DYNAMIC", "FUNCTION_LEVEL", "CONDITIONAL"]):
                    dynamic_examples.append(f"{module_name} ← {imported_by}")
                    if len(dynamic_examples) >= 3:  # Show max 3 examples
                        break
            if len(dynamic_examples) >= 3:
                break
    
    if dynamic_examples:
        print("🔍 Enhanced Detection Examples:")
        for example in dynamic_examples:
            print(f"   • {example}")
        print()
    
    if result.unused_modules > 0:
        print("🗑️  POTENTIALLY UNUSED MODULES:")
        print("-" * 30)
        print("⚠️  These modules are not imported by your entry points, but verify before deleting!")
        print()
        for module_name in result.unused_module_list:
            module_info = analyzer.modules[module_name]
            print(f"   📄 {module_name}")
            print(f"      Path: {module_info.path.relative_to(analyzer.project_root)}")
            print(f"      Lines: {module_info.lines_of_code}")
            print()
    else:
        print("✅ NO UNUSED MODULES DETECTED!")
        print("   All modules are either imported by entry points or are package structure files.")
        print()
    
    print("💡 RECOMMENDATIONS:")
    print("-" * 20)
    for recommendation in result.recommendations:
        print(recommendation)


def print_json_format(result: AnalysisResult, analyzer: UnusedModuleAnalyzer) -> None:
    """Print results in JSON format."""
    output = {
        "summary": {
            "total_modules": result.total_modules,
            "used_modules": result.used_modules,
            "unused_modules": result.unused_modules,
            "entry_points": result.entry_points
        },
        "unused_modules": [
            {
                "name": module_name,
                "path": str(analyzer.modules[module_name].path.relative_to(analyzer.project_root)),
                "lines_of_code": analyzer.modules[module_name].lines_of_code
            }
            for module_name in result.unused_module_list
        ],
        "dependency_tree": result.dependency_tree,
        "recommendations": result.recommendations
    }
    
    print(json.dumps(output, indent=2))


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Analyze unused modules in Python project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/analyze_unused_modules.py
  python scripts/analyze_unused_modules.py --entry-points main.py run_webapp.py
  python scripts/analyze_unused_modules.py --format json --include-tests
  python scripts/analyze_unused_modules.py --src-dir src/skill_similarity_engine
        """
    )
    
    parser.add_argument(
        "--entry-points",
        nargs="+",
        default=["main.py", "run_webapp.py"],
        help="Entry point files to analyze (default: main.py run_webapp.py)"
    )
    
    parser.add_argument(
        "--src-dir",
        default="src",
        help="Source directory to analyze (default: src)"
    )
    
    parser.add_argument(
        "--format",
        choices=["tree", "json"],
        default="tree",
        help="Output format (default: tree)"
    )
    
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Include test modules in analysis"
    )
    
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root directory (default: current directory)"
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize analyzer
        analyzer = UnusedModuleAnalyzer(args.project_root, args.src_dir)
        
        # Perform analysis
        result = analyzer.analyze(args.entry_points, args.include_tests)
        
        # Output results
        if args.format == "json":
            print_json_format(result, analyzer)
        else:
            print_tree_format(result, analyzer)
        
        # Exit with error code if unused modules found
        return 1 if result.unused_modules > 0 else 0
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
