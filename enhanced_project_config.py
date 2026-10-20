"""
Enhanced Project Configuration System Integration
Integrates all configuration management features into save/load pipeline.
Handles database connections, tool chaining, page configurations, and smart column matching.
"""

import streamlit as st
import json
import copy
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from database_connection_manager import DatabaseConnectionManager, DatabaseConnectionProfile
from tool_output_registry import ToolOutputRegistry
from page_configuration_manager import PageConfigurationManager, ConfigColumnMatcher, SmartConfigurationLoader


class EnhancedProjectConfigManager:
    """
    Master manager integrating all configuration enhancement features.
    Provides enhanced save/load with full configuration persistence.
    """
    
    def __init__(self):
        self.db_manager = DatabaseConnectionManager()
        self.tool_registry = ToolOutputRegistry()
        self.page_configs = PageConfigurationManager()
        self.load_reports = {}
    
    def initialize_session_state(self):
        """Initialize all session state for enhanced configuration system."""
        if "enhanced_config_manager" not in st.session_state:
            st.session_state.enhanced_config_manager = self
        
        if "db_connection_manager" not in st.session_state:
            st.session_state.db_connection_manager = self.db_manager
        
        if "tool_output_registry" not in st.session_state:
            st.session_state.tool_output_registry = self.tool_registry
        
        if "page_config_manager" not in st.session_state:
            st.session_state.page_config_manager = self.page_configs
        
        if "config_load_reports" not in st.session_state:
            st.session_state.config_load_reports = {}
    
    # =====================================================================
    # ENHANCED SAVE OPERATIONS
    # =====================================================================
    
    def enhance_project_blueprint(
        self,
        original_blueprint: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enhance a project blueprint with configuration data.
        
        Args:
            original_blueprint: Original blueprint from save_project()
        
        Returns:
            Enhanced blueprint with all configuration data
        """
        enhanced = copy.deepcopy(original_blueprint)
        
        # Add database connection profiles (without passwords)
        enhanced["database_connections"] = self.db_manager.to_dict()
        
        # Add tool output registry metadata
        enhanced["tool_output_registry"] = self.tool_registry.to_dict()
        
        # Add page configurations
        enhanced["page_configurations"] = self.page_configs.to_dict()
        
        # Add configuration metadata
        enhanced["config_metadata"] = {
            "enhanced_at": datetime.now().isoformat(),
            "config_system_version": "2.0",
            "has_tool_chaining": len(self.tool_registry.outputs) > 0,
            "has_db_profiles": len(self.db_manager.profiles) > 0,
            "has_page_configs": len(self.page_configs.page_configs) > 0,
            "page_config_count": len(self.page_configs.page_configs),
            "db_profile_count": len(self.db_manager.profiles),
            "tool_output_count": len(self.tool_registry.outputs)
        }
        
        return enhanced
    
    def capture_page_configuration(
        self,
        page_name: str,
        tool_name: str,
        used_columns: Optional[List[str]] = None
    ) -> None:
        """
        Capture current page configuration from session state.
        Call after user finalizes settings on a validation page.
        """
        tool_config = st.session_state.get("tool_config", {})
        if used_columns is None:
            used_columns = st.session_state.get("selected_columns", [])
        
        self.page_configs.save_page_config(
            page_name=page_name,
            tool_name=tool_name,
            config=copy.deepcopy(tool_config),
            used_columns=list(used_columns)
        )
    
    def register_tool_execution(
        self,
        step_id: str,
        tool_name: str,
        output_data: Any,
        source_step_id: Optional[str] = None
    ) -> None:
        """
        Register a tool execution output for chaining.
        Call after a tool completes successfully.
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
    
    # =====================================================================
    # ENHANCED LOAD OPERATIONS
    # =====================================================================
    
    def load_enhanced_blueprint(
        self,
        blueprint: Dict[str, Any],
        new_dataset_columns: List[str]
    ) -> Dict[str, Any]:
        """
        Load and intelligently migrate project configurations for new dataset.
        
        Args:
            blueprint: Project blueprint to load
            new_dataset_columns: Columns available in new dataset
        
        Returns:
            Load result with messages, warnings, and migration reports
        """
        result = {
            "success": True,
            "messages": [],
            "warnings": [],
            "errors": [],
            "load_reports": {},
            "database_connections": None,
            "tool_registry": None,
            "page_configurations": None,
            "column_mapping": {},
            "smart_load_enabled": True
        }
        
        try:
            # =========================================================
            # LOAD DATABASE CONNECTIONS
            # =========================================================
            if "database_connections" in blueprint:
                self.db_manager = DatabaseConnectionManager.from_dict(
                    blueprint["database_connections"]
                )
                st.session_state.db_connection_manager = self.db_manager
                result["database_connections"] = blueprint["database_connections"]
                
                profile_count = len(self.db_manager.profiles)
                if profile_count > 0:
                    result["messages"].append(
                        f"✅ Loaded {profile_count} database connection profile(s)"
                    )
            
            # =========================================================
            # LOAD TOOL OUTPUT REGISTRY
            # =========================================================
            if "tool_output_registry" in blueprint:
                self.tool_registry = ToolOutputRegistry.from_dict(
                    blueprint["tool_output_registry"]
                )
                st.session_state.tool_output_registry = self.tool_registry
                result["tool_registry"] = blueprint["tool_output_registry"]
                
                output_count = len(self.tool_registry.outputs)
                if output_count > 0:
                    result["messages"].append(
                        f"✅ Loaded tool output registry with {output_count} registered output(s)"
                    )
            
            # =========================================================
            # LOAD AND MIGRATE PAGE CONFIGURATIONS
            # =========================================================
            if "page_configurations" in blueprint:
                self.page_configs = PageConfigurationManager.from_dict(
                    blueprint["page_configurations"]
                )
                st.session_state.page_config_manager = self.page_configs
                
                # Generate migration reports
                load_reports = {}
                total_matched = 0
                total_unmatched = 0
                
                for page_key, config_list in self.page_configs.page_configs.items():
                    if config_list:
                        latest = config_list[-1]
                        
                        # Perform column matching
                        matched, unmatched, extra = ConfigColumnMatcher.find_matching_columns(
                            latest.used_columns,
                            new_dataset_columns
                        )
                        
                        # Migrate configuration
                        migrated, report = ConfigColumnMatcher.migrate_config(
                            latest.config,
                            matched,
                            new_dataset_columns
                        )
                        
                        total_matched += len(matched)
                        total_unmatched += len(unmatched)
                        
                        # Generate comprehensive report
                        load_reports[page_key] = {
                            "page_name": latest.page_name,
                            "tool_name": latest.tool_name,
                            "original_columns": latest.used_columns,
                            "new_columns": new_dataset_columns,
                            "column_matching": {
                                "matched": matched,
                                "unmatched": unmatched,
                                "extra_new": extra,
                                "match_count": len(matched),
                                "unmatched_count": len(unmatched)
                            },
                            "migration_report": report,
                            "migrated_config": migrated,
                            "status": "migrated" if len(matched) > 0 else "requires_review"
                        }
                
                result["page_configurations"] = load_reports
                result["load_reports"] = load_reports
                self.load_reports = load_reports
                
                config_count = len(self.page_configs.page_configs)
                if config_count > 0:
                    result["messages"].append(
                        f"✅ Loaded {config_count} page configuration(s) with smart column matching"
                    )
                
                # Add warnings if needed
                if total_unmatched > 0:
                    result["warnings"].append(
                        f"⚠️  Found {total_unmatched} column reference(s) not in new dataset. "
                        f"Review migration reports for details."
                    )
                
                if total_matched > 0:
                    result["messages"].append(
                        f"✨ Successfully matched {total_matched} column(s) from saved config to new dataset"
                    )
        
        except Exception as e:
            result["success"] = False
            result["errors"].append(f"❌ Error loading configuration: {str(e)}")
            import traceback
            result["errors"].append(traceback.format_exc())
        
        return result
    
    # =====================================================================
    # UTILITY METHODS
    # =====================================================================
    
    def save_database_profile(
        self,
        name: str,
        db_type: str,
        host: str,
        port: int,
        username: str,
        database: str,
        notes: str = ""
    ) -> bool:
        """
        Save a database connection profile.
        Password is NOT saved for security.
        """
        try:
            self.db_manager.create_profile(
                name=name,
                db_type=db_type,
                host=host,
                port=port,
                username=username,
                database=database,
                notes=notes
            )
            return True
        except Exception:
            return False
    
    def get_available_tool_inputs(
        self,
        current_step_id: str
    ) -> Dict[str, Dict]:
        """Get available tool outputs that can be used as input."""
        return self.tool_registry.list_available_outputs(
            exclude_step_id=current_step_id
        )
    
    def get_tool_input_data(
        self,
        input_step_id: Optional[str],
        main_df: Any
    ) -> Optional[Any]:
        """Get input data for a tool from previous tool output or main dataset."""
        if input_step_id is None:
            return main_df
        
        cached_data = self.tool_registry.get_output_data(input_step_id)
        if cached_data is not None:
            return cached_data
        
        return None
    
    def generate_configuration_report(self) -> Dict[str, Any]:
        """Generate comprehensive report of all saved configurations."""
        return {
            "database_connections": {
                "count": len(self.db_manager.profiles),
                "profiles": list(self.db_manager.profiles.keys())
            },
            "tool_outputs": {
                "count": len(self.tool_registry.outputs),
                "statistics": self.tool_registry.get_statistics()
            },
            "page_configurations": {
                "count": len(self.page_configs.page_configs),
                "pages": list(self.page_configs.page_configs.keys())
            },
            "load_reports": self.load_reports,
            "generated_at": datetime.now().isoformat()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize entire configuration system."""
        return {
            "database_connections": self.db_manager.to_dict(),
            "tool_output_registry": self.tool_registry.to_dict(),
            "page_configurations": self.page_configs.to_dict(),
            "serialized_at": datetime.now().isoformat()
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "EnhancedProjectConfigManager":
        """Deserialize configuration system."""
        manager = EnhancedProjectConfigManager()
        
        if "database_connections" in data:
            manager.db_manager = DatabaseConnectionManager.from_dict(
                data["database_connections"]
            )
        
        if "tool_output_registry" in data:
            manager.tool_registry = ToolOutputRegistry.from_dict(
                data["tool_output_registry"]
            )
        
        if "page_configurations" in data:
            manager.page_configs = PageConfigurationManager.from_dict(
                data["page_configurations"]
            )
        
        return manager


# =====================================================================
# INTEGRATION HELPER FUNCTIONS
# =====================================================================

def get_enhanced_config_manager() -> EnhancedProjectConfigManager:
    """Get or create the enhanced configuration manager."""
    if "enhanced_config_manager" not in st.session_state:
        manager = EnhancedProjectConfigManager()
        manager.initialize_session_state()
        st.session_state.enhanced_config_manager = manager
        return manager
    
    return st.session_state.enhanced_config_manager


def display_configuration_dashboard():
    """Display comprehensive configuration status dashboard."""
    manager = get_enhanced_config_manager()
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("📋 Configuration Dashboard")
    
    col1, col2, col3 = st.sidebar.columns(3)
    
    with col1:
        db_count = len(manager.db_manager.profiles)
        st.metric("🗄️ DB Profiles", db_count)
    
    with col2:
        tool_count = len(manager.tool_registry.outputs)
        st.metric("🔧 Tool Outputs", tool_count)
    
    with col3:
        config_count = len(manager.page_configs.page_configs)
        st.metric("📄 Configs", config_count)


def display_load_report(load_result: Dict[str, Any]):
    """Display user-friendly load report."""
    st.subheader("📊 Configuration Load Report", divider="orange")
    
    # Messages
    if load_result["messages"]:
        st.info("\n".join(load_result["messages"]))
    
    # Warnings
    if load_result["warnings"]:
        st.warning("\n".join(load_result["warnings"]))
    
    # Errors
    if load_result["errors"]:
        st.error("\n".join(load_result["errors"]))
    
    # Load Reports Detail
    if load_result["load_reports"]:
        st.write("---")
        st.subheader("Detailed Configuration Mappings")
        
        for page_key, report in load_result["load_reports"].items():
            with st.expander(f"📄 {page_key}", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "Matched Columns",
                        report["column_matching"]["match_count"]
                    )
                
                with col2:
                    st.metric(
                        "Unmatched Columns",
                        report["column_matching"]["unmatched_count"]
                    )
                
                with col3:
                    st.metric(
                        "Extra New Columns",
                        len(report["column_matching"]["extra_new"])
                    )
                
                # Show mapping details
                if report["column_matching"]["matched"]:
                    st.write("**Column Mappings:**")
                    for old_col, new_col in report["column_matching"]["matched"].items():
                        if old_col != new_col:
                            st.caption(f"  {old_col} → {new_col}")
                        else:
                            st.caption(f"  {old_col} (unchanged)")
