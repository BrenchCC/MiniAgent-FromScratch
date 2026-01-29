import os
import sys

sys.path.append(os.getcwd())
from miniagent.cli import main


if __name__ == "__main__":
    raise SystemExit(main())