"""
Page Configuration Manager
Manages and persists configurations for all validation/processing pages.
Enables intelligent column matching when reusing configurations with new datasets.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import copy


class PageConfiguration:
    """Represents a configuration for a specific page/validation."""

    def __init__(
        self,
        page_name: str,
        tool_name: str,
        config: Dict[str, Any],
        used_columns: List[str],
        created_at: str = None
    ):
        self.page_name = page_name  # e.g., "Missing Checks", "Duplicate Checks"
        self.tool_name = tool_name  # e.g., "Missing Tool", "Duplicate Tool"
        self.config = config  # Full tool configuration
        self.used_columns = used_columns  # Columns referenced in this config
        self.created_at = created_at or datetime.now().isoformat()

    def to_dict(self) -> Dict:
        """Serialize configuration."""
        return {
            "page_name": self.page_name,
            "tool_name": self.tool_name,
            "config": copy.deepcopy(self.config),
            "used_columns": list(self.used_columns),
            "created_at": self.created_at
        }

    @staticmethod
    def from_dict(data: Dict) -> "PageConfiguration":
        """Deserialize configuration."""
        return PageConfiguration(
            page_name=data.get("page_name", ""),
            tool_name=data.get("tool_name", ""),
            config=data.get("config", {}),
            used_columns=data.get("used_columns", []),
            created_at=data.get("created_at")
        )


class ConfigColumnMatcher:
    """Intelligently matches saved configurations to new dataset columns."""

    @staticmethod
    def find_matching_columns(
        saved_columns: List[str],
        new_columns: List[str]
    ) -> Tuple[Dict[str, str], List[str], List[str]]:
        """
        Match saved columns to new dataset columns.
        
        Returns:
        - matched: {saved_col: new_col} mapping for exact/case-insensitive matches
        - unmatched_saved: columns in saved config not found in new dataset
        - extra_new: columns in new dataset not in saved config
        """
        matched = {}
        unmatched_saved = []
        extra_new = list(new_columns)  # Will remove as we match

        new_cols_lower = {col.lower(): col for col in new_columns}

        for saved_col in saved_columns:
        # ✅ SAFETY CHECK — fixes Logical Checks crash
            if not isinstance(saved_col, str) or not saved_col.strip():
               unmatched_saved.append(saved_col)
               continue

            saved_lower = saved_col.strip().lower()

            # Try exact match (case-insensitive)
            if saved_lower in new_cols_lower:
                matched_col = new_cols_lower[saved_lower]
                matched[saved_col] = matched_col
                if matched_col in extra_new:
                    extra_new.remove(matched_col)
            else:
                unmatched_saved.append(saved_col)

        return matched, unmatched_saved, extra_new

    @staticmethod
    def migrate_config(
        saved_config: Dict[str, Any],
        column_mapping: Dict[str, str],
        new_available_columns: List[str]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Migrate saved configuration to work with new dataset.
        
        Returns:
        - migrated_config: updated configuration with remapped columns
        - migration_report: dict with details about what changed
        """
        migrated_config = copy.deepcopy(saved_config)
        report = {
            "columns_updated": {},
            "columns_removed": [],
            "columns_added": [],
            "migration_notes": []
        }

        # Remap columns in configuration
        for key, value in migrated_config.items():
            if isinstance(value, str) and value in column_mapping:
                old_col = value
                new_col = column_mapping[value]
                migrated_config[key] = new_col
                report["columns_updated"][old_col] = new_col

            elif isinstance(value, list) and all(isinstance(v, str) for v in value):
                # Check if it's a list of columns
                remapped = []
                for col in value:
                    if col in column_mapping:
                        remapped.append(column_mapping[col])
                        if col not in report["columns_updated"]:
                            report["columns_updated"][col] = column_mapping[col]
                    elif col in new_available_columns:
                        remapped.append(col)  # Keep if it exists in new dataset
                    else:
                        report["columns_removed"].append(col)

                migrated_config[key] = remapped

        report["migration_notes"].append(
            f"Successfully migrated {len(report['columns_updated'])} column references"
        )
        if report["columns_removed"]:
            report["migration_notes"].append(
                f"Removed {len(report['columns_removed'])} unmapped columns"
            )

        return migrated_config, report


