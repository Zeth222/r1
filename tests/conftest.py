import os
import sys

os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
