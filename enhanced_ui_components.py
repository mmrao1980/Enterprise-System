"""
Enhanced UI Components for Configuration Management and Tool Chaining
Provides Streamlit components for tool input selection, database profiles, and config management.
"""

import streamlit as st
from typing import Dict, List, Optional, Any, Tuple
from tool_output_registry import ToolOutputRegistry
from database_connection_manager import DatabaseConnectionManager, DatabaseConnectionProfile


def render_tool_input_selector(
    registry: ToolOutputRegistry,
    current_step_id: str,
    default_input_step: Optional[str] = None,
    view_mode: str = "dropdown"
) -> Optional[str]:
    """
    Render UI for selecting which tool output to use as input.
    
    Args:
        registry: ToolOutputRegistry with available outputs
        current_step_id: ID of current step (excluded from options)
        default_input_step: Previously selected input step
        view_mode: "dropdown", "visual", or "both"
    
    Returns:
        Selected step_id or None (for main dataset)
    """
    available_outputs = registry.list_available_outputs(
        exclude_step_id=current_step_id
    )
    
    if not available_outputs:
        st.info("📌 No previous tool outputs available. Using main dataset.")
        return None
    
    st.subheader("🔌 Input Source Selection", divider="blue")
    
    if view_mode in ["both", "dropdown"]:
        with st.expander("📋 Use Previous Tool Output", expanded=True):
            options = ["📊 Main Dataset"] + [
                f"🔧 {data['tool_name']} (Step: {step_id[:8]}...)"
                for step_id, data in available_outputs.items()
            ]
            
            default_index = 0
            if default_input_step and default_input_step in available_outputs:
                for idx, opt in enumerate(options):
                    if default_input_step[:8] in opt:
                        default_index = idx
                        break
            
            selected = st.selectbox(
                "Select Input Data Source",
                options,
                index=default_index,
                key=f"input_selector_{current_step_id}"
            )
            
            if selected != "📊 Main Dataset":
                for step_id, data in available_outputs.items():
                    if step_id[:8] in selected:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.caption(f"**Output Shape:** {data['output_shape']}")
                        with col2:
                            st.caption(f"**Execution Time:** {data.get('execution_time_ms', 0):.0f}ms")
                        
                        # Show columns
                        col_display = ", ".join(data['columns'][:5])
                        if len(data['columns']) > 5:
                            col_display += f"... ({len(data['columns'])} total)"
                        st.caption(f"**Columns:** {col_display}")
                        
                        return step_id
        
        return None
    
    elif view_mode == "visual":
        # Visual connection mode
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            st.write("**📥 Available Sources**")
            use_main = st.checkbox(
                "Main Dataset",
                value=default_input_step is None,
                key=f"main_ds_{current_step_id}"
            )
        
        with col2:
            st.write("**↓ Data Flow ↓**")
        
        with col3:
            st.write("**Current Step**")
            st.write(f"🔧 {current_step_id[:8]}...")
        
        if not use_main and available_outputs:
            st.write("---")
            selected_output = st.radio(
                "Or select tool output:",
                options=list(available_outputs.keys()),
                format_func=lambda x: (
                    f"{available_outputs[x]['tool_name']} ({x[:8]}...) "
                    f"→ {available_outputs[x]['output_shape']}"
                ),
                key=f"visual_selector_{current_step_id}"
            )
            return selected_output
        
        return None
    
    return None