class PageConfigurationManager:
    """Manages configurations for all pages in the application."""

    def __init__(self):
        self.page_configs: Dict[str, List[PageConfiguration]] = {}

    def save_page_config(
        self,
        page_name: str,
        tool_name: str,
        config: Dict[str, Any],
        used_columns: List[str]
    ):
        """Save configuration for a specific page/tool."""
        page_key = f"{page_name}_{tool_name}"

        if page_key not in self.page_configs:
            self.page_configs[page_key] = []

        # Add new configuration (keep history)
        page_config = PageConfiguration(
            page_name=page_name,
            tool_name=tool_name,
            config=config,
            used_columns=used_columns
        )
        self.page_configs[page_key].append(page_config)

    def get_latest_page_config(
        self,
        page_name: str,
        tool_name: str
    ) -> Optional[PageConfiguration]:
        """Get the most recent configuration for a page/tool."""
        page_key = f"{page_name}_{tool_name}"
        if page_key in self.page_configs and self.page_configs[page_key]:
            return self.page_configs[page_key][-1]
        return None

    def get_page_configs_for_page(
        self,
        page_name: str
    ) -> List[Dict[str, Any]]:
        """Get all tool configurations for a specific page."""
        configs = []
        for key, config_list in self.page_configs.items():
            if key.startswith(page_name):
                if config_list:
                    configs.append(config_list[-1].to_dict())
        return configs

    def migrate_page_config(
        self,
        page_name: str,
        tool_name: str,
        new_available_columns: List[str]
    ) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        Migrate saved page configuration to new dataset.
        
        Returns:
        - migrated_config: updated config for new dataset
        - migration_report: details about changes made
        """
        saved_config = self.get_latest_page_config(page_name, tool_name)
        if not saved_config:
            return None, None

        # Find column matches
        matched, unmatched, extra = ConfigColumnMatcher.find_matching_columns(
            saved_config.used_columns,
            new_available_columns
        )

        # Migrate configuration
        migrated, report = ConfigColumnMatcher.migrate_config(
            saved_config.config,
            matched,
            new_available_columns
        )

        report["analysis"] = {
            "matched_columns": len(matched),
            "unmatched_saved_columns": unmatched,
            "extra_new_columns": extra,
            "remapping": matched
        }

        return migrated, report

    def clear_page_configs(self):
        """Clear all page configurations."""
        self.page_configs.clear()

    def to_dict(self) -> Dict:
        """Serialize all page configurations."""
        result = {}
        for key, config_list in self.page_configs.items():
            result[key] = [cfg.to_dict() for cfg in config_list]
        return result

    @staticmethod
    def from_dict(data: Dict) -> "PageConfigurationManager":
        """Deserialize page configurations."""
        manager = PageConfigurationManager()
        for key, config_list_data in data.items():
            manager.page_configs[key] = [
                PageConfiguration.from_dict(cfg)
                for cfg in config_list_data
            ]
        return manager


class SmartConfigurationLoader:
    """Loads saved project configurations intelligently with new dataset."""

    @staticmethod
    def generate_load_report(
        page_name: str,
        saved_columns: List[str],
        new_columns: List[str],
        migration_report: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a user-friendly report of configuration loading."""
        matched, unmatched, extra = ConfigColumnMatcher.find_matching_columns(
            saved_columns,
            new_columns
        )

        return {
            "page_name": page_name,
            "status": "migrated" if matched or len(unmatched) < len(saved_columns) else "unchanged",
            "summary": {
                "total_saved_columns": len(saved_columns),
                "matched_columns": len(matched),
                "unmatched_columns": len(unmatched),
                "extra_columns": len(extra)
            },
            "details": {
                "matched": matched,  # {old: new} mapping
                "unmatched": unmatched,  # Columns not found
                "extra": extra,  # New columns not in saved config
            },
            "migration_report": migration_report,
            "message": f"Loaded configuration with {len(matched)} matching columns. "
                       f"{len(unmatched)} columns not found in new dataset. "
                       f"{len(extra)} new columns available."
        }

    @staticmethod
    def generate_full_load_report(
        page_configs: Dict[str, Tuple[Dict[str, Any], Dict[str, Any]]],
        new_columns: List[str]
    ) -> Dict[str, Dict]:
        """Generate comprehensive report for all loaded page configurations."""
        full_report = {}

        for page_key, (migrated_config, migration_report) in page_configs.items():
            page_name = page_key.split("_")[0]
            saved_columns = migration_report.get("analysis", {}).get("analysis", {}).get("saved_columns", [])

            full_report[page_key] = SmartConfigurationLoader.generate_load_report(
                page_name,
                saved_columns,
                new_columns,
                migration_report
            )

        return full_report
