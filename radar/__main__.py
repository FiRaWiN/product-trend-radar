"""Enable `python -m radar` execution."""

from .cli import main
import sys

sys.exit(main())
