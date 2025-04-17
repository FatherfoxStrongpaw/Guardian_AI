import os
import re

def check_file_imports(file_path):
    """Check specific imports in a file for potential issues."""
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Check for imports that might be problematic
            
            # 1. Check for imports from memory_manager vs memory.memory_manager
            if 'from memory_manager import' in content and not file_path.endswith('memory_manager.py'):
                # Check if memory/memory_manager.py exists
                if os.path.exists('./memory/memory_manager.py'):
                    issues.append("Imports from memory_manager but memory/memory_manager.py also exists")
            
            # 2. Check for imports from sandbox_executor vs sandbox_excecuter
            if 'from sandbox_executor import' in content and not file_path.endswith('sandbox_executor.py'):
                # Check if sandbox_excecuter.py exists
                if os.path.exists('./sandbox_excecuter.py'):
                    issues.append("Imports from sandbox_executor but sandbox_excecuter.py also exists")
            
            # 3. Check for imports from perpetual_llm vs perpetual_agent_old
            if 'from perpetual_llm import' in content and not file_path.endswith('perpetual_llm.py'):
                # Check if perpetual_agent_old.py exists
                if os.path.exists('./perpetual_agent_old.py'):
                    issues.append("Imports from perpetual_llm but perpetual_agent_old.py also exists")
            
            # 4. Check for verify_dependencies vs tools/verify_dependencies
            if 'from verify_dependencies import' in content and not file_path.endswith('verify_dependencies.py'):
                # Check if tools/verify_dependencies.py exists
                if os.path.exists('./tools/verify_dependencies.py'):
                    issues.append("Imports from verify_dependencies but tools/verify_dependencies.py also exists")
            
            # 5. Check for code_interpreter imports
            if 'from code_interpreter import' in content and not file_path.endswith('code_interpreter.py'):
                issues.append("Imports from code_interpreter which was recently reintegrated")
            
            # 6. Check for command_processor imports
            if 'from command_processor import' in content and not file_path.endswith('command_processor.py'):
                issues.append("Imports from command_processor which was recently reintegrated")
            
    except Exception as e:
        issues.append(f"Error reading file: {e}")
    
    return issues

def main():
    # Find all Python files
    python_files = []
    for root, _, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    # Check each file for specific import issues
    files_with_issues = {}
    
    for file_path in python_files:
        issues = check_file_imports(file_path)
        if issues:
            files_with_issues[file_path] = issues
    
    # Print results
    print("\n=== SPECIFIC IMPORT ISSUES ===\n")
    
    if files_with_issues:
        print("FILES WITH POTENTIAL IMPORT ISSUES:")
        for file_path, issues in files_with_issues.items():
            print(f"\n  📄 {file_path}")
            for issue in issues:
                print(f"    ⚠️ {issue}")
    else:
        print("✅ No specific import issues detected!")
    
    # Now check for missing imports of the reintegrated functionality
    print("\n=== CHECKING FOR MISSING REINTEGRATED FUNCTIONALITY ===\n")
    
    # Key functionality that was reintegrated
    reintegrated_features = {
        "variant_simulation": ["simulate_variants", "variant_performance", "priority_layers", "priority_weights"],
        "file_monitoring": ["store_file_version", "get_file_versions", "restore_file_version", "register_monitored_file", "check_monitored_files", "check_file_integrity", "add_changelog_entry", "get_changelog"],
        "code_interpreter": ["CodeInterpreter", "interpreter_worker", "SAFE_BUILTINS", "handle_code_interpretation"],
        "enhanced_security": ["SandboxSecurityError", "sandbox_worker", "validate_code", "cpu_quota", "network_disabled", "readonly_filesystem"]
    }
    
    # Check if these features are used in the codebase
    feature_usage = {feature: [] for feature in reintegrated_features}
    
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                for feature, keywords in reintegrated_features.items():
                    for keyword in keywords:
                        if keyword in content:
                            if file_path not in feature_usage[feature]:
                                feature_usage[feature].append(file_path)
        except Exception:
            pass
    
    # Print results
    print("USAGE OF REINTEGRATED FUNCTIONALITY:")
    
    for feature, files in feature_usage.items():
        print(f"\n  🔍 {feature.replace('_', ' ').title()}:")
        if files:
            for file in files:
                print(f"    ✅ Used in: {file}")
        else:
            print(f"    ⚠️ Not used in any file")

if __name__ == "__main__":
    main()
