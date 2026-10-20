"""
PRACTICAL EXAMPLES: Using the New Configuration System

This file demonstrates how to use the new configuration management system
in real-world scenarios.
"""

import streamlit as st
import pandas as pd
from config_integration import get_config_manager


# =====================================================================
# EXAMPLE 1: Save Database Connection After Successful Connection
# =====================================================================
def example_save_db_connection():
    """
    Example: Save a database connection profile after user connects.
    Call this after successful database connection.
    """
    config_manager = get_config_manager()

    # Connection details from form
    db_config = {
        "db_type": "postgresql",
        "host": "prod-db.example.com",
        "port": 5432,
        "user": "data_analyst",
        "database": "analytics_db",
        "query": "SELECT * FROM customer_data LIMIT 10000"
    }

    # Save connection profile (password is NEVER included)
    connection_id = config_manager.db_manager.create_profile(
        db_type=db_config["db_type"],
        host=db_config["host"],
        port=db_config["port"],
        user=db_config["user"],
        database=db_config["database"],
        query=db_config["query"],
        schema_name="public"
    )

    st.success(f"✅ Connection saved! Profile ID: {connection_id}")


# =====================================================================
# EXAMPLE 2: Load Saved Connection and Auto-Populate Form
# =====================================================================
def example_load_saved_connection():
    """
    Example: Load a saved connection and populate form fields.
    User still must enter password for security.
    """
    config_manager = get_config_manager()

    # Get saved connection
    all_profiles = config_manager.db_manager.list_profiles()

    if all_profiles:
        connection_id = list(all_profiles.keys())[0]
        profile = config_manager.db_manager.get_profile(connection_id)

        st.write(f"Loaded connection: {profile.db_type}")
        st.write(f"Host: {profile.host}:{profile.port}")
        st.write(f"User: {profile.user}")
        st.write(f"Database: {profile.database}")

        # User must re-enter password
        password = st.text_input("Enter password:", type="password")

        # Pre-fill query
        query = st.text_area("Query:", value=profile.query)


# =====================================================================
# EXAMPLE 3: Register Tool Output After Execution
# =====================================================================
def example_register_tool_output():
    """
    Example: Register tool output after successful tool execution.
    This enables downstream tools to use this output as input.
    """
    config_manager = get_config_manager()

    # After a tool executes successfully
    result_df = pd.DataFrame({
        "id": [1, 2, 3],
        "value": [100, 200, 300],
        "status": ["active", "inactive", "active"]
    })

    # Register the output
    config_manager.register_tool_output_from_session(
        step_id="sampling_tool_step_1",
        tool_name="Sampling Tool",
        output_data=result_df,
        source_step_id=None  # This tool uses main dataset
    )

    st.success("✅ Tool output registered for downstream chaining")


# =====================================================================
# EXAMPLE 4: Use Previous Tool Output as Input
# =====================================================================
def example_use_tool_output_as_input():
    """
    Example: Use output from a previous tool as input to current tool.
    """
    config_manager = get_config_manager()

    # Show available upstream outputs
    available = config_manager.tool_registry.list_available_outputs(
        exclude_step_id="current_tool"
    )

    if available:
        selected_step = st.selectbox(
            "Use output from:",
            options=list(available.keys()),
            format_func=lambda x: available[x]["tool_name"]
        )

        # Get the input data
        input_data = config_manager.tool_registry.get_output_data(selected_step)

        if input_data is not None:
            st.write(f"Using {len(input_data)} rows from {available[selected_step]['tool_name']}")
            # Now process input_data with current tool
        else:
            st.warning("Data not cached. Will re-execute upstream tools...")


# =====================================================================
# EXAMPLE 5: Save Page Configuration for Missing Checks
# =====================================================================
def example_save_page_configuration():
    """
    Example: Save configuration for Missing Checks page.
    Call this when user finalizes their validation settings.
    """
    config_manager = get_config_manager()

    # Configuration that user created
    page_config = {
        "key_cols": ["customer_id", "order_id"],
        "check_cols": ["email", "phone", "address"],
        "export_format": "excel",
        "skip_all_nulls": False
    }

    used_columns = ["customer_id", "order_id", "email", "phone", "address"]

    # Save it
    config_manager.save_page_configuration_from_session(
        page_name="Missing Checks",
        tool_name="Missing Data Validator"
    )

    st.success("✅ Page configuration saved for future projects")


# =====================================================================
# EXAMPLE 6: Smart Column Matching on Project Reload
# =====================================================================
def example_smart_column_matching():
    """
    Example: When loading project with new dataset, intelligently match columns.
    """
    config_manager = get_config_manager()

    # Old project columns (from saved config)
    saved_columns = ["customer_id", "email", "phone", "address", "deleted_flag"]

    # New dataset columns
    new_columns = ["customer_id", "email", "contact_phone", "mailing_address", "city"]

    # Find matches
    from page_configuration_manager import ConfigColumnMatcher

    matched, unmatched, extra = ConfigColumnMatcher.find_matching_columns(
        saved_columns,
        new_columns
    )

    st.write("**Column Matching Report:**")
    st.write(f"✅ Matched: {matched}")
    st.write(f"❌ Unmatched (removed): {unmatched}")
    st.write(f"🆕 Extra (available): {extra}")

    # Migrate config to new columns
    old_config = {
        "key_cols": ["customer_id"],
        "check_cols": ["email", "phone", "address", "deleted_flag"]
    }

    migrated_config, report = ConfigColumnMatcher.migrate_config(
        old_config,
        matched,
        new_columns
    )

    st.write("**Migrated Configuration:**")
    st.write(migrated_config)


