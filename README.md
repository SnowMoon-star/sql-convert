# sql_convert

MySQL → KingbaseES（MySQL 兼容模式）SQL 转换器。

将 mysqldump 导出的 `.sql` 文件转换为可直接导入 Kingbase 的 SQL。基于正则规则引擎，零第三方依赖。

## 环境要求

- Python 3.10 或更高

## 用法

```bash
python convert.py <input.sql> [-o OUTPUT] [--mode {mysql}]
                              [--encoding ENC] [--overwrite] [-v]
```

| 参数 | 默认值 | 说明 |
|---|---|---|
| `input` | 必填 | 待转换的 mysqldump `.sql` 文件路径 |
| `-o, --output` | `<input 主名>_convert.<扩展>`，同目录 | 输出文件路径 |
| `--mode` | `mysql` | Kingbase 兼容模式，当前仅支持 `mysql` |
| `--encoding` | `utf-8` | 读写文件编码。若源文件为 GBK，用 `--encoding gbk` |
| `--overwrite` | 关 | 输出文件已存在时是否覆盖 |
| `-v, --verbose` | 关 | 打印每条规则命中次数 |

### 示例

```bash
# 基本用法：输出到 dump_convert.sql
python convert.py dump.sql

# 指定输出并覆盖
python convert.py dump.sql -o out.sql --overwrite

# 查看每条规则的命中统计
python convert.py dump.sql -v

# GBK 编码的源文件
python convert.py dump.sql --encoding gbk
```

### 退出码

- `0`：成功
- `2`：使用错误（参数、路径、权限）
- `3`：运行时错误（编码、IO、规则异常）

## 当前支持的转换规则

首批共 9 条，覆盖 mysqldump 输出中 Kingbase MySQL 模式不支持的常见语法：

1. 剔除 `/*!40101 ... */` 版本条件注释
2. 删除 `LOCK TABLES` / `UNLOCK TABLES` 行
3. 删除 `SET @OLD_...` / `SET @@...` 会话变量
4. 删除表级 `ENGINE=xxx`
5. 删除表级 `DEFAULT CHARSET` / `CHARACTER SET` / `COLLATE`
6. 删除表级 `AUTO_INCREMENT=N` 起始值（列级 `AUTO_INCREMENT` 保留）
7. 删除 `ROW_FORMAT` / `KEY_BLOCK_SIZE` 等表选项
8. 删除列定义中的 `CHARACTER SET` / `COLLATE`
9. 展开 `DELIMITER $$ ... $$ DELIMITER ;` 块

**数据安全底线：** 所有规则均设置 `skip_insert=True`，`INSERT INTO` 数据行绝对不会被修改。

## 新增规则

在 `rules.py` 的 `RULES` 列表末尾追加条目，主流程无需改动。字段说明见文件顶部 docstring。

## 手动验证

```bash
python convert.py tests/sample_input.sql -o tests/actual.sql --overwrite
diff tests/actual.sql tests/sample_output.sql
rm tests/actual.sql
```

`diff` 无输出即通过。

## 真实数据验证

用真实 mysqldump 文件跑一遍 `convert.py`，把输出导入 Kingbase；如出现导入报错，把对应语法补进 `RULES` 并回归 `tests/sample_input.sql`。
