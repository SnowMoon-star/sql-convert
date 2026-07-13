"""SQL 流式写入器 — 高效地将转换后的 SQL 写入目标文件。"""
from __future__ import annotations
from pathlib import Path

class SQLWriter:
    """流式 SQL 语句写入器。"""

    def __init__(self, file_path: str | Path, encoding: str = "utf-8", append: bool = False):
        self.file_path = Path(file_path)
        self.encoding = encoding
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if append else "w"
        self.file = open(self.file_path, mode, encoding=self.encoding)

    def write(self, statement: str) -> None:
        """流式写入单条语句。"""
        self.file.write(statement)
        if not statement.endswith("\n"):
            self.file.write("\n")

    def flush(self) -> None:
        """刷新缓存区。"""
        self.file.flush()

    def close(self) -> None:
        """关闭文件。"""
        if not self.file.closed:
            self.file.close()

    def __enter__(self) -> SQLWriter:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
