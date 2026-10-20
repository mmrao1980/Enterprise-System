"""
Integration Guide: Enhanced Configuration System
Step-by-step instructions for integrating new configuration features into ai_data_quality_platform.py
"""

# =====================================================================
# INTEGRATION STEPS
# =====================================================================

# 1. ADD IMPORTS AT TOP OF ai_data_quality_platform.py
# Place after existing imports (around line 28-30):

"""
# Enhanced Configuration System
from enhanced_project_config import (
    get_enhanced_config_manager,
    display_configuration_dashboard
)
from enhanced_ui_components import (
    render_tool_input_selector,
    render_db_connection_form,
    render_saved_connections_panel,
    render_config_migration_report,
    render_configuration_status_panel,
    render_quick_save_info
)
"""

# 2. INITIALIZE CONFIGURATION SYSTEM IN SESSION STATE SETUP
# Place in the session state initialization section (around line 100-150):

"""
# Initialize Enhanced Configuration System
if "enhanced_config_manager" not in st.session_state:
    from enhanced_project_config import EnhancedProjectConfigManager
    config_manager = EnhancedProjectConfigManager()
    config_manager.initialize_session_state()
    st.session_state.enhanced_config_manager = config_manager
"""

# 3. UPDATE save_project() FUNCTION
# Replace the return statement around line 8766 with:

"""
# Before: return json.dumps(master_blueprint, indent=4, ensure_ascii=False, cls=CustomProjectEncoder)

# After: Enhance with configuration system
from enhanced_project_config import get_enhanced_config_manager
config_manager = get_enhanced_config_manager()
enhanced_blueprint = config_manager.enhance_project_blueprint(master_blueprint)

try:
    return json.dumps(enhanced_blueprint, indent=4, ensure_ascii=False, cls=CustomProjectEncoder)
except Exception:
    try:
        brute_force_project = {}
        for k, v in enhanced_blueprint.items():
            if isinstance(v, dict):
                brute_force_project[k] = {subkey: str(subval) for subkey, subval in v.items()}
            elif isinstance(v, list):
                brute_force_project[k] = [str(item) for item in v]
            else:
                brute_force_project[k] = str(v)
        return json.dumps(brute_force_project, indent=4)
    except Exception:
        return None
"""

# 4. UPDATE load_saved_project_blueprint() FUNCTION
# Add smart column matching after line 8913:

"""
# After loading home_config (line 8913):
# Add column matching logic:

if "main_df" in st.session_state and st.session_state.main_df is not None:
    new_dataset_columns = [str(c) for c in st.session_state.main_df.columns]
    
    # Use enhanced configuration loader
    from enhanced_project_config import get_enhanced_config_manager
    config_manager = get_enhanced_config_manager()
    
    load_result = config_manager.load_enhanced_blueprint(
        master_blueprint,
        new_dataset_columns
    )
    
    st.session_state.config_load_reports = load_result.get("load_reports", {})
    
    # Store messages for display
    if load_result.get("messages"):
        st.session_state.config_load_messages = load_result["messages"]
    if load_result.get("warnings"):
        st.session_state.config_load_warnings = load_result["warnings"]
"""

# 5. ADD UI DISPLAY FOR LOAD REPORTS
# In the home page, after data is loaded, show:

"""
# Display configuration load reports if they exist
if "config_load_messages" in st.session_state:
    for msg in st.session_state.config_load_messages:
        st.success(msg)
    del st.session_state.config_load_messages

if "config_load_warnings" in st.session_state:
    for warning in st.session_state.config_load_warnings:
        st.warning(warning)
    del st.session_state.config_load_warnings

# Show detailed reports
if "config_load_reports" in st.session_state and st.session_state.config_load_reports:
    from enhanced_ui_components import render_config_migration_report
    render_config_migration_report(st.session_state.config_load_reports)
"""

# 6. ADD DATABASE CONNECTION PROFILE SAVING
# In the home page database connection section:

"""
# When user connects to database and chooses to save profile:
if save_profile and config and "host" in config:
    config_manager = get_enhanced_config_manager()
    profile_name = config.get("profile_name", f"{config['db_type']}_{config['host']}")
    
    config_manager.save_database_profile(
        name=profile_name,
        db_type=config["db_type"],
        host=config.get("host", ""),
        port=config.get("port", 5432),
        username=config.get("username", ""),
        database=config.get("database", ""),
        notes=config.get("notes", "")
    )
    st.success(f"✅ Profile '{profile_name}' saved!")
"""

# 7. ADD TOOL OUTPUT REGISTRATION
# After each tool execution (e.g., in validation pages):

"""
# After a tool produces output (output_df is the result):
from enhanced_project_config import get_enhanced_config_manager

config_manager = get_enhanced_config_manager()
config_manager.register_tool_execution(
    step_id=f"tool_{tool_name}_{timestamp}",
    tool_name=tool_name,
    output_data=output_df,
    source_step_id=input_source  # None if from main dataset
)
"""

