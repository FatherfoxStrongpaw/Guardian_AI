import os
import re
import shutil
import tempfile

def fix_file_imports(file_path):
    """Fix imports in a file to ensure proper dependencies."""
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Create a backup
        backup_path = f"{file_path}.bak"
        shutil.copy2(file_path, backup_path)
        
        # Track if any changes were made
        changes_made = False
        
        # Fix imports
        new_content = content
        
        # 1. Add comments for potentially problematic imports
        if 'from memory.memory_manager import' in new_content:
            new_content = new_content.replace(
                'from memory.memory_manager import',
                '# TODO: Consider using memory_manager.py in root directory instead\nfrom memory.memory_manager import'
            )
            changes_made = True
        
        if 'from sandbox_excecuter import' in new_content:
            new_content = new_content.replace(
                'from sandbox_excecuter import',
                '# TODO: Use sandbox_executor.py instead which has the integrated functionality\nfrom sandbox_executor import'
            )
            changes_made = True
        
        if 'from perpetual_agent_old import' in new_content:
            new_content = new_content.replace(
                'from perpetual_agent_old import',
                '# TODO: Use perpetual_llm.py instead which has the integrated functionality\nfrom perpetual_llm import'
            )
            changes_made = True
        
        if 'from verify_dependencies import' in new_content and not file_path.endswith('verify_dependencies.py'):
            new_content = new_content.replace(
                'from verify_dependencies import',
                '# TODO: Use tools.verify_dependencies instead for consistency\nfrom tools.verify_dependencies import'
            )
            changes_made = True
        
        # 2. Add import for reintegrated functionality if it's used but not imported
        
        # Check for variant simulation usage
        if ('simulate_variants' in new_content or 'priority_layers' in new_content or 'priority_weights' in new_content) and 'from perpetual_llm import' not in new_content and not file_path.endswith('perpetual_llm.py'):
            # Add import if not already present
            if 'import' in new_content:
                # Add after the last import
                import_pattern = re.compile(r'^(?:from\s+\S+\s+import\s+.*|import\s+\S+(?:\s+as\s+\S+)?)', re.MULTILINE)
                matches = list(import_pattern.finditer(new_content))
                if matches:
                    last_import = matches[-1]
                    last_import_end = last_import.end()
                    new_content = new_content[:last_import_end] + '\nfrom perpetual_llm import PerpetualLLM  # For variant simulation' + new_content[last_import_end:]
                    changes_made = True
            else:
                # Add at the beginning
                new_content = 'from perpetual_llm import PerpetualLLM  # For variant simulation\n\n' + new_content
                changes_made = True
        
        # Check for file monitoring usage
        if ('store_file_version' in new_content or 'check_file_integrity' in new_content) and 'from memory_manager import' not in new_content and not file_path.endswith('memory_manager.py'):
            # Add import if not already present
            if 'import' in new_content:
                # Add after the last import
                import_pattern = re.compile(r'^(?:from\s+\S+\s+import\s+.*|import\s+\S+(?:\s+as\s+\S+)?)', re.MULTILINE)
                matches = list(import_pattern.finditer(new_content))
                if matches:
                    last_import = matches[-1]
                    last_import_end = last_import.end()
                    new_content = new_content[:last_import_end] + '\nfrom memory_manager import MemoryManager  # For file monitoring' + new_content[last_import_end:]
                    changes_made = True
            else:
                # Add at the beginning
                new_content = 'from memory_manager import MemoryManager  # For file monitoring\n\n' + new_content
                changes_made = True
        
        # Check for code interpreter usage
        if ('CodeInterpreter' in new_content or 'interpreter_worker' in new_content) and 'from perpetual_llm import' not in new_content and not file_path.endswith('perpetual_llm.py'):
            # Add import if not already present
            if 'import' in new_content:
                # Add after the last import
                import_pattern = re.compile(r'^(?:from\s+\S+\s+import\s+.*|import\s+\S+(?:\s+as\s+\S+)?)', re.MULTILINE)
                matches = list(import_pattern.finditer(new_content))
                if matches:
                    last_import = matches[-1]
                    last_import_end = last_import.end()
                    new_content = new_content[:last_import_end] + '\nfrom perpetual_llm import CodeInterpreter  # For code interpretation' + new_content[last_import_end:]
                    changes_made = True
            else:
                # Add at the beginning
                new_content = 'from perpetual_llm import CodeInterpreter  # For code interpretation\n\n' + new_content
                changes_made = True
        
        # Write changes if any were made
        if changes_made:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✅ Fixed imports in {file_path}")
            return True
        else:
            # Remove backup if no changes were made
            os.remove(backup_path)
            print(f"ℹ️ No changes needed in {file_path}")
            return False
    
    except Exception as e:
        print(f"❌ Error fixing imports in {file_path}: {e}")
        # Restore from backup if available
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, file_path)
            os.remove(backup_path)
        return False

def main():
    # Files to check and fix
    files_to_fix = [
        "./main.py",
        "./perpetual_llm.py",
        "./rsi_module.py",
        "./monitoring/health_checker.py",
        "./tests/test_integration.py",
        "./tests_optional/test_security.py"
    ]
    
    print("\n=== FIXING DEPENDENCIES ===\n")
    
    fixed_count = 0
    for file_path in files_to_fix:
        if fix_file_imports(file_path):
            fixed_count += 1
    
    print(f"\nFixed imports in {fixed_count} files.")
    print("Backup files (.bak) were created for modified files.")
    print("Please review the changes and remove the backup files if satisfied.")

if __name__ == "__main__":
    main()
