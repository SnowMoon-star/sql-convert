"""Kahn 算法对外键表进行拓扑排序。"""
from __future__ import annotations
from collections import deque
from model import TableBlock


def _topological_sort(deps: dict[str, list[str]]) -> list[str]:
    """Kahn 拓扑排序：deps[name] = [该表所依赖的其他表]。

    返回表名列表，无依赖者在前。循环依赖或外部引用时保持原顺序。
    使用 deque.popleft() 代替 list.pop(0)，将队列操作从 O(n) 降为 O(1)。
    """
    # 入度
    in_degree: dict[str, int] = {name: 0 for name in deps}
    dependents: dict[str, list[str]] = {name: [] for name in deps}

    for name, refs in deps.items():
        for ref in refs:
            if ref in deps:
                dependents.setdefault(ref, [])
                dependents[ref].append(name)
                in_degree[name] += 1

    # 入度为 0 的入队（deque 保证 popleft 为 O(1)）
    queue: deque[str] = deque(n for n, d in in_degree.items() if d == 0)
    result: list[str] = []

    while queue:
        name = queue.popleft()
        result.append(name)
        for dependent in dependents.get(name, []):
            if dependent in in_degree:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

    # 循环依赖或外部引用：保持原顺序追加
    for name in deps:
        if name not in result:
            result.append(name)

    return result


def sort_tables_by_fk(tables: list[TableBlock]) -> list[TableBlock]:
    """按 FK 依赖排序表，只考虑当前 SQL 中存在的表间依赖。

    - 全部无外键 → 保持原始顺序
    - FK 引用外部表（不在当前 SQL 中）→ 视为已满足的依赖，忽略
    - FK 引用内部表 → 被引用表先输出
    - 循环依赖 → 降级保持原顺序
    """
    if not tables:
        return tables

    known_names = {t.name.lower() for t in tables}

    # 构建 deps：只计算引用目标在已知表集合中的 FK
    deps: dict[str, list[str]] = {}
    for t in tables:
        refs: list[str] = []
        for fk in t.foreign_keys:
            if fk.ref_table.lower() in known_names:
                refs.append(fk.ref_table.lower())
        deps[t.name.lower()] = list(set(refs))

    # 无内部依赖 → 保持原顺序
    if not any(deps.values()):
        return tables

    sorted_names = _topological_sort(deps)
    name_to_table = {t.name.lower(): t for t in tables}
    return [name_to_table[n] for n in sorted_names if n in name_to_table]
