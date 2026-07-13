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

## 架构设计 (流式转换架构)

本项目采用**全流式 (Streaming) 架构**设计，能够以常数级内存 $O(1)$（通常低于 20MB）转换数十 GB 的超大 SQL 备份文件，彻底解决 OOM 问题。

```
                       +----------------------+
输入 SQL 文件 --------> |     SQL Reader       | (流式读取与语句切分)
                       +----------------------+
                                  │
                                  ▼
                       +----------------------+
                       | Statement Classifier | (DDL/DML 分类器)
                       +----------------------+
                                  │
                  ┌───────────────┴───────────────┐
                  ▼                               ▼
            [DDL/COMMENT/INDEX]              [DML INSERT]
                  │                               │
                  ▼                               ▼
       +----------------------+        +----------------------+
       |   Pipeline 转换引擎  |        |   Pipeline 转换引擎  |
       +----------------------+        +----------------------+
                  │                               │
                  ▼                               ▼
       +----------------------+        +----------------------+
       |      Schema AST      |        |      磁盘临时缓存    |
       | (仅在内存构建轻量结构) |        |  (按表分流存储数据)  |
       +----------------------+        +----------------------+
                  │                               │
                  ▼ (拓扑依赖排序)                │ (流式读取/解析/转换)
         [排序后的 DDL 输出]                       │
                  │                               │
                  └───────────────┬───────────────┘
                                  ▼
                       +----------------------+
                       |     SQL Writer       | (流式拼接并写入目标文件)
                       +----------------------+
```

### 1. 流式分流与轻量 Schema 排序
- **DDL/DML 分流**：输入文件通过 `SQLReader` 逐语句读入。`Statement Classifier` 判断语句类型。所有的 DDL、COMMENT、INDEX 均加载到内存并构建轻量级的 `Schema AST` 图；占体积 99% 的 DML `INSERT` 数据则直接分流追加写入到本地磁盘的临时缓存中，不占用物理内存。
- **拓扑排序**：仅对内存中的轻量级 `TableBlock`（DDL 结构）根据外键依赖关系进行拓扑排序，确定最终的安全输出顺序。

### 2. 流式 DML 翻译与写入 (DML Streaming Engine)
- 在写入目标 SQL 时，按照拓扑排序好的表顺序，依次流式写入对应的 DDL 语句。
- 随后，流式读取并解析该表对应的磁盘 DML 缓存文件，通过 `iter_insert_rows`（基于 Generator 的 VALUES 行解析器）实时完成类型映射与方言转换，并以 1000 行为批次立即 flush 到最终目标文件中。

---

## 模块结构

- `reader/`:
  - `sql_reader.py`：基于状态机的流式 SQL 读取器，支持各种注释过滤、自定义 DELIMITER 与 PostgreSQL Dollar Quote。
  - `classifier.py`：对语句类型进行判别分类。
- `writer/`:
  - `sql_writer.py`：带输出缓冲区的高效流式 SQL 写入器。
- `parser/`:
  - `insert_stream.py`：以生成器 (Generator) 逐行流式拆解 `INSERT VALUES`，极具内存优势。
- `model/`：Schema AST 实体模型，包括 `Schema`, `TableBlock`, `ColumnDef`, `ForeignKeyDef`, `IndexDef`。
- `converter/`：Pipeline 转换规则引擎和数据库 Dialect 的注册与实现。

---

## 支持的语言

| 方言 | 别名 | 支持方向 |
|---|---|---|
| MySQL | `mysql` | 源 + 目标 |
| Oracle | `oracle` | 源 |
| PostgreSQL | `pgsql`、`postgresql`、`postgres` | 源 + 目标 |
| KingbaseES | `kingbase` | 源 + 目标 |
| SQLite | `sqlite`、`sqlite3` | 源 + 目标 |

---

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

规则文件与 Pipeline 框架均无需修改。
