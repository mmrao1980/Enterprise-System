"""
UI Components for Configuration Management and Tool Chaining
Provides reusable Streamlit components for the new features.
"""

import streamlit as st
from typing import Dict, List, Optional, Any, Tuple
from tool_output_registry import ToolOutputRegistry
from database_connection_manager import DatabaseConnectionManager, DatabaseConnectionProfile


def render_tool_input_selector(
    registry: ToolOutputRegistry,
    current_step_id: str,
    default_input_step: Optional[str] = None,
    view_mode: str = "dropdown"  # "dropdown", "visual", or "both"
) -> Optional[str]:
    """
    Render UI for selecting which tool output to use as input.
    
    Args:
        registry: ToolOutputRegistry instance with available outputs
        current_step_id: ID of current step (to exclude from options)
        default_input_step: Previously selected input step
        view_mode: UI rendering mode
    
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

            selected = st.selectbox(
                "Select Input Data Source",
                options,
                index=0,
                key=f"input_selector_{current_step_id}"
            )

            if selected != "📊 Main Dataset":
                # Extract step_id from display text
                for step_id, data in available_outputs.items():
                    if step_id[:8] in selected:
                        st.caption(f"**Output Shape:** {data['output_shape']}")
                        st.caption(f"**Columns:** {', '.join(data['columns'][:5])}"
                                   f"{'...' if len(data['columns']) > 5 else ''}")
                        return step_id

        return None

    elif view_mode == "visual":
        # Visual connection mode with columns
        col1, col2, col3 = st.columns([1, 2, 1])

        with col1:
            st.write("**📥 Available Sources**")
            use_main = st.checkbox("Main Dataset", value=True, key=f"main_ds_{current_step_id}")

        with col2:
            st.write("**↓ Input Flow ↓**")

        with col3:
            st.write("**Current Tool**")
            st.write(f"🔧 {current_step_id[:8]}...")

        if not use_main and available_outputs:
            st.write("---")
            selected_output = st.radio(
                "Or select tool output:",
                options=list(available_outputs.keys()),
                format_func=lambda x: f"{available_outputs[x]['tool_name']} ({x[:8]}...)",
                key=f"visual_selector_{current_step_id}"
            )
            return selected_output

    return None


def render_db_connection_form(
    profile: Optional[DatabaseConnectionProfile] = None,
    mode: str = "create"  # "create" or "edit"
) -> Tuple[Dict, bool]:
    """
    Render database connection form.
    
    Returns:
        - config dict with connection details (NO password)
        - whether to save profile
    """
    st.subheader("🔌 Database Connection Configuration", divider="blue")

    col1, col2 = st.columns(2)

    with col1:
        db_type = st.selectbox(
            "Database Type",
            ["sqlserver", "postgresql", "mysql", "oracle", "sqlite"],
            index=0 if not profile else ["sqlserver", "postgresql", "mysql", "oracle", "sqlite"].index(profile.db_type),
            key="db_type_form"
        )

    if profile and mode == "edit":
        st.info(f"✏️ Editing profile: {profile.connection_id}")

    config = {"db_type": db_type}

    if db_type != "sqlite":
        with col1:
            config["host"] = st.text_input(
                "Host",
                value=profile.host if profile else "localhost",
                key="db_host_form"
            )
            config["user"] = st.text_input(
                "Username",
                value=profile.user if profile else "",
                key="db_user_form"
            )

        with col2:
            config["port"] = st.number_input(
                "Port",
                value=profile.port if profile and profile.port else 0,
                min_value=0,
                max_value=65535,
                key="db_port_form"
            )
            config["database"] = st.text_input(
                "Database / Service Name",
                value=profile.database if profile else "",
                key="db_name_form"
            )

        # PASSWORD FIELD - NEVER SAVED
        st.warning("⚠️ Password is NOT saved for security. You'll enter it during connection.")
        password = st.text_input(
            "Password (for connection test only)",
            type="password",
            key="db_password_form",
            help="Password is used only for testing connection and is never saved."
        )
        config["password"] = password

        # Query field
        st.subheader("SQL Query")
        config["query"] = st.text_area(
            "SQL Query",
            value=profile.query if profile else "SELECT * FROM table_name",
            height=150,
            key="db_query_form"
        )

    else:
        st.write("SQLite file upload would go here")

    # Save option
    st.markdown("---")
    save_profile = st.checkbox(
        "💾 Save this connection profile for future use (without password)",
        value=True,
        key="save_profile_form"
    )

    return config, save_profile


def render_saved_connections_panel(
    manager: DatabaseConnectionManager
) -> Optional[str]:
    """
    Render panel for loading saved database connections.
    
    Returns:
        Selected connection_id or None
    """
    profiles = manager.list_profiles()

    if not profiles:
        st.info("No saved database connections yet. Create one first!")
        return None

    st.subheader("📋 Saved Database Connections", divider="green")

    selected_id = st.selectbox(
        "Load saved connection",
        options=list(profiles.keys()),
        format_func=lambda x: f"{profiles[x]['db_type']} @ {profiles[x]['host']} "
                             f"({profiles[x]['connection_id'][:8]}...)",
        key="connection_selector"
    )

    if selected_id:
        profile_data = profiles[selected_id]

        with st.expander(f"📌 Connection Details: {selected_id[:12]}...", expanded=True):
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Type:** {profile_data['db_type']}")
                st.write(f"**Host:** {profile_data['host']}")
                st.write(f"**User:** {profile_data['user']}")

            with col2:
                st.write(f"**Port:** {profile_data['port']}")
                st.write(f"**Database:** {profile_data['database']}")
                if profile_data.get('schema_name'):
                    st.write(f"**Schema:** {profile_data['schema_name']}")

            if profile_data.get('query'):
                st.write("**Saved Query:**")
                st.code(profile_data['query'], language="sql")

            st.caption(f"Created: {profile_data['created_at'][:10]}")
            st.caption(f"Last used: {profile_data['last_used'][:10]}")

        return selected_id

    return None


def render_config_load_report(
    load_report: Dict[str, Any],
    show_details: bool = True
) -> None:
    """
    Render user-friendly report of configuration loading/migration.
    """
    st.subheader("📊 Configuration Load Report", divider="orange")

    report_cols = st.columns(4)

    with report_cols[0]:
        st.metric("Total Saved Columns", load_report["summary"]["total_saved_columns"])

    with report_cols[1]:
        st.metric("✅ Matched Columns", load_report["summary"]["matched_columns"],
                  delta=f"+{load_report['summary']['matched_columns']}")

    with report_cols[2]:
        st.metric("⚠️ Unmatched Columns", load_report["summary"]["unmatched_columns"],
                  delta=f"-{load_report['summary']['unmatched_columns']}")

    with report_cols[3]:
        st.metric("🆕 Extra Columns", load_report["summary"]["extra_columns"],
                  delta=f"+{load_report['summary']['extra_columns']}")

    st.markdown("---")
    st.info(f"📌 {load_report['message']}")

    if show_details and load_report["details"]:
        details = load_report["details"]

        if details.get("matched"):
            with st.expander("✅ Matched Columns (Reused)", expanded=False):
                for old, new in details["matched"].items():
                    if old == new:
                        st.success(f"✅ `{old}` (unchanged)")
                    else:
                        st.success(f"✅ `{old}` → `{new}` (remapped)")

        if details.get("unmatched"):
            with st.expander("⚠️ Unmatched Columns (Not Found)", expanded=False):
                for col in details["unmatched"]:
                    st.warning(f"❌ `{col}` - Not found in new dataset, removed from config")

        if details.get("extra"):
            with st.expander("🆕 New Columns Available", expanded=False):
                for col in details["extra"][:10]:  # Show first 10
                    st.info(f"➕ `{col}` - Available for use (not in saved config)")
                if len(details["extra"]) > 10:
                    st.caption(f"... and {len(details['extra']) - 10} more columns")


def render_all_saved_configurations(
    page_manager,
    db_manager: Optional[DatabaseConnectionManager] = None
) -> None:
    """
    Render comprehensive view of all saved configurations.
    """
    st.subheader("📁 All Saved Configurations", divider="rainbow")

    tab1, tab2, tab3 = st.tabs(
        ["🔧 Tool Configurations", "🗄️ Database Connections", "📋 Page Configurations"]
    )

    with tab1:
        st.write("Tool pipeline configurations will be displayed here")
        st.info("Currently 0 tool configurations saved. Configure tools and save project to populate.")

    with tab2:
        if db_manager:
            profiles = db_manager.list_profiles()
            if profiles:
                for conn_id, profile_data in profiles.items():
                    with st.expander(f"🔌 {profile_data['db_type']} - {profile_data['host']}", expanded=False):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Connection ID:** `{conn_id}`")
                            st.write(f"**Host:** {profile_data['host']}:{profile_data['port']}")
                            st.write(f"**User:** {profile_data['user']}")
                        with col2:
                            st.write(f"**Database:** {profile_data['database']}")
                            if profile_data.get('schema_name'):
                                st.write(f"**Schema:** {profile_data['schema_name']}")

                        if profile_data.get('query'):
                            st.write("**Query:**")
                            st.code(profile_data['query'], language="sql")

                        if st.button("🗑️ Delete", key=f"del_{conn_id}"):
                            db_manager.delete_profile(conn_id)
                            st.success("Connection deleted!")
                            st.rerun()
            else:
                st.info("No database connections saved yet.")
        else:
            st.warning("Database manager not initialized")

    with tab3:
        st.write("Page configuration details")
        st.info("Page-specific configurations (for Missing Checks, Duplicates, etc.) appear here.")
