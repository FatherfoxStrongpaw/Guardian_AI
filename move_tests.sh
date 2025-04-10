# Create new directory
mkdir -p tests_optional

# Move optional test files
mv tests/test_circular_deps.py tests_optional/
mv tests/test_dependencies.py tests_optional/
mv tests/test_security.py tests_optional/
mv tests/test_consolidated_code_analysis.py tests_optional/
mv tests/test_hitl_interface.py tests_optional/