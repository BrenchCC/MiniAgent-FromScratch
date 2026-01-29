import os
import sys

sys.path.append(os.getcwd())
from quarkagent.cli import main


if __name__ == "__main__":
    raise SystemExit(main())