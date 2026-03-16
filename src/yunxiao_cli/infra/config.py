from __future__ import annotations

import os
from pathlib import Path


class CliConfig:
    @classmethod
    def data_root(cls) -> Path:
        root = os.environ.get("YUNXIAO_CLI_HOME")
        if root:
            return Path(root)
        return Path.home() / ".yunxiao"
