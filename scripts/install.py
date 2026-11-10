"""Compatibility entry point; the installer lives in telegram_dev_install.py."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telegram_dev_install import main  # noqa: E402

if __name__ == '__main__':
    main()
