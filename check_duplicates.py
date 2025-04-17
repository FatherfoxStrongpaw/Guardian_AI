import os
import difflib

def compare_files(file1, file2):
    """Compare two files and return their similarity ratio."""
    try:
        with open(file1, 'r', encoding='utf-8') as f1, open(file2, 'r', encoding='utf-8') as f2:
            content1 = f1.read()
            content2 = f2.read()
            
            # Calculate similarity ratio
            similarity = difflib.SequenceMatcher(None, content1, content2).ratio()
            
            # Get unique functions in each file
            functions1 = extract_functions(content1)
            functions2 = extract_functions(content2)
            
            unique_to_file1 = [f for f in functions1 if f not in functions2]
            unique_to_file2 = [f for f in functions2 if f not in functions1]
            
            return {
                "similarity": similarity,
                "unique_to_file1": unique_to_file1,
                "unique_to_file2": unique_to_file2
            }
    except Exception as e:
        return {
            "error": str(e),
            "similarity": 0,
            "unique_to_file1": [],
            "unique_to_file2": []
        }

def extract_functions(content):
    """Extract function names from Python code."""
    import re
    
    # Pattern to match function definitions
    pattern = r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
    
    # Find all matches
    matches = re.findall(pattern, content)
    
    return matches

def main():
    # Pairs of files to compare
    file_pairs = [
        ("./memory_manager.py", "./memory/memory_manager.py"),
        ("./test_rsi_module.py", "./tests/test_rsi_module.py"),
        ("./verify_dependencies.py", "./tools/verify_dependencies.py"),
        ("./sandbox_executor.py", "./sandbox_excecuter.py")
    ]
    
    print("\n=== DUPLICATE FILE ANALYSIS ===\n")
    
    for file1, file2 in file_pairs:
        if os.path.exists(file1) and os.path.exists(file2):
            print(f"Comparing {file1} and {file2}:")
            
            result = compare_files(file1, file2)
            
            if "error" in result:
                print(f"  ❌ Error: {result['error']}")
                continue
            
            similarity = result["similarity"] * 100
            print(f"  📊 Similarity: {similarity:.2f}%")
            
            if similarity > 90:
                print("  ⚠️ These files are very similar and might be duplicates!")
            elif similarity > 70:
                print("  ⚠️ These files have significant overlap!")
            else:
                print("  ✅ These files are sufficiently different.")
            
            if result["unique_to_file1"]:
                print(f"\n  Functions unique to {file1}:")
                for func in result["unique_to_file1"]:
                    print(f"    - {func}")
            
            if result["unique_to_file2"]:
                print(f"\n  Functions unique to {file2}:")
                for func in result["unique_to_file2"]:
                    print(f"    - {func}")
            
            print("\n" + "-" * 80 + "\n")
        else:
            if not os.path.exists(file1):
                print(f"❌ File not found: {file1}")
            if not os.path.exists(file2):
                print(f"❌ File not found: {file2}")

if __name__ == "__main__":
    main()
