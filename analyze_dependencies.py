import os
import sys
import ast
import importlib
import logging
from typing import Dict, List, Set, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger("DependencyAnalyzer")

class ImportVisitor(ast.NodeVisitor):
    """AST visitor to extract imports from Python files"""
    def __init__(self):
        self.imports = set()
        self.from_imports = {}
        
    def visit_Import(self, node):
        for name in node.names:
            self.imports.add(name.name)
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node):
        if node.module is not None:
            module = node.module
            if module not in self.from_imports:
                self.from_imports[module] = set()
            for name in node.names:
                self.from_imports[module].add(name.name)
        self.generic_visit(node)

def extract_imports(file_path: str) -> Tuple[Set[str], Dict[str, Set[str]]]:
    """Extract imports from a Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        visitor = ImportVisitor()
        visitor.visit(tree)
        
        return visitor.imports, visitor.from_imports
    except Exception as e:
        logger.error(f"Error extracting imports from {file_path}: {e}")
        return set(), {}

def analyze_dependencies(files: List[str]) -> Dict[str, Dict]:
    """Analyze dependencies between files"""
    dependency_map = {}
    
    for file in files:
        module_name = os.path.splitext(os.path.basename(file))[0]
        imports, from_imports = extract_imports(file)
        
        # Filter to only include local modules
        local_imports = set()
        for imp in imports:
            if any(os.path.exists(f"{imp}.py") for imp in [imp, imp.split('.')[0]]):
                local_imports.add(imp)
        
        local_from_imports = {}
        for module, names in from_imports.items():
            if any(os.path.exists(f"{mod}.py") for mod in [module, module.split('.')[0]]):
                local_from_imports[module] = names
        
        dependency_map[module_name] = {
            "direct_imports": local_imports,
            "from_imports": local_from_imports,
            "all_dependencies": local_imports.union(local_from_imports.keys())
        }
    
    return dependency_map

def check_circular_dependencies(dependency_map: Dict[str, Dict]) -> List[str]:
    """Check for circular dependencies"""
    circular_deps = []
    
    def dfs(module: str, visited: List[str]):
        if module in visited:
            circular_deps.append(" -> ".join(visited + [module]))
            return
        
        new_visited = visited + [module]
        if module in dependency_map:
            for dep in dependency_map[module]["all_dependencies"]:
                dfs(dep, new_visited)
    
    for module in dependency_map:
        dfs(module, [])
    
    return circular_deps

def main():
    """Main function"""
    # Add current directory to Python path
    sys.path.insert(0, os.getcwd())
    
    # Critical files to analyze
    critical_files = [
        "perpetual_llm.py",
        "rsi_module.py",
        "sandbox_executor.py",
        "hitl_interface.py",
        "ollama_agent.py",
        "self_diagnostic.py",
        "memory_manager.py"
    ]
    
    # Verify files exist
    existing_files = []
    for file in critical_files:
        if os.path.exists(file):
            existing_files.append(file)
        else:
            logger.warning(f"File not found: {file}")
    
    # Analyze dependencies
    logger.info("Analyzing dependencies...")
    dependency_map = analyze_dependencies(existing_files)
    
    # Print dependency map
    logger.info("\nDependency Map:")
    for module, deps in dependency_map.items():
        logger.info(f"\n{module}:")
        if deps["direct_imports"]:
            logger.info("  Direct imports:")
            for imp in sorted(deps["direct_imports"]):
                logger.info(f"    - {imp}")
        
        if deps["from_imports"]:
            logger.info("  From imports:")
            for module_name, names in sorted(deps["from_imports"].items()):
                logger.info(f"    - {module_name}: {', '.join(sorted(names))}")
    
    # Check for circular dependencies
    circular_deps = check_circular_dependencies(dependency_map)
    if circular_deps:
        logger.warning("\nCircular Dependencies Detected:")
        for dep in circular_deps:
            logger.warning(f"  {dep}")
    else:
        logger.info("\nNo circular dependencies detected.")

if __name__ == "__main__":
    main()