# =====================================================================
# EXAMPLE 7: Create Enhanced Project Blueprint and Save
# =====================================================================
def example_save_enhanced_project():
    """
    Example: Save project with all enhanced configuration data.
    """
    config_manager = get_config_manager()

    # Original blueprint from save_project()
    original_blueprint = {
        "home_config": {
            "project_name": "My Analysis",
            "selected_columns": ["col1", "col2"]
        },
        "pipeline_canvas": [
            {"tool": "Sampling Tool", "config": {"n": 1000}}
        ]
    }

    # Enhance it with new config data
    enhanced = config_manager.generate_enhanced_project_blueprint(
        original_blueprint
    )

    st.write("**Enhanced blueprint includes:**")
    st.write(f"- Database connections: {len(enhanced.get('database_connections', {}))}")
    st.write(f"- Tool outputs: {len(enhanced.get('tool_output_registry', {}))}")
    st.write(f"- Page configs: {len(enhanced.get('page_configurations', {}))}")


# =====================================================================
# EXAMPLE 8: Load Project with Intelligent Config Migration
# =====================================================================
def example_load_project_with_migration():
    """
    Example: Load saved project with new dataset and intelligent config migration.
    """
    config_manager = get_config_manager()

    # Project loaded from JSON file
    saved_project = {
        "home_config": {"project_name": "Previous Project"},
        "pipeline_canvas": [],
        "database_connections": {},
        "tool_output_registry": {},
        "page_configurations": {}
    }

    # New dataset columns
    new_columns = ["id", "name", "email", "created_date", "updated_date"]

    # Load with intelligent migration
    result = config_manager.load_enhanced_project_blueprint(
        saved_project,
        new_columns
    )

    if result["success"]:
        st.success("✅ Project loaded successfully!")

        for msg in result["messages"]:
            st.info(msg)

        for warning in result["warnings"]:
            st.warning(warning)

        # Display migration details
        if result["load_reports"]:
            for page_key, report in result["load_reports"].items():
                st.write(f"**{page_key}:**")
                st.write(f"- Matched: {len(report.get('migration_report', {}).get('analysis', {}).get('matched_columns', {}))}")
                st.write(f"- Unmatched: {len(report.get('migration_report', {}).get('analysis', {}).get('unmatched_saved_columns', []))}")


# =====================================================================
# EXAMPLE 9: Display All Saved Configurations
# =====================================================================
def example_display_configurations():
    """
    Example: Display all saved configurations in UI.
    """
    config_manager = get_config_manager()

    st.subheader("📊 Project Configurations")

    # Database Connections
    st.write("**Database Connections:**")
    db_profiles = config_manager.db_manager.list_profiles()
    for conn_id, profile in db_profiles.items():
        st.write(f"- {profile['db_type']} @ {profile['host']} ({conn_id[:12]}...)")

    # Tool Registry
    st.write("**Available Tool Outputs:**")
    outputs = config_manager.tool_registry.list_available_outputs()
    for step_id, output in outputs.items():
        st.write(f"- {output['tool_name']}: {output['output_shape']}")

    # Page Configurations
    st.write("**Page Configurations:**")
    page_configs = config_manager.page_configs.page_configs
    for page_key, configs in page_configs.items():
        st.write(f"- {page_key}: {len(configs)} version(s)")


# =====================================================================
# EXAMPLE 10: Full Workflow - From Start to Save and Reload
# =====================================================================
def example_full_workflow():
    """
    Example: Complete workflow from project creation to save and reload.
    """
    config_manager = get_config_manager()

    st.write("### Full Workflow Example")

    # Step 1: Connect to database
    st.write("**Step 1: Connect to Database**")
    connection_id = config_manager.db_manager.create_profile(
        db_type="postgresql",
        host="localhost",
        port=5432,
        user="analyst",
        database="analytics",
        query="SELECT * FROM sales LIMIT 5000"
    )
    st.write(f"✅ Connected: {connection_id}")

    # Step 2: Execute first tool (Sampling)
    st.write("**Step 2: Execute Sampling Tool**")
    sample_data = pd.DataFrame({
        "id": [1, 2, 3],
        "amount": [100, 200, 300]
    })
    config_manager.register_tool_output_from_session(
        step_id="sampling_1",
        tool_name="Sampling Tool",
        output_data=sample_data
    )
    st.write(f"✅ Sampled {len(sample_data)} rows")

    # Step 3: Execute second tool using output from first
    st.write("**Step 3: Execute Sorting Tool using Sampling output**")
    sorted_data = sample_data.sort_values("amount")
    config_manager.register_tool_output_from_session(
        step_id="sorting_1",
        tool_name="Sort Tool",
        output_data=sorted_data,
        source_step_id="sampling_1"
    )
    st.write(f"✅ Sorted {len(sorted_data)} rows")

    # Step 4: Save project
    st.write("**Step 4: Save Project**")
    st.write(f"✅ Project saved with {len(config_manager.db_manager.profiles)} DB connections")
    st.write(f"✅ Project saved with {len(config_manager.tool_registry.outputs)} tool outputs")

    # Step 5: Reload project with new dataset
    st.write("**Step 5: Reload Project with New Dataset**")
    new_columns = ["id", "amount", "customer_id", "date"]
    result = config_manager.load_enhanced_project_blueprint(
        {},  # Empty blueprint for demo
        new_columns
    )
    st.write(f"✅ Project reloaded and configured for {len(new_columns)} columns")
