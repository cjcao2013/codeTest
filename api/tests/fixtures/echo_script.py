# A mock subprocess script for tests
import sys
print("line one")
print("line two")
print("line three")
sys.exit(int(sys.argv[1]) if len(sys.argv) > 1 else 0)