def render_db_connection_form(
    profile: Optional[DatabaseConnectionProfile] = None,
    mode: str = "create"
) -> Tuple[Dict, bool]:
    """
    Render database connection form.
    Password field is shown only for testing, never saved.
    
    Returns:
        (config_dict, should_save_profile)
    """
    st.subheader("🔌 Database Connection Configuration", divider="blue")
    
    col1, col2 = st.columns(2)
    
    with col1:
        db_type = st.selectbox(
            "Database Type",
            ["postgresql", "mysql", "sqlserver", "oracle", "sqlite"],
            index=0 if not profile else ["postgresql", "mysql", "sqlserver", "oracle", "sqlite"].index(profile.db_type),
            key="db_type_form"
        )
    
    if profile and mode == "edit":
        st.info(f"✏️ Editing profile: {profile.name}")
    
    config = {"db_type": db_type}
    
    if db_type != "sqlite":
        with col1:
            config["host"] = st.text_input(
                "Host",
                value=profile.host if profile else "localhost",
                key="db_host_form"
            )
            config["username"] = st.text_input(
                "Username",
                value=profile.username if profile else "",
                key="db_user_form"
            )
        
        with col2:
            config["port"] = st.number_input(
                "Port",
                value=profile.port if profile and profile.port else 5432,
                min_value=0,
                max_value=65535,
                key="db_port_form"
            )
            config["database"] = st.text_input(
                "Database / Service Name",
                value=profile.database if profile else "",
                key="db_name_form"
            )
        
        # PASSWORD - NEVER SAVED
        st.warning("⚠️  **Password is NOT saved** for security. Re-enter when needed for connection.")
        config["password"] = st.text_input(
            "Password (test connection only)",
            type="password",
            key="db_password_form",
            help="Password is used only for testing and is never saved to project."
        )
        
        # SQL Query
        st.subheader("SQL Query")
        config["query"] = st.text_area(
            "SQL Query",
            value=profile.saved_queries.get("default", "SELECT * FROM table_name") if profile else "SELECT * FROM table_name",
            height=120,
            key="db_query_form",
            help="Query to execute against the database"
        )
    
    else:
        config["db_path"] = st.text_input(
            "SQLite File Path",
            value=profile.database if profile else "",
            key="db_path_form",
            help="Path to SQLite database file"
        )
    
    # Save profile option
    st.markdown("---")
    save_profile = st.checkbox(
        "💾 Save this connection profile for future use (password NOT saved)",
        value=True,
        key="save_profile_checkbox"
    )
    
    return config, save_profile


