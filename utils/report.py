"""转换报告 (Conversion Report) 引擎 — 记录指标、警告、错误并生成精美的可视化 HTML 报告。"""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ConversionReport:
    start_time: float = field(default_factory=time.perf_counter)
    end_time: float | None = None

    # 结构指标统计
    table_count: int = 0
    index_count: int = 0
    constraint_count: int = 0

    # 转换规则与状态
    rule_hits: dict[str, int] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    failed_statements: list[dict] = field(default_factory=list)  # {"sql": str, "error": str}
    
    # 异步/多线程 Web 回调支持
    progress_callback: Any = None
    _last_notified_line: int = 0

    def notify_progress(self, current_line: int, status: str = "PROCESSING"):
        """推流进度通知到绑定的回调接口（限制推送频率）。"""
        if self.progress_callback:
            # 状态变更、首行或行数增加 500 时推送以节省 I/O 资源
            if status != "PROCESSING" or current_line - self._last_notified_line >= 500 or self._last_notified_line == 0:
                self._last_notified_line = current_line
                self.progress_callback({
                    "status": status,
                    "current_line": current_line,
                    "table_count": self.table_count,
                    "index_count": self.index_count,
                    "constraint_count": self.constraint_count,
                    "warning_count": len(self.warnings),
                    "failure_count": len(self.failed_statements),
                })

    def start(self):
        self.start_time = time.perf_counter()


    def stop(self):
        self.end_time = time.perf_counter()

    @property
    def duration(self) -> float:
        if self.end_time is None:
            return time.perf_counter() - self.start_time
        return self.end_time - self.start_time

    def add_warning(self, msg: str):
        # 告警去重
        if msg not in self.warnings:
            self.warnings.append(msg)

    def record_failure(self, sql: str, err: Exception):
        self.failed_statements.append({
            "sql": sql.strip(),
            "error": str(err)
        })

    def increment_table(self):
        self.table_count += 1

    def increment_index(self, count: int = 1):
        self.index_count += count

    def increment_constraint(self, count: int = 1):
        self.constraint_count += count

    def update_rule_hits(self, hits: dict[str, int]):
        for k, v in hits.items():
            if v > 0:
                self.rule_hits[k] = self.rule_hits.get(k, 0) + v

    def generate_html(self, source_mode: str, target_mode: str) -> str:
        """生成富交互、具有精美现代设计（自适应暗色/亮色模式）的 HTML 转换报告。"""
        # 总规则命中次数
        total_rules = sum(self.rule_hits.values())
        warning_count = len(self.warnings)
        failure_count = len(self.failed_statements)
        
        # 状态颜色
        status_text = "转换成功" if failure_count == 0 else "转换存在异常"
        status_class = "status-success" if failure_count == 0 else "status-error"

        # 规则命中的 HTML
        rule_rows_html = ""
        if self.rule_hits:
            for rule_name, count in sorted(self.rule_hits.items(), key=lambda x: x[1], reverse=True):
                rule_rows_html += f"""
                <tr>
                    <td class="font-mono">{rule_name}</td>
                    <td class="text-right font-bold">{count} 次</td>
                </tr>
                """
        else:
            rule_rows_html = "<tr><td colspan='2' class='text-center text-muted'>无规则匹配次数统计</td></tr>"

        # 告警 HTML（对告警文本进行 HTML 转义，防止 XSS 注入）
        warnings_html = ""
        if self.warnings:
            import html as _html
            for i, warn in enumerate(self.warnings):
                warn_escaped = _html.escape(warn)
                warn_body = warn_escaped.split(']', 1)[1].strip() if ']' in warn_escaped else warn_escaped
                warn_level = warn_escaped.split(']', 1)[0].replace('[', '') if '[' in warn_escaped else '警告'
                warnings_html += f"""
                <div class="accordion-item">
                    <button class="accordion-header" onclick="toggleAccordion('warn-{i}')">
                        <span class="badge badge-warning">告警</span> {warn_body}
                    </button>
                    <div id="warn-{i}" class="accordion-content">
                        <div class="content-inner">
                            <strong>告警级别：</strong> {warn_level}<br/>
                            <strong>提示：</strong> 请仔细核对目标库的语法支持情况，必要时手工微调转换后的 SQL。
                        </div>
                    </div>
                </div>
                """
        else:
            warnings_html = """
            <div class="success-banner">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l5-5z" clip-rule="evenodd"/>
                </svg>
                <span>未检测到任何兼容性风险（Feature Matrix 校验通过）。</span>
            </div>
            """

        # 失败语句 HTML（对 SQL 原文及错误信息进行 HTML 转义，防止 XSS 注入）
        failures_html = ""
        if self.failed_statements:
            import html as _html
            for i, fail in enumerate(self.failed_statements):
                sql_snippet = fail['sql']
                if len(sql_snippet) > 200:
                    sql_snippet = sql_snippet[:200] + "\n... (语句过长已截断) ..."
                sql_snippet_escaped = _html.escape(sql_snippet)
                error_escaped = _html.escape(fail['error'])

                failures_html += f"""
                <div class="accordion-item error-item">
                    <button class="accordion-header" onclick="toggleAccordion('fail-{i}')">
                        <span class="badge badge-danger">失败</span> 语句 #{i+1} 解析异常
                    </button>
                    <div id="fail-{i}" class="accordion-content">
                        <div class="content-inner">
                            <div class="error-msg"><strong>异常描述：</strong> {error_escaped}</div>
                            <pre class="code-block"><code>{sql_snippet_escaped}</code></pre>
                        </div>
                    </div>
                </div>
                """
        else:
            failures_html = """
            <div class="success-banner">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l5-5z" clip-rule="evenodd"/>
                </svg>
                <span>所有输入语句均成功转换并分流，无执行失败。</span>
            </div>
            """

        # 构造完整富设计感的 HTML 模板
        html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SQL 转换评估报告</title>
    <style>
        :root {{
            --bg-color: #f8fafc;
            --card-bg: #ffffff;
            --text-color: #1e293b;
            --text-muted: #64748b;
            --primary: #6366f1;
            --primary-light: #e0e7ff;
            --success: #10b981;
            --success-light: #d1fae5;
            --warning: #f59e0b;
            --warning-light: #fef3c7;
            --danger: #ef4444;
            --danger-light: #fee2e2;
            --border-color: #e2e8f0;
            --shadow: 0 4px 6px -1px rgb(0 0 0 / 0.05), 0 2px 4px -2px rgb(0 0 0 / 0.05);
            --shadow-hover: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
        }}

        @media (prefers-color-scheme: dark) {{
            :root {{
                --bg-color: #0f172a;
                --card-bg: #1e293b;
                --text-color: #f1f5f9;
                --text-muted: #94a3b8;
                --primary: #818cf8;
                --primary-light: #312e81;
                --success: #34d399;
                --success-light: #064e3b;
                --warning: #fbbf24;
                --warning-light: #78350f;
                --danger: #f87171;
                --danger-light: #7f1d1d;
                --border-color: #334155;
                --shadow: 0 4px 6px -1px rgb(0 0 0 / 0.3), 0 2px 4px -2px rgb(0 0 0 / 0.3);
                --shadow-hover: 0 12px 20px -3px rgb(0 0 0 / 0.5), 0 4px 8px -4px rgb(0 0 0 / 0.5);
            }}
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            margin: 0;
            padding: 2rem 1rem;
            line-height: 1.5;
            transition: background-color 0.3s, color 0.3s;
        }}

        .container {{
            max-width: 1000px;
            margin: 0 auto;
        }}

        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            flex-wrap: wrap;
            gap: 1rem;
        }}

        h1 {{
            margin: 0;
            font-size: 1.8rem;
            font-weight: 800;
            background: linear-gradient(135deg, var(--primary), #ec4899);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .dialect-flow {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.95rem;
            font-weight: 600;
            background-color: var(--primary-light);
            color: var(--primary);
            padding: 0.5rem 1rem;
            border-radius: 9999px;
            transition: all 0.3s;
        }}

        .dialect-flow svg {{
            width: 16px;
            height: 16px;
        }}

        /* 状态标识 */
        .status-badge {{
            font-weight: 600;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-size: 0.9rem;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .status-success {{
            background-color: var(--success-light);
            color: var(--success);
        }}

        .status-error {{
            background-color: var(--danger-light);
            color: var(--danger);
        }}

        /* 指标卡片 */
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1.25rem;
            margin-bottom: 2rem;
        }}

        .metric-card {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.25rem;
            box-shadow: var(--shadow);
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        .metric-card:hover {{
            transform: translateY(-4px);
            box-shadow: var(--shadow-hover);
        }}

        .metric-label {{
            font-size: 0.85rem;
            color: var(--text-muted);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
        }}

        .metric-value {{
            font-size: 1.8rem;
            font-weight: 700;
            color: var(--text-color);
        }}

        .metric-subtext {{
            font-size: 0.8rem;
            color: var(--text-muted);
            margin-top: 0.25rem;
        }}

        /* 主体布局 */
        .main-layout {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 1.5rem;
        }}

        @media (min-width: 768px) {{
            .main-layout {{
                grid-template-columns: 3fr 2fr;
            }}
        }}

        .card {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: var(--shadow);
            margin-bottom: 1.5rem;
        }}

        .card-title {{
            font-size: 1.1rem;
            font-weight: 700;
            margin-top: 0;
            margin-bottom: 1.25rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 0.75rem;
        }}

        /* 表格样式 */
        table {{
            width: 100%;
            border-collapse: collapse;
        }}

        th, td {{
            padding: 0.75rem 1rem;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
            font-size: 0.9rem;
        }}

        th {{
            color: var(--text-muted);
            font-weight: 600;
        }}

        tr:last-child td {{
            border-bottom: none;
        }}

        .text-right {{
            text-align: right;
        }}

        .font-mono {{
            font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace;
            font-size: 0.85rem;
        }}

        .font-bold {{
            font-weight: 700;
        }}

        /* 折叠面板 (Accordion) */
        .accordion-item {{
            border: 1px solid var(--border-color);
            border-radius: 8px;
            margin-bottom: 0.75rem;
            overflow: hidden;
        }}

        .accordion-header {{
            width: 100%;
            background-color: var(--card-bg);
            color: var(--text-color);
            border: none;
            padding: 0.85rem 1.25rem;
            text-align: left;
            font-weight: 600;
            font-size: 0.9rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            transition: background-color 0.2s;
        }}

        .accordion-header:hover {{
            background-color: var(--primary-light);
            color: var(--primary);
        }}

        .accordion-content {{
            display: none;
            background-color: var(--bg-color);
            border-top: 1px solid var(--border-color);
        }}

        .content-inner {{
            padding: 1rem 1.25rem;
            font-size: 0.85rem;
            color: var(--text-color);
        }}

        .badge {{
            font-size: 0.75rem;
            font-weight: 700;
            padding: 0.15rem 0.5rem;
            border-radius: 4px;
            text-transform: uppercase;
        }}

        .badge-warning {{
            background-color: var(--warning-light);
            color: var(--warning);
        }}

        .badge-danger {{
            background-color: var(--danger-light);
            color: var(--danger);
        }}

        .success-banner {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            background-color: var(--success-light);
            color: var(--success);
            padding: 1rem;
            border-radius: 8px;
            font-size: 0.9rem;
            font-weight: 500;
        }}

        .code-block {{
            margin-top: 0.75rem;
            margin-bottom: 0;
            padding: 0.75rem 1rem;
            background-color: #1e293b;
            color: #f1f5f9;
            border-radius: 6px;
            overflow-x: auto;
            font-family: SFMono-Regular, Consolas, monospace;
            font-size: 0.8rem;
        }}

        .error-msg {{
            color: var(--danger);
            background-color: var(--danger-light);
            padding: 0.5rem 0.75rem;
            border-radius: 4px;
            margin-bottom: 0.75rem;
        }}

        footer {{
            text-align: center;
            font-size: 0.8rem;
            color: var(--text-muted);
            margin-top: 3rem;
            border-top: 1px solid var(--border-color);
            padding-top: 1.5rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>SQL 转换评估报告</h1>
                <div style="font-size: 0.85rem; color: var(--text-muted); margin-top: 0.25rem;">
                    生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}
                </div>
            </div>
            <div style="display: flex; gap: 0.75rem; align-items: center;">
                <div class="dialect-flow">
                    <span>{source_mode.upper()}</span>
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3"></path>
                    </svg>
                    <span>{target_mode.upper()}</span>
                </div>
                <div class="status-badge {status_class}">
                    {status_text}
                </div>
            </div>
        </header>

        <!-- 指标网格 -->
        <section class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">处理表总数</div>
                <div class="metric-value">{self.table_count}</div>
                <div class="metric-subtext">Table Blocks</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">额外索引总数</div>
                <div class="metric-value">{self.index_count}</div>
                <div class="metric-subtext">Index Blocks</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">外键/约束总数</div>
                <div class="metric-value">{self.constraint_count}</div>
                <div class="metric-subtext">Constraints</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">转换规则命中</div>
                <div class="metric-value">{total_rules}</div>
                <div class="metric-subtext">Rule Applications</div>
            </div>
        </section>

        <!-- 主体布局 -->
        <div class="main-layout">
            <!-- 左侧：警告与失败 -->
            <div>
                <div class="card">
                    <div class="card-title">
                        <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
                        </svg>
                        语法兼容性告警 ({warning_count})
                    </div>
                    {warnings_html}
                </div>

                <div class="card">
                    <div class="card-title">
                        <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                        解析失败语句明细 ({failure_count})
                    </div>
                    {failures_html}
                </div>
            </div>

            <!-- 右侧：统计细节与规则命中 -->
            <div>
                <div class="card">
                    <div class="card-title">
                        <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                        转换明细指标
                    </div>
                    <table>
                        <tr>
                            <td>累计处理耗时</td>
                            <td class="text-right font-bold">{self.duration:.4f} 秒</td>
                        </tr>
                        <tr>
                            <td>警告规则命中数</td>
                            <td class="text-right font-bold">{warning_count} 次</td>
                        </tr>
                        <tr>
                            <td>抛错并跳过语句</td>
                            <td class="text-right font-bold">{failure_count} 条</td>
                        </tr>
                    </table>
                </div>

                <div class="card">
                    <div class="card-title">
                        <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"></path>
                        </svg>
                        细分规则命频统计
                    </div>
                    <table>
                        <thead>
                            <tr>
                                <th>规则名称</th>
                                <th class="text-right">命中次数</th>
                            </tr>
                        </thead>
                        <tbody>
                            {rule_rows_html}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <footer>
            sql_convert 数据库方言流式迁移转换评估报告 • Powered by Antigravity
        </footer>
    </div>

    <script>
        function toggleAccordion(id) {{
            var content = document.getElementById(id);
            if (content.style.display === "block") {{
                content.style.display = "none";
            }} else {{
                content.style.display = "block";
            }}
        }}
    </script>
</body>
</html>
"""
        return html_template

    def generate_json(self) -> str:
        """生成结构化的 JSON 报告。"""
        import json
        data = {
            "duration": self.duration,
            "table_count": self.table_count,
            "index_count": self.index_count,
            "constraint_count": self.constraint_count,
            "rule_hits": self.rule_hits,
            "warnings": self.warnings,
            "failed_statements": self.failed_statements
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    def generate_markdown(self, source_mode: str, target_mode: str) -> str:
        """生成 Markdown 格式的评估报告。"""
        total_rules = sum(self.rule_hits.values())
        warning_count = len(self.warnings)
        failure_count = len(self.failed_statements)

        lines = [
            "# SQL 转换评估报告",
            "",
            f"- **源方言**: `{source_mode.upper()}`",
            f"- **目标方言**: `{target_mode.upper()}`",
            f"- **转换耗时**: `{self.duration:.4f} 秒`",
            f"- **转换状态**: `{'成功' if failure_count == 0 else '存在异常'}`",
            "",
            "## 1. 结构指标统计",
            "",
            f"- **表总数**: {self.table_count}",
            f"- **额外索引数**: {self.index_count}",
            f"- **外键与约束数**: {self.constraint_count}",
            f"- **规则累计命中**: {total_rules}",
            "",
            "## 2. 转换规则命中统计",
            ""
        ]

        if self.rule_hits:
            lines.append("| 规则名称 | 命中次数 |")
            lines.append("| :--- | :--- |")
            for name, count in sorted(self.rule_hits.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"| `{name}` | {count} 次 |")
        else:
            lines.append("未匹配到任何转换规则。")

        lines.append("")
        lines.append(f"## 3. 语法兼容性告警 ({warning_count})")
        lines.append("")
        if self.warnings:
            for warn in self.warnings:
                lines.append(f"- {warn}")
        else:
            lines.append("未发现兼容性风险（Feature Matrix 校验全部通过）。")

        lines.append("")
        lines.append(f"## 4. 解析失败语句明细 ({failure_count})")
        lines.append("")
        if self.failed_statements:
            for i, fail in enumerate(self.failed_statements):
                lines.append(f"### 失败语句 #{i+1}")
                lines.append(f"- **错误描述**: `{fail['error']}`")
                lines.append("- **SQL 原文**:")
                lines.append("```sql")
                lines.append(fail["sql"])
                lines.append("```")
        else:
            lines.append("所有输入语句均正常转换并解析，无失败项。")

        return "\n".join(lines)

    def generate_console(self, source_mode: str, target_mode: str) -> str:
        """生成终端控制台格式化报告。"""
        total_rules = sum(self.rule_hits.values())
        warning_count = len(self.warnings)
        failure_count = len(self.failed_statements)

        lines = [
            "===========================================",
            "              SQL 转换评估报告",
            "===========================================",
            f"方言转换流: {source_mode.upper()} -> {target_mode.upper()}",
            f"累计转换耗时: {self.duration:.4f} 秒",
            f"结构统计: 表 {self.table_count} | 索引 {self.index_count} | 约束 {self.constraint_count}",
            f"转换规则命中: {total_rules} 次",
            f"兼容性告警: {warning_count} 个",
            f"转换失败语句: {failure_count} 个",
            "==========================================="
        ]
        return "\n".join(lines)

    def write_report(self, output_path: str | Path, source_mode: str, target_mode: str) -> Path:
        """根据输出路径生成匹配的 HTML 报告文件：<输出主名>_report.html。"""
        out_p = Path(output_path)
        
        # 确保目录存在
        out_p.parent.mkdir(parents=True, exist_ok=True)

        # 写出 HTML
        report_name = f"{out_p.stem}_report.html"
        report_path = out_p.with_name(report_name)
        report_path.write_text(self.generate_html(source_mode, target_mode), encoding="utf-8")

        return report_path
