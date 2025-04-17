import os
import re
import sys

def extract_imports(file_path):
    """Extract all import statements from a Python file."""
    imports = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Find all import statements
            import_pattern = re.compile(r'^(?:from\s+(\S+)\s+import\s+.*|import\s+(\S+)(?:\s+as\s+\S+)?)', re.MULTILINE)
            for match in import_pattern.finditer(content):
                from_import, direct_import = match.groups()
                if from_import:
                    # Handle 'from X import Y'
                    imports.append(from_import)
                if direct_import:
                    # Handle 'import X'
                    # Split for cases like 'import os, sys'
                    for module in direct_import.split(','):
                        imports.append(module.strip())
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return imports

def find_all_python_files():
    """Find all Python files in the current directory and subdirectories."""
    python_files = []
    for root, _, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

def check_file_exists(import_path):
    """Check if a file corresponding to an import path exists."""
    # Convert import path to file path
    file_path = import_path.replace('.', os.sep) + '.py'
    
    # Check if the file exists directly
    if os.path.exists(file_path):
        return True
    
    # Check if it exists as a relative path
    if os.path.exists(os.path.join('.', file_path)):
        return True
    
    # Check if it's a directory with __init__.py
    dir_path = import_path.replace('.', os.sep)
    if os.path.isdir(dir_path) and os.path.exists(os.path.join(dir_path, '__init__.py')):
        return True
    
    # Check if it's a directory with __init__.py (relative)
    if os.path.isdir(os.path.join('.', dir_path)) and os.path.exists(os.path.join('.', dir_path, '__init__.py')):
        return True
    
    return False

def is_standard_library(module_name):
    """Check if a module is part of the Python standard library."""
    standard_libs = [
        'abc', 'argparse', 'ast', 'asyncio', 'base64', 'collections', 'contextlib', 
        'copy', 'csv', 'datetime', 'enum', 'functools', 'glob', 'hashlib', 'io', 
        'itertools', 'json', 'logging', 'math', 'multiprocessing', 'os', 'pathlib', 
        're', 'random', 'sched', 'shutil', 'signal', 'socket', 'sqlite3', 'string', 
        'subprocess', 'sys', 'tempfile', 'threading', 'time', 'traceback', 'types', 
        'typing', 'unittest', 'urllib', 'uuid', 'warnings', 'xml', 'zipfile'
    ]
    
    # Check if the module or its top-level package is in the standard library
    module_parts = module_name.split('.')
    return module_parts[0] in standard_libs

def is_third_party_library(module_name):
    """Check if a module is likely a third-party library."""
    third_party_libs = [
        'docker', 'mysql', 'prometheus_client', 'psutil', 'requests', 'yaml'
    ]
    
    # Check if the module or its top-level package is a known third-party library
    module_parts = module_name.split('.')
    return module_parts[0] in third_party_libs

def main():
    python_files = find_all_python_files()
    
    # Dictionary to store all imports for each file
    file_imports = {}
    
    # Extract imports from all files
    for file_path in python_files:
        imports = extract_imports(file_path)
        file_imports[file_path] = imports
    
    # Check for missing dependencies
    missing_dependencies = {}
    
    for file_path, imports in file_imports.items():
        missing = []
        
        for import_name in imports:
            # Skip standard library and third-party imports
            if is_standard_library(import_name) or is_third_party_library(import_name):
                continue
            
            # Skip relative imports (starting with .)
            if import_name.startswith('.'):
                continue
            
            # Check if the import exists as a file
            if not check_file_exists(import_name):
                missing.append(import_name)
        
        if missing:
            missing_dependencies[file_path] = missing
    
    # Print results
    print("\n=== DEPENDENCY CHECK RESULTS ===\n")
    
    if missing_dependencies:
        print("FILES WITH MISSING DEPENDENCIES:")
        for file_path, missing in missing_dependencies.items():
            print(f"\n  📄 {file_path}")
            for dep in missing:
                print(f"    ❌ Missing: {dep}")
    else:
        print("✅ All dependencies are satisfied!")
    
    # Check for circular imports
    print("\n=== CHECKING FOR CIRCULAR DEPENDENCIES ===\n")
    
    # Build dependency graph
    dependency_graph = {}
    for file_path, imports in file_imports.items():
        # Normalize file path for graph
        normalized_path = file_path
        if normalized_path.startswith('./'):
            normalized_path = normalized_path[2:]
        
        dependency_graph[normalized_path] = []
        
        for import_name in imports:
            # Skip standard library and third-party imports
            if is_standard_library(import_name) or is_third_party_library(import_name):
                continue
            
            # Skip relative imports for simplicity
            if import_name.startswith('.'):
                continue
            
            # Convert import to file path
            import_file = import_name.replace('.', os.sep) + '.py'
            
            # Add to graph if the file exists
            if os.path.exists(import_file) or os.path.exists(os.path.join('.', import_file)):
                if os.path.exists(import_file):
                    dependency_graph[normalized_path].append(import_file)
                else:
                    dependency_graph[normalized_path].append(os.path.join('.', import_file))
    
    # Function to detect cycles in the graph
    def find_cycles(graph):
        cycles = []
        visited = set()
        path = []
        
        def dfs(node):
            if node in path:
                cycle = path[path.index(node):]
                cycle.append(node)  # Complete the cycle
                cycles.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, []):
                dfs(neighbor)
            
            path.pop()
        
        for node in graph:
            dfs(node)
        
        return cycles
    
    cycles = find_cycles(dependency_graph)
    
    if cycles:
        print("CIRCULAR DEPENDENCIES DETECTED:")
        for i, cycle in enumerate(cycles, 1):
            print(f"\n  ⭕ Cycle {i}:")
            for node in cycle:
                print(f"    → {node}")
    else:
        print("✅ No circular dependencies detected!")
    
    # Print summary of all dependencies
    print("\n=== DEPENDENCY SUMMARY ===\n")
    
    # Count dependencies by type
    std_lib_count = 0
    third_party_count = 0
    project_count = 0
    
    for file_path, imports in file_imports.items():
        for import_name in imports:
            if is_standard_library(import_name):
                std_lib_count += 1
            elif is_third_party_library(import_name):
                third_party_count += 1
            else:
                project_count += 1
    
    print(f"Total Python files: {len(python_files)}")
    print(f"Standard library imports: {std_lib_count}")
    print(f"Third-party library imports: {third_party_count}")
    print(f"Project-specific imports: {project_count}")
    
    # Check for duplicate functionality
    print("\n=== CHECKING FOR POTENTIAL DUPLICATE FUNCTIONALITY ===\n")
    
    # Files with similar names might indicate duplication
    similar_files = []
    file_names = [os.path.basename(f) for f in python_files]
    
    for i, name1 in enumerate(file_names):
        for j, name2 in enumerate(file_names):
            if i != j and name1.replace('_', '') == name2.replace('_', ''):
                similar_files.append((python_files[i], python_files[j]))
    
    if similar_files:
        print("POTENTIALLY SIMILAR FILES:")
        for file1, file2 in similar_files:
            print(f"  ⚠️ {file1} and {file2}")
    else:
        print("✅ No obviously similar files detected!")

if __name__ == "__main__":
    main()
