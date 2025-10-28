from pathlib import Path
from typing import List

def tail_lines(path: Path, n: int = 200) -> List[str]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        lines = f.readlines()
    return lines[-n:]
