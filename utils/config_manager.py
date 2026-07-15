"""配置加载管理器 — 负责加载 config.yml / config.template.yml 并向各组件提供配置支持。"""
from __future__ import annotations
import os
from pathlib import Path
from typing import Any

# 默认硬编码配置兜底
_DEFAULT_CONFIG = {
    "converter": {
        "continue_on_error": False,
        "encoding": "utf-8",
        "batch_size": 1000,
    },
    "web": {
        "host": "127.0.0.1",
        "port": 8000,
        "max_upload_size_mb": 500,
    },
    "dialects": {
        "mysql": {
            "default_engine": "InnoDB",
        },
        "pgsql": {
            "drop_cascade": True,
        }
    }
}


class ConfigManager:
    """SQL 转换器全局配置管理器。"""

    def __init__(self, config_path: str | Path | None = None):
        self.root_dir = Path(__file__).parent.parent.resolve()
        
        # 确定配置文件的路径优先级：
        # 1. 显式指定的路径
        # 2. 根目录下的 config.yml
        # 3. 根目录下的 config.template.yml
        if config_path:
            self.config_path = Path(config_path)
        else:
            local_config = self.root_dir / "config.yml"
            if local_config.exists():
                self.config_path = local_config
            else:
                self.config_path = self.root_dir / "config.template.yml"

        self.config: dict[str, Any] = _DEFAULT_CONFIG.copy()
        self._load_config()

    def _load_config(self) -> None:
        """从文件流式加载并合并默认配置。"""
        if not self.config_path.exists():
            return

        try:
            import yaml
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data and isinstance(data, dict):
                    self._deep_update(self.config, data)
        except ImportError:
            # 兼容未安装 yaml 时的极度精简运行（降级至硬编码默认配置）
            pass
        except Exception:
            # 读取异常时回退到默认，不崩溃
            pass

    def _deep_update(self, base_dict: dict, update_dict: dict) -> None:
        """深度合并字典配置，确保嵌套结构不会被直接覆盖。"""
        for k, v in update_dict.items():
            if isinstance(v, dict) and k in base_dict and isinstance(base_dict[k], dict):
                self._deep_update(base_dict[k], v)
            else:
                base_dict[k] = v

    def get(self, key_path: str, default: Any = None) -> Any:
        """通过点语法访问嵌套配置，例如 get("converter.batch_size")。"""
        parts = key_path.split(".")
        current = self.config
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        return current


# 全局单例配置实例
config = ConfigManager()
