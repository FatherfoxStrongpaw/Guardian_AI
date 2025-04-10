import sys
print(sys.path)
try:
    import yaml
    print("YAML version:", yaml.__version__)
except ImportError as e:
    print("Import error:", e)