# 8. ADD TOOL INPUT SELECTOR FOR PIPELINE CHAINING
# In validation pages where you want to support chaining:

"""
# Before processing data in a validation tool:
from enhanced_project_config import get_enhanced_config_manager
from enhanced_ui_components import render_tool_input_selector

config_manager = get_enhanced_config_manager()

# Show input selector
input_source = render_tool_input_selector(
    registry=config_manager.tool_registry,
    current_step_id=current_tool_id,
    view_mode="dropdown"  # or "visual" or "both"
)

# Get the data to process
input_data = config_manager.get_tool_input_data(input_source, main_df)
"""

# 9. ADD CONFIGURATION STATUS TO SIDEBAR
# In the main navigation/sidebar section:

"""
# Display configuration status
from enhanced_ui_components import render_configuration_status_panel
render_configuration_status_panel()
"""

# 10. ADD SAVE INFORMATION DIALOG
# Before save dialog in home page:

"""
# Show what will be saved
from enhanced_ui_components import render_quick_save_info
render_quick_save_info()
"""

# =====================================================================
# EXAMPLE: COMPLETE VALIDATION PAGE INTEGRATION
# =====================================================================

"""
# In any validation page (e.g., Missing Checks):

def page_missing_checks():
    from enhanced_project_config import get_enhanced_config_manager
    from enhanced_ui_components import render_tool_input_selector
    
    st.title("Missing Values Check")
    
    # Get configuration manager
    config_manager = get_enhanced_config_manager()
    
    # Option 1: Select input source (tool output or main dataset)
    input_source = render_tool_input_selector(
        registry=config_manager.tool_registry,
        current_step_id="missing_check_tool",
        view_mode="dropdown"
    )
    
    # Get input data
    input_df = config_manager.get_tool_input_data(input_source, st.session_state.main_df)
    
    if input_df is None:
        st.error("No input data available")
        return
    
    # Configure tool
    st.subheader("Configuration")
    columns_to_check = st.multiselect("Columns to check", input_df.columns)
    
    # Process
    if st.button("Run Missing Check"):
        # Process data
        missing_report = check_missing_values(input_df, columns_to_check)
        
        # Register output for chaining
        config_manager.register_tool_execution(
            step_id="missing_check_step_001",
            tool_name="Missing Values Check",
            output_data=missing_report,
            source_step_id=input_source
        )
        
        # Save page configuration
        config_manager.capture_page_configuration(
            page_name="Missing Checks",
            tool_name="Missing Values Check",
            used_columns=columns_to_check
        )
        
        st.success("Check completed and saved!")
        st.dataframe(missing_report)
"""

# =====================================================================
# USAGE: ACCESSING SAVED CONFIGURATIONS
# =====================================================================

"""
# Get manager instance
config_manager = get_enhanced_config_manager()

# Access database connections
db_profiles = config_manager.db_manager.list_profiles()
profile = config_manager.db_manager.get_profile("my_postgres")

# Access tool outputs
tool_outputs = config_manager.tool_registry.list_available_outputs()
output_data = config_manager.tool_registry.get_output_data(step_id)

# Access page configs
page_config = config_manager.page_configs.get_latest_page_config("Missing Checks", "Missing Tool")

# Generate reports
config_report = config_manager.generate_configuration_report()
"""

# =====================================================================
# KEY FEATURES ENABLED BY INTEGRATION
# =====================================================================

"""
✅ TOOL OUTPUT CHAINING
   - Each tool can use output from previous tools as input
   - Visual dropdown for selecting input sources
   - Data flows through pipeline

✅ DATABASE PROFILE SAVING
   - Connection details saved without passwords
   - Quick reload of connections
   - Connection history and metadata

✅ PAGE CONFIGURATION PERSISTENCE
   - Each validation page settings saved separately
   - Configuration history tracked
   - Tool-specific configurations preserved

✅ SMART COLUMN MATCHING
   - When reopening project with new dataset:
   - Automatically matches columns (case-insensitive)
   - Shows what was matched/unmatched
   - Configuration intelligently updated
   - User-friendly migration report

✅ COMPLETE PROJECT SERIALIZATION
   - All configurations save together
   - Backward compatible with old projects
   - Passwords never stored
   - Easy export/import of workflows
"""

# =====================================================================
# BACKWARD COMPATIBILITY
# =====================================================================

"""
The enhanced system is fully backward compatible:
- Old projects load correctly
- Missing configuration data doesn't cause errors
- New features activate only when data exists
- Graceful degradation for missing modules
"""

# =====================================================================
# ERROR HANDLING
# =====================================================================

"""
All new components include comprehensive error handling:
- Missing imports handled gracefully
- Invalid data validated before use
- User-friendly error messages
- No data loss on errors
- Detailed logging for debugging
"""
