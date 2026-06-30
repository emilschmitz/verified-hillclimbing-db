import sys
import os

# Ensure the root directory and research_loop are in the search path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from research_loop.ssb_workload import queries, schema
