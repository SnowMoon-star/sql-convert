# sql_convert

多方言 SQL 转换器。支持 MySQL、Oracle、PostgreSQL、Kingbase、SQLite 之间的双向转换。

基于 Dialect + Capability + Rule Engine 架构，新增数据库仅需声明方言能力，无需修改规则。

## 环境要求

- Python 3.10+

## 用法

```bash
python convert.py <input.sql> --source-mode <SOURCE> --target-mode <TARGET>
                   [-o OUTPUT] [--encoding ENC] [--overwrite] [-v]
                   [--database DB]
```

| 参数 | 默认值 | 说明 |
|---|---|---|
| `input` | 必填 | 待转换的 `.sql` 文件路径 |
| `--source-mode` | 必填 | 源数据库类型：`mysql`、`oracle`、`kingbase`、`pgsql`、`sqlite` |
| `--target-mode` | 必填 | 目标数据库类型：`mysql`、`kingbase`、`pgsql`、`sqlite` |
| `-o, --output` | `<input>_<target>_<时间戳>.<扩展>` | 输出文件路径 |
| `--encoding` | `utf-8` | 读写文件编码 |
| `--overwrite` | 关 | 输出文件已存在时是否覆盖 |
| `-v, --verbose` | 关 | 打印每条规则命中次数 |
| `--database` | 无 | 数据库名，用于输出中表标识符的前缀 |

### 示例

```bash
# MySQL → Kingbase
python convert.py dump.sql --source-mode mysql --target-mode kingbase

# MySQL → PostgreSQL
python convert.py dump.sql --source-mode mysql --target-mode pgsql

# MySQL → SQLite（直接生成 .db 文件）
python convert.py dump.sql --source-mode mysql --target-mode sqlite

# Oracle → PostgreSQL
python convert.py dump.sql --source-mode oracle --target-mode pgsql

# Kingbase → MySQL（反向转换）
python convert.py kingbase_output.sql --source-mode kingbase --target-mode mysql

# 指定输出并查看规则命中
python convert.py dump.sql --source-mode mysql --target-mode kingbase -o out.sql -v

# GBK 编码
python convert.py dump.sql --source-mode mysql --target-mode kingbase --encoding gbk
```

### 退出码

- `0`：成功
- `2`：使用错误
- `3`：运行时错误

## 输出格式

转换输出为 5 步骤结构化 SQL：

1. 删除旧表（`DROP TABLE IF EXISTS ...`）
2. 表结构（`CREATE TABLE ...`）
3. 索引（`CREATE INDEX ...`）
4. 外键（`ALTER TABLE ADD CONSTRAINT ...`）
5. 数据导入（`INSERT INTO ... VALUES ...`）

输出按外键依赖拓扑排序，确保导入顺序正确。

## 架构

```
Dialect（方言自我描述）
  └─ Capability（能力标签）
       └─ Rule Engine（正则规则 + Pipeline）
            └─ Canonical Mapping（类型 + 函数映射）
```

- **Dialect**：每个数据库声明自身能力（`capabilities`），不关心其他数据库
- **Rule**：源有某能力、目标无 → 自动执行规则，无需为每个目标重复编写
- **Pipeline**：规则按 6 个阶段顺序执行，避免冲突
- **Canonical Mapping**：类型和函数通过中间规范层转发（`Source Type → Canonical → Target Type`）

## 支持的语言

| 方言 | 别名 | 支持方向 |
|---|---|---|
| MySQL | `mysql` | 源 + 目标 |
| Oracle | `oracle` | 源 |
| PostgreSQL | `pgsql`、`postgresql`、`postgres` | 源 + 目标 |
| KingbaseES | `kingbase` | 源 + 目标 |
| SQLite | `sqlite`、`sqlite3` | 源 + 目标 |

## 新增方言

在 `converter/dialects/` 下新建文件，继承 `BaseDialect`，声明 `family`、`capabilities`、映射表：

```python
@register
class NewDialect(BaseDialect):
    family = "pg"
    identifier_quote = '"'
    capabilities = {CAP_CASCADE, ...}
    canonical_to_type = {"Integer32": "INTEGER", ...}
    canonical_to_function = {"Coalesce": "COALESCE", ...}
```

规则文件无需修改。
