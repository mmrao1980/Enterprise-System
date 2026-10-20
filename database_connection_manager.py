"""
Database Connection Manager
Manages database connection profiles securely without storing passwords.
Enables connection reuse and profile management.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json
from dataclasses import dataclass, field


@dataclass
class DatabaseConnectionProfile:
    """Represents a database connection profile without password."""
    
    name: str
    db_type: str  # postgresql, mysql, oracle, mssql, sqlite
    host: str
    port: int
    username: str
    database: str
    saved_queries: Dict[str, str] = field(default_factory=dict)
    created_at: str = ""
    last_used: str = ""
    notes: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.last_used:
            self.last_used = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Serialize profile without password."""
        return {
            "name": self.name,
            "db_type": self.db_type,
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "database": self.database,
            "saved_queries": dict(self.saved_queries),
            "created_at": self.created_at,
            "last_used": self.last_used,
            "notes": self.notes
        }
    
    @staticmethod
    def from_dict(data: Dict) -> "DatabaseConnectionProfile":
        """Deserialize profile from dict."""
        return DatabaseConnectionProfile(
            name=data.get("name", ""),
            db_type=data.get("db_type", ""),
            host=data.get("host", ""),
            port=data.get("port", 5432),
            username=data.get("username", ""),
            database=data.get("database", ""),
            saved_queries=data.get("saved_queries", {}),
            created_at=data.get("created_at", ""),
            last_used=data.get("last_used", ""),
            notes=data.get("notes", "")
        )


class DatabaseConnectionManager:
    """Manages database connection profiles securely."""
    
    def __init__(self):
        self.profiles: Dict[str, DatabaseConnectionProfile] = {}
    
    def create_profile(
        self,
        name: str,
        db_type: str,
        host: str,
        port: int,
        username: str,
        database: str,
        notes: str = ""
    ) -> DatabaseConnectionProfile:
        """
        Create a new connection profile (password NOT stored).
        
        Args:
            name: Profile name for identification
            db_type: Database type (postgresql, mysql, oracle, mssql, sqlite)
            host: Database host address
            port: Database port number
            username: Database username
            database: Database name
            notes: Optional notes about the connection
        
        Returns:
            Created DatabaseConnectionProfile
        """
        profile = DatabaseConnectionProfile(
            name=name,
            db_type=db_type,
            host=host,
            port=port,
            username=username,
            database=database,
            notes=notes
        )
        self.profiles[name] = profile
        return profile
    
    def get_profile(self, name: str) -> Optional[DatabaseConnectionProfile]:
        """Get connection profile by name."""
        return self.profiles.get(name)
    
    def list_profiles(self) -> List[str]:
        """List all profile names."""
        return list(self.profiles.keys())
    
    def update_profile(
        self,
        old_name: str,
        new_name: str = None,
        **kwargs
    ) -> Optional[DatabaseConnectionProfile]:
        """
        Update connection profile.
        Allows renaming and updating non-password fields.
        """
        if old_name not in self.profiles:
            return None
        
        profile = self.profiles[old_name]
        
        # Update fields if provided
        if "host" in kwargs:
            profile.host = kwargs["host"]
        if "port" in kwargs:
            profile.port = kwargs["port"]
        if "username" in kwargs:
            profile.username = kwargs["username"]
        if "database" in kwargs:
            profile.database = kwargs["database"]
        if "notes" in kwargs:
            profile.notes = kwargs["notes"]
        if "db_type" in kwargs:
            profile.db_type = kwargs["db_type"]
        
        # Handle rename
        if new_name and new_name != old_name:
            profile.name = new_name
            self.profiles[new_name] = profile
            del self.profiles[old_name]
        
        profile.last_used = datetime.now().isoformat()
        return profile
    
    def save_query(
        self,
        profile_name: str,
        query_name: str,
        query_text: str
    ) -> bool:
        """Save a query to a connection profile."""
        if profile_name not in self.profiles:
            return False
        
        self.profiles[profile_name].saved_queries[query_name] = query_text
        return True
    
    def get_query(self, profile_name: str, query_name: str) -> Optional[str]:
        """Get a saved query from a profile."""
        if profile_name in self.profiles:
            return self.profiles[profile_name].saved_queries.get(query_name)
        return None
    
    def list_queries(self, profile_name: str) -> Dict[str, str]:
        """List all saved queries for a profile."""
        if profile_name in self.profiles:
            return dict(self.profiles[profile_name].saved_queries)
        return {}
    
    def delete_profile(self, name: str) -> bool:
        """Delete a connection profile."""
        if name in self.profiles:
            del self.profiles[name]
            return True
        return False
    
    def delete_query(self, profile_name: str, query_name: str) -> bool:
        """Delete a saved query."""
        if profile_name in self.profiles:
            if query_name in self.profiles[profile_name].saved_queries:
                del self.profiles[profile_name].saved_queries[query_name]
                return True
        return False
    
    def to_dict(self) -> Dict:
        """Serialize all profiles (no passwords)."""
        return {
            name: profile.to_dict()
            for name, profile in self.profiles.items()
        }
    
    @staticmethod
    def from_dict(data: Dict) -> "DatabaseConnectionManager":
        """Deserialize profiles from dict."""
        manager = DatabaseConnectionManager()
        for name, profile_data in data.items():
            manager.profiles[name] = DatabaseConnectionProfile.from_dict(profile_data)
        return manager
    
    def validate_connection_params(
        self,
        db_type: str,
        host: str,
        port: int,
        username: str,
        database: str
    ) -> Tuple[bool, str]:
        """
        Validate connection parameters before attempting connection.
        
        Returns:
            (is_valid, error_message)
        """
        if not db_type:
            return False, "Database type is required"
        
        if db_type != "sqlite" and not host:
            return False, "Host is required for this database type"
        
        if db_type != "sqlite" and not port:
            return False, "Port is required for this database type"
        
        if db_type != "sqlite" and not username:
            return False, "Username is required for this database type"
        
        if not database:
            return False, "Database name is required"
        
        return True, ""


    def save_default_query(
        self,
        profile_name: str,
        query_text: str
    ) -> bool:
        """Persist the primary reusable query for a profile."""
        return self.save_query(profile_name, "default", query_text)
