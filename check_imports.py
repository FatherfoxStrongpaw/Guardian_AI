import importlib
import os
import sys
import traceback

def check_module_imports(module_path):
    """Check if a module can be imported and report any issues."""
    # Convert file path to module name
    if module_path.endswith('.py'):
        module_path = module_path[:-3]  # Remove .py extension
    
    # Convert path to module name
    module_name = module_path.replace('/', '.').replace('\\', '.')
    if module_name.startswith('./'):
        module_name = module_name[2:]
    if module_name.startswith('.'):
        module_name = module_name[1:]
    
    # Skip __pycache__ and similar
    if '__' in module_name:
        return None
    
    # Skip test files for now
    if module_name.startswith('test') or 'test_' in module_name:
        return None
    
    try:
        # Try to import the module
        module = importlib.import_module(module_name)
        return (module_name, True, None)
    except Exception as e:
        # Return the error
        return (module_name, False, str(e))

def main():
    results = []
    
    # Get all Python files
    for root, _, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                module_path = os.path.join(root, file)
                result = check_module_imports(module_path)
                if result:
                    results.append(result)
    
    # Print results
    print("\n=== IMPORT CHECK RESULTS ===\n")
    
    # First print failures
    failures = [r for r in results if not r[1]]
    if failures:
        print("IMPORT FAILURES:")
        for module_name, _, error in failures:
            print(f"  ❌ {module_name}: {error}")
    else:
        print("✅ All modules import successfully!")
    
    # Print successes
    successes = [r for r in results if r[1]]
    print(f"\nSUCCESSFUL IMPORTS ({len(successes)}):")
    for module_name, _, _ in successes:
        print(f"  ✅ {module_name}")
    
    # Summary
    print(f"\nSUMMARY: {len(successes)} successful, {len(failures)} failed")

if __name__ == "__main__":
    main()
