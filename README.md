# sql_convert

多方言 SQL 转换器。支持 MySQL、Oracle、PostgreSQL、Kingbase、SQLite、SQLServer 之间的双向/流式转换。

基于 Dialect + Capability + Rule Engine 架构，新增数据库仅需声明方言能力，无需修改规则。

## 最新特性 (2.0 核心演进)

* **R1：错误诊断与日志体系** — 在语句流中跟踪物理行号与偏移量，集成异常分类继承树，支持 `--continue-on-error` 出错跳过与 `--debug`/`--trace` 多级控制台日志。
* **R2：E2E 集成测试** — 引入 Golden File 集成测试套件与比对，支持过滤空格、换行符及注释。新增 SQLServer 方言基座支持。
* **R3：MySQL 条件注释处理** — 自动处理 `/*!40101 ... */`，MySQL 目标库下原样保留，其它目标库下提取内部真实语句并优雅映射（例如 `SET NAMES` 转为 `SET client_encoding`），过滤无效变量。
* **R4：基于 Lexer + AST 的 DDL 解析引擎** — 引入带行列定位的 SQL 词法分析器，DDL 解析彻底摒弃易错正则，改由基于 Token 流的手写下降分析器状态机驱动，解析精度和健壮性大幅跃升。
* **R5：可视化转换报告** — 转换后自动在同级生成同名精确时间戳的 **HTML（交互式自适应暗色网页）** 报告，统计规则命中、警告及失败项。
* **R6：兼容性 Feature Matrix** — 引入功能兼容性大表，对分区表、函数索引、触发器、序列、物化视图等高级功能进行检索并在发现不支持时主动警告。

---

## 环境要求

- Python 3.10+

## 用法

```bash
python main.py <input.sql> --source-mode <SOURCE> --target-mode <TARGET>
                 [-o OUTPUT] [--encoding ENC] [--overwrite] [-v]
                 [--database DB] [--continue-on-error] [--debug] [--trace]
```

| 参数 | 默认值 | 说明 |
|---|---|---|
| `input` | 必填 | 待转换的 `.sql` 文件路径 |
| `--source-mode` | 选填（支持自动嗅探） | 源数据库类型：`mysql`、`oracle`、`kingbase`、`pgsql`、`sqlite`、`sqlserver` |
| `--target-mode` | 必填 | 目标数据库类型：`mysql`、`kingbase`、`pgsql`、`sqlite`、`oracle` |
| `-o, --output` | `<input>_<target>_<时间戳>.<扩展>` | 输出文件路径 |
| `--encoding` | `utf-8` | 读写文件编码 |
| `--overwrite` | 关 | 输出文件已存在时是否覆盖 |
| `-v, --verbose` | 关 | 打印每条规则命中次数，且日志级别设为 INFO |
| `--database` | 无 | 数据库名，用于输出中表标识符的前缀 |
| `--continue-on-error` | 关 | 遇到转换/解析失败时跳过并继续，不崩溃退出 |
| `--debug` | 关 | 开启调试级别日志输出 |
| `--trace` | 关 | 开启极详尽的跟踪日志输出 |

### 示例

```bash
# MySQL → Kingbase (自动识别源)
python main.py dump.sql --target-mode kingbase

# MySQL → PostgreSQL (出错继续)
python main.py dump.sql --target-mode pgsql --continue-on-error

# MySQL → SQLite（直接生成 .db 文件）
python main.py dump.sql --target-mode sqlite

# Oracle → PostgreSQL (开启调试日志)
python main.py dump.sql --source-mode oracle --target-mode pgsql --debug

# SQLServer → PostgreSQL
python main.py dump.sql --source-mode sqlserver --target-mode pgsql
```

### 退出码

- `0`：成功
- `2`：使用错误
- `3`：运行时错误

---

## 输出格式

转换输出为 5 步骤结构化 SQL：

1. 删除旧表（`DROP TABLE IF EXISTS ...`）
2. 表结构（`CREATE TABLE ...`）
3. 索引（`CREATE INDEX ...`）
4. 外键（`ALTER TABLE ADD CONSTRAINT ...`）
5. 数据导入（`INSERT INTO ... VALUES ...`）

输出按外键依赖拓扑排序，确保导入顺序正确。在输出中亦会保留全局会话环境声明语句（如 `SET client_encoding`）并在文件头部优先输出。

---

## 架构设计 (流式转换与 Token 解析架构)

本项目采用**全流式 (Streaming) 架构**设计，能够以常数级内存 $O(1)$（通常低于 20MB）转换数十 GB 的超大 SQL 备份文件，彻底解决 OOM 问题。

```
                        +----------------------+
输入 SQL 文件 --------> |     SQL Reader       | (流式读取与语句切分，跟踪行列坐标与条件注释)
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
        |   Lexer / Tokenizer  |        |   Pipeline 转换引擎  |
        +----------------------+        +----------------------+
                   │                               │
                   ▼                               ▼
        +----------------------+        +----------------------+
        |  手写 Token-AST 分析  |        |      磁盘临时缓存    |
        |  (DDL 下降状态机提取) |        |  (按表分流存储数据)  |
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
- **DDL/DML 分流**：输入文件通过 `SQLReader` 逐语句读入。`Statement Classifier` 判断语句类型。所有的 DDL、COMMENT、INDEX 经 Lexer 分词后，通过 AST Parser 分析并构建轻量级表结构图；占体积 99% 的 DML `INSERT` 数据则直接分流追加写入到本地磁盘的临时缓存中。
- **拓扑排序**：仅对内存中的轻量级 `TableBlock` 结构根据外键依赖关系进行拓扑排序，确定最终的安全输出顺序。

### 2. 流式 DML 翻译与写入 (DML Streaming Engine)
- 在写入目标 SQL 时，按照拓扑排序好的表顺序，先流式写入全局变量（如编码集等），接着依次流式写入对应的 DDL 语句。
- 随后，流式读取并解析该表对应的磁盘 DML 缓存文件，通过 `iter_insert_rows`（基于 Generator 的 VALUES 行解析器）实时完成类型映射与方言转换，并以 1000 行为批次立即 flush 到最终目标文件中。

---

## 模块结构

- `core/`：包含元数据模型 `Statement` / `Diagnostic`、分类异常继承树及全局日志 Logger。
- `reader/`：
  - `sql_reader.py`：基于状态机的流式 SQL 读取器，支持各种注释过滤、条件注释分句保留与 PostgreSQL Dollar Quote。
  - `classifier.py`：对语句类型进行判别分类。
- `writer/`：
  - `sql_writer.py`：带输出缓冲区的高效流式 SQL 写入器。
- `parser/`：
  - `insert_stream.py`：以生成器 (Generator) 逐行流式拆解 `INSERT VALUES`，极具内存优势。
- `utils/`：
  - `sql_parser/`：包含词法扫描器 `lexer.py` 与手写 Token 下降 DDL 解析器 `ddl_parser.py`、AST 渲染生成器 `generator.py`、外键拓扑排序 `toposort.py`。
  - `report.py`：多格式评估报告输出引擎。
  - `compat.py`：兼容性特性检索矩阵与不支持警告。
- `model/`：Schema AST 实体模型，包括 `Schema`, `TableBlock`, `ColumnDef`, `ForeignKeyDef`, `IndexDef`。
- `converter/`：Pipeline 转换规则引擎和数据库 Dialect 的注册与实现。
- `tests/`：
  - `test_*.py`：各单元测试。
  - `e2e/`：Golden File 集成校验测试，对 MySQL->PG、SQLServer->PG 等五种方言对进行自动验证。
