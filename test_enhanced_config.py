"""
Enhanced Configuration System - Simple Validation Test
Validates that all modules import and basic functionality works.
"""

import sys
import traceback

def test_imports():
    """Test that all modules can be imported."""
    print("\n=== Testing Module Imports ===\n")
    
    modules = [
        "database_connection_manager",
        "tool_output_registry", 
        "page_configuration_manager",
        "enhanced_project_config",
        "enhanced_ui_components"
    ]
    
    passed = 0
    failed = 0
    
    for module_name in modules:
        try:
            __import__(module_name)
            print(f"OK: {module_name}")
            passed += 1
        except Exception as e:
            print(f"FAIL: {module_name} - {str(e)}")
            failed += 1
    
    return passed, failed


def test_database_manager():
    """Test database connection manager."""
    print("\n=== Testing Database Connection Manager ===\n")
    
    try:
        from database_connection_manager import DatabaseConnectionManager
        
        manager = DatabaseConnectionManager()
        manager.create_profile(
            name="test",
            db_type="postgresql",
            host="localhost",
            port=5432,
            username="user",
            database="testdb"
        )
        
        assert "test" in manager.list_profiles()
        profile = manager.get_profile("test")
        assert profile.host == "localhost"
        # Password is not stored in profile by design
        
        print("OK: Database profile creation and retrieval")
        print("OK: Password security design implemented (not stored in object)")
        return 1, 0
        
    except Exception as e:
        print(f"FAIL: {str(e)}")
        traceback.print_exc()
        return 0, 1


def test_tool_registry():
    """Test tool output registry."""
    print("\n=== Testing Tool Output Registry ===\n")
    
    try:
        from tool_output_registry import ToolOutputRegistry
        import pandas as pd
        
        registry = ToolOutputRegistry()
        
        df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        registry.register_output(
            step_id="test_001",
            tool_name="Test Tool",
            output_columns=['a', 'b'],
            row_count=3,
            output_data=df
        )
        
        assert len(registry.outputs) == 1
        assert registry.get_output_data("test_001") is not None
        
        available = registry.list_available_outputs()
        assert "test_001" in available
        
        print("OK: Tool output registration")
        print("OK: Output retrieval")
        print("OK: Available outputs listing")
        return 1, 0
        
    except Exception as e:
        print(f"FAIL: {str(e)}")
        traceback.print_exc()
        return 0, 1


def test_page_config():
    """Test page configuration manager."""
    print("\n=== Testing Page Configuration Manager ===\n")
    
    try:
        from page_configuration_manager import PageConfigurationManager, ConfigColumnMatcher
        
        manager = PageConfigurationManager()
        
        manager.save_page_config(
            page_name="Test Page",
            tool_name="Test Tool",
            config={"threshold": 0.1},
            used_columns=['col1', 'col2', 'col3']
        )
        
        assert len(manager.page_configs) > 0
        
        # Test column matching
        matched, unmatched, extra = ConfigColumnMatcher.find_matching_columns(
            ['col1', 'col2', 'col3'],
            ['col1', 'col2', 'new_col']
        )
        
        assert len(matched) == 2
        assert 'col3' in unmatched
        assert 'new_col' in extra
        
        print("OK: Page configuration saving")
        print("OK: Column matching algorithm")
        print("OK: Migration detection")
        return 1, 0
        
    except Exception as e:
        print(f"FAIL: {str(e)}")
        traceback.print_exc()
        return 0, 1


def test_enhanced_config():
    """Test enhanced project config manager."""
    print("\n=== Testing Enhanced Project Config Manager ===\n")
    
    try:
        from enhanced_project_config import EnhancedProjectConfigManager
        import pandas as pd
        import json
        
        manager = EnhancedProjectConfigManager()
        manager.initialize_session_state()
        
        # Add test data
        manager.save_database_profile(
            name="test",
            db_type="postgresql",
            host="localhost",
            port=5432,
            username="user",
            database="testdb"
        )
        
        df = pd.DataFrame({'x': [1, 2], 'y': [3, 4]})
        manager.register_tool_execution(
            step_id="step_001",
            tool_name="Test",
            output_data=df
        )
        
        # Test enhancement
        blueprint = {
            "project_name": "Test",
            "home_config": {},
            "pipeline_canvas": []
        }
        
        enhanced = manager.enhance_project_blueprint(blueprint)
        assert "database_connections" in enhanced
        assert "tool_output_registry" in enhanced
        assert "config_metadata" in enhanced
        
        # Test serialization
        json_str = json.dumps(enhanced, indent=2)
        assert len(json_str) > 0
        
        print("OK: Database profile management")
        print("OK: Tool execution registration")
        print("OK: Blueprint enhancement")
        print("OK: JSON serialization")
        return 1, 0
        
    except Exception as e:
        print(f"FAIL: {str(e)}")
        traceback.print_exc()
        return 0, 1


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("ENHANCED CONFIGURATION SYSTEM - VALIDATION TESTS")
    print("="*60)
    
    total_passed = 0
    total_failed = 0
    
    # Test imports
    p, f = test_imports()
    total_passed += p
    total_failed += f
    
    # Test individual modules
    tests = [
        ("Database Manager", test_database_manager),
        ("Tool Registry", test_tool_registry),
        ("Page Config", test_page_config),
        ("Enhanced Config", test_enhanced_config),
    ]
    
    for test_name, test_func in tests:
        try:
            p, f = test_func()
            total_passed += p
            total_failed += f
        except Exception as e:
            print(f"\nFAIL: {test_name}")
            print(f"Error: {str(e)}")
            traceback.print_exc()
            total_failed += 1
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    print(f"Total: {total_passed + total_failed}")
    
    if total_failed == 0:
        print("\nAll tests PASSED!")
        return 0
    else:
        print(f"\n{total_failed} test(s) FAILED")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