def render_saved_connections_panel(
    manager: DatabaseConnectionManager
) -> Optional[str]:
    """
    Render panel to select from saved database connections.
    
    Returns:
        Selected profile name or None
    """
    profiles = manager.list_profiles()
    
    if not profiles:
        st.info("📌 No saved database connections yet. Create one first!")
        return None
    
    st.subheader("📋 Saved Database Connections", divider="green")
    
    profile_names = profiles
    selected_name = st.selectbox(
        "Load saved connection",
        options=profile_names,
        format_func=lambda x: f"{manager.get_profile(x).db_type} @ {manager.get_profile(x).host}",
        key="connection_selector"
    )
    
    if selected_name:
        profile = manager.get_profile(selected_name)
        
        with st.expander(f"📌 Details: {profile.name}", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Type:** {profile.db_type}")
                st.write(f"**Host:** {profile.host}")
                st.write(f"**Username:** {profile.username}")
            
            with col2:
                st.write(f"**Port:** {profile.port}")
                st.write(f"**Database:** {profile.database}")
                if profile.notes:
                    st.write(f"**Notes:** {profile.notes}")
            
            # Saved queries
            if profile.saved_queries:
                st.write("**Saved Queries:**")
                for query_name, query_text in profile.saved_queries.items():
                    st.caption(f"📝 {query_name}")
                    st.code(query_text, language="sql")
            
            st.caption(f"Created: {profile.created_at[:10]}")
            st.caption(f"Last used: {profile.last_used[:10]}")
        
        return selected_name
    
    return None


def render_config_migration_report(
    load_reports: Dict[str, Dict]
) -> None:
    """
    Render detailed migration report for configuration loading.
    Shows what columns were matched, unmatched, and added.
    """
    if not load_reports:
        st.info("No configuration migration data to display.")
        return
    
    st.subheader("📊 Configuration Migration Report", divider="orange")
    
    # Overview metrics
    total_matched = 0
    total_unmatched = 0
    
    for report in load_reports.values():
        matching = report.get("column_matching", {})
        total_matched += matching.get("match_count", 0)
        total_unmatched += matching.get("unmatched_count", 0)
    
    metric_cols = st.columns(3)
    with metric_cols[0]:
        st.metric("✅ Total Matched Columns", total_matched)
    with metric_cols[1]:
        st.metric("⚠️  Unmatched Columns", total_unmatched)
    with metric_cols[2]:
        st.metric("📄 Configurations Loaded", len(load_reports))
    
    st.write("---")
    
    # Detailed reports
    st.write("**Detailed Mappings:**")
    for page_key, report in load_reports.items():
        with st.expander(f"📄 {page_key} ({report['tool_name']})", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Matched",
                    report["column_matching"]["match_count"],
                    delta=None
                )
            
            with col2:
                st.metric(
                    "Unmatched",
                    report["column_matching"]["unmatched_count"],
                    delta=None,
                    delta_color="inverse"
                )
            
            with col3:
                st.metric(
                    "New Columns Available",
                    len(report["column_matching"]["extra_new"]),
                    delta=None
                )
            
            # Show mappings
            if report["column_matching"]["matched"]:
                st.write("**Column Remappings:**")
                for old_col, new_col in report["column_matching"]["matched"].items():
                    if old_col != new_col:
                        st.caption(f"  🔄 {old_col} → {new_col}")
                    else:
                        st.caption(f"  ✓ {old_col} (unchanged)")
            
            # Show unmatched
            if report["column_matching"]["unmatched"]:
                st.warning("**Unmatched Columns (removed from config):**")
                for col in report["column_matching"]["unmatched"]:
                    st.caption(f"  ✗ {col}")
            
            # Show extra
            if report["column_matching"]["extra_new"]:
                st.info("**New Columns Available in Dataset:**")
                for col in report["column_matching"]["extra_new"]:
                    st.caption(f"  + {col}")


def render_tool_pipeline_visualization(
    registry: ToolOutputRegistry
) -> None:
    """
    Render visual representation of tool pipeline and data flow.
    """
    pipeline_data = registry.get_pipeline_visualization_data()
    
    if pipeline_data["total_outputs"] == 0:
        st.info("No tool outputs in pipeline yet.")
        return
    
    st.subheader("🔄 Tool Pipeline Visualization", divider="blue")
    
    # Create a text-based visualization
    col1, col2 = st.columns([2, 1])
    
    with col1:
        pipeline_text = "📊 Main Dataset\n"
        
        for edge in pipeline_data["edges"]:
            if edge["from"] == "main_dataset":
                pipeline_text += f"  ↓ ({edge['label']})\n"
        
        for node in pipeline_data["nodes"]:
            if node["type"] == "tool_output":
                pipeline_text += f"{node['label']}\n"
                
                # Find outgoing edges
                for edge in pipeline_data["edges"]:
                    if edge["from"] == node["id"]:
                        pipeline_text += f"  ↓ ({edge['label']})\n"
        
        st.code(pipeline_text)
    
    with col2:
        stats = registry.get_statistics()
        st.metric("Total Outputs", stats["total_outputs"])
        st.metric("Total Rows Processed", f"{stats['total_rows']:,}")
        st.metric("Tools Used", len(stats["tools_used"]))


def render_configuration_status_panel() -> None:
    """
    Render sidebar status panel showing configuration health.
    """
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Configuration Status")
    
    from enhanced_project_config import get_enhanced_config_manager
    manager = get_enhanced_config_manager()
    
    col1, col2, col3 = st.sidebar.columns(3)
    
    with col1:
        db_count = len(manager.db_manager.profiles)
        st.metric(
            "Databases",
            db_count,
            help="Saved connection profiles"
        )
    
    with col2:
        tool_count = len(manager.tool_registry.outputs)
        st.metric(
            "Tools",
            tool_count,
            help="Registered tool outputs"
        )
    
    with col3:
        config_count = len(manager.page_configs.page_configs)
        st.metric(
            "Pages",
            config_count,
            help="Saved page configurations"
        )


def render_quick_save_info() -> None:
    """
    Render quick info about what will be saved.
    """
    from enhanced_project_config import get_enhanced_config_manager
    manager = get_enhanced_config_manager()
    
    st.info(
        f"💾 **Save will include:**\n"
        f"  • {len(manager.db_manager.profiles)} database connection profile(s)\n"
        f"  • {len(manager.tool_registry.outputs)} tool output(s)\n"
        f"  • {len(manager.page_configs.page_configs)} page configuration(s)"
    )
