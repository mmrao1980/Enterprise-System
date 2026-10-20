"""
Integration Guide for Configuration Management System
Provides utilities to integrate the new configuration system into the main app.
"""

import streamlit as st
import json
import copy
from datetime import datetime
from typing import Dict, Any, List, Optional

from database_connection_manager import DatabaseConnectionManager
from tool_output_registry import ToolOutputRegistry
from page_configuration_manager import PageConfigurationManager, SmartConfigurationLoader


class ProjectConfigurationManager:
    """
    Master manager for the entire project configuration system.
    Coordinates database connections, tool output registry, and page configurations.
    """

    def __init__(self):
        self.db_manager = DatabaseConnectionManager()
        self.tool_registry = ToolOutputRegistry()
        self.page_configs = PageConfigurationManager()

    # =====================================================================
    # SESSION STATE INITIALIZATION
    # =====================================================================

    def initialize_session_state(self):
        """Initialize all session state variables for the configuration system."""
        if "db_connection_manager" not in st.session_state:
            st.session_state.db_connection_manager = self.db_manager

        if "tool_output_registry" not in st.session_state:
            st.session_state.tool_output_registry = self.tool_registry

        if "page_config_manager" not in st.session_state:
            st.session_state.page_config_manager = self.page_configs

        if "config_load_reports" not in st.session_state:
            st.session_state.config_load_reports = {}

    # =====================================================================
    # ENHANCED SAVE/LOAD FUNCTIONS
    # =====================================================================

    def generate_enhanced_project_blueprint(
        self,
        original_blueprint: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enhance existing project blueprint with new configuration data.
        
        Args:
            original_blueprint: Current project blueprint from save_project()
        
        Returns:
            Enhanced blueprint with database connections, tool registry, and page configs
        """
        enhanced = copy.deepcopy(original_blueprint)

        # Add database connection profiles
        enhanced["database_connections"] = self.db_manager.to_dict()

        # Add tool output registry metadata
        enhanced["tool_output_registry"] = self.tool_registry.to_dict()

        # Add page configurations
        enhanced["page_configurations"] = self.page_configs.to_dict()

        # Add config metadata
        enhanced["config_metadata"] = {
            "saved_at": datetime.now().isoformat(),
            "config_system_version": "1.0",
            "has_tool_chaining": len(self.tool_registry.outputs) > 0,
            "has_db_profiles": len(self.db_manager.profiles) > 0,
            "has_page_configs": len(self.page_configs.page_configs) > 0
        }

        return enhanced

    def load_enhanced_project_blueprint(
        self,
        blueprint: Dict[str, Any],
        new_dataset_columns: List[str]
    ) -> Dict[str, Any]:
        """
        Load and intelligently migrate project configuration for new dataset.
        
        Args:
            blueprint: Project blueprint to load
            new_dataset_columns: Columns available in the new dataset
        
        Returns:
            Dictionary with loaded data and migration reports
        """
        result = {
            "success": True,
            "messages": [],
            "warnings": [],
            "load_reports": {},
            "database_connections": None,
            "tool_registry": None,
            "page_configurations": None
        }

        try:
            # Load database connections (no migration needed, just restore)
            if "database_connections" in blueprint:
                self.db_manager = DatabaseConnectionManager.from_dict(
                    blueprint["database_connections"]
                )
                st.session_state.db_connection_manager = self.db_manager
                result["database_connections"] = blueprint["database_connections"]
                result["messages"].append(
                    f"✅ Loaded {len(self.db_manager.profiles)} database connection profiles"
                )

            # Load tool registry (metadata only, data will be regenerated)
            if "tool_output_registry" in blueprint:
                self.tool_registry = ToolOutputRegistry.from_dict(
                    blueprint["tool_output_registry"]
                )
                st.session_state.tool_output_registry = self.tool_registry
                result["tool_registry"] = blueprint["tool_output_registry"]
                result["messages"].append(
                    f"✅ Loaded tool output registry with {len(self.tool_registry.outputs)} outputs"
                )

            # Load and migrate page configurations
            if "page_configurations" in blueprint:
                self.page_configs = PageConfigurationManager.from_dict(
                    blueprint["page_configurations"]
                )
                st.session_state.page_config_manager = self.page_configs

                # Generate migration reports for each page config
                load_reports = {}
                for page_key, config_list in self.page_configs.page_configs.items():
                    if config_list:
                        latest = config_list[-1]
                        migrated, report = self._migrate_single_config(
                            latest.used_columns,
                            latest.config,
                            new_dataset_columns
                        )

                        load_reports[page_key] = {
                            "original_columns": latest.used_columns,
                            "new_columns": new_dataset_columns,
                            "migration_report": report,
                            "migrated_config": migrated
                        }

                result["page_configurations"] = load_reports
                result["load_reports"] = load_reports

                result["messages"].append(
                    f"✅ Loaded {len(self.page_configs.page_configs)} page configurations"
                )

                # Check for potential issues
                total_unmatched = sum(
                    len(report.get("analysis", {}).get("unmatched_saved_columns", []))
                    for report in load_reports.values()
                )
                if total_unmatched > 0:
                    result["warnings"].append(
                        f"⚠️ {total_unmatched} total column references not found in new dataset. "
                        f"Review migration reports."
                    )

        except Exception as e:
            result["success"] = False
            result["messages"].append(f"❌ Error loading configuration: {str(e)}")

        return result

    @staticmethod
    def _migrate_single_config(
        saved_columns: List[str],
        config: Dict[str, Any],
        new_columns: List[str]
    ) -> tuple:
        """Helper to migrate a single configuration."""
        from page_configuration_manager import ConfigColumnMatcher

        matched, unmatched, extra = ConfigColumnMatcher.find_matching_columns(
            saved_columns,
            new_columns
        )

        migrated, report = ConfigColumnMatcher.migrate_config(
            config,
            matched,
            new_columns
        )

        report["analysis"] = {
            "matched_columns": matched,
            "unmatched_saved_columns": unmatched,
            "extra_new_columns": extra
        }

        return migrated, report

    # =====================================================================
    # CONFIGURATION UTILITIES
    # =====================================================================

    def save_page_configuration_from_session(
        self,
        page_name: str,
        tool_name: str
    ) -> None:
        """
        Save current page configuration from session state.
        Call this when user finalizes settings on a validation page.
        """
        # Extract tool config from session state
        tool_config = st.session_state.get("tool_config", {})
        used_columns = st.session_state.get("selected_columns", [])

        self.page_configs.save_page_config(
            page_name=page_name,
            tool_name=tool_name,
            config=tool_config,
            used_columns=used_columns
        )

    def register_tool_output_from_session(
        self,
        step_id: str,
        tool_name: str,
        output_data,
        source_step_id: Optional[str] = None
    ) -> None:
        """
        Register tool output from session state.
        Call this after a tool executes successfully.
        """
        output_columns = list(output_data.columns) if hasattr(output_data, 'columns') else []
        row_count = len(output_data) if hasattr(output_data, '__len__') else 0
        execution_time = st.session_state.get(f"last_exec_time_{step_id}", 0)

        self.tool_registry.register_output(
            step_id=step_id,
            tool_name=tool_name,
            output_columns=output_columns,
            row_count=row_count,
            source_step_id=source_step_id,
            output_data=output_data,
            execution_time_ms=execution_time
        )

    def get_tool_input_data(
        self,
        input_step_id: Optional[str],
        main_df
    ):
        """
        Get input data for a tool, either from tool output or main dataset.
        """
        if input_step_id is None:
            return main_df

        cached_data = self.tool_registry.get_output_data(input_step_id)
        if cached_data is not None:
            return cached_data

        # If no cached data, need to re-execute upstream tools
        return None


class CustomProjectEncoder(json.JSONEncoder):
    """JSON encoder for project blueprints with custom type handling."""

    def default(self, obj):
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        elif isinstance(obj, set):
            return list(obj)
        try:
            return super().default(obj)
        except TypeError:
            return str(obj)


# =====================================================================
# HELPER FUNCTIONS FOR INTEGRATION
# =====================================================================

def initialize_configuration_system():
    """Initialize the configuration system when app starts."""
    manager = ProjectConfigurationManager()
    manager.initialize_session_state()
    return manager


def get_config_manager() -> ProjectConfigurationManager:
    """Get or create the configuration manager from session state."""
    if "project_config_manager" not in st.session_state:
        st.session_state.project_config_manager = initialize_configuration_system()

    return st.session_state.project_config_manager


def display_configuration_status():
    """Display status of configurations in sidebar."""
    manager = get_config_manager()

    st.sidebar.markdown("---")
    st.sidebar.subheader("📋 Configuration Status")

    col1, col2 = st.sidebar.columns(2)

    with col1:
        db_count = len(manager.db_manager.profiles)
        st.metric("DB Profiles", db_count)

    with col2:
        tool_count = len(manager.tool_registry.outputs)
        st.metric("Tool Outputs", tool_count)

    page_count = len(manager.page_configs.page_configs)
    st.sidebar.metric("Page Configs", page_count)
