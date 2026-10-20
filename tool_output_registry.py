"""
Tool Output Registry
Manages tool outputs for chaining, enabling output from one tool to be used as input to another.
No data overlap - each tool works with selected output independently.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import pandas as pd
from dataclasses import dataclass, field


@dataclass
class ToolOutput:
    """Represents output from a tool execution."""
    
    step_id: str  # Unique identifier for this step
    tool_name: str  # e.g., "Missing Tool", "Duplicate Tool"
    output_columns: List[str]  # Columns in the output
    row_count: int  # Number of rows
    source_step_id: Optional[str] = None  # If input from another tool, its step_id
    execution_time_ms: float = 0.0  # Execution time
    created_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)  # Extra metadata
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Serialize output metadata (not the data itself)."""
        return {
            "step_id": self.step_id,
            "tool_name": self.tool_name,
            "output_columns": list(self.output_columns),
            "row_count": self.row_count,
            "source_step_id": self.source_step_id,
            "execution_time_ms": self.execution_time_ms,
            "created_at": self.created_at,
            "metadata": dict(self.metadata)
        }
    
    @staticmethod
    def from_dict(data: Dict) -> "ToolOutput":
        """Deserialize output metadata."""
        return ToolOutput(
            step_id=data.get("step_id", ""),
            tool_name=data.get("tool_name", ""),
            output_columns=data.get("output_columns", []),
            row_count=data.get("row_count", 0),
            source_step_id=data.get("source_step_id"),
            execution_time_ms=data.get("execution_time_ms", 0.0),
            created_at=data.get("created_at", ""),
            metadata=data.get("metadata", {})
        )


class ToolOutputRegistry:
    """
    Manages tool outputs for pipeline chaining.
    
    Key Features:
    - Track outputs from each tool execution
    - Enable using one tool's output as another tool's input
    - No data overlap - each tool has independent data access
    - Visual UI for selecting tool inputs
    """
    
    def __init__(self):
        self.outputs: Dict[str, ToolOutput] = {}  # step_id -> ToolOutput metadata
        self.data_cache: Dict[str, Any] = {}  # step_id -> actual output data
    
    def register_output(
        self,
        step_id: str,
        tool_name: str,
        output_columns: List[str],
        row_count: int,
        source_step_id: Optional[str] = None,
        output_data: Optional[Any] = None,
        execution_time_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ToolOutput:
        """
        Register a tool output.
        
        Args:
            step_id: Unique identifier for this execution step
            tool_name: Name of the tool that produced this output
            output_columns: List of column names in output
            row_count: Number of rows in output
            source_step_id: If this tool used another tool's output as input
            output_data: The actual output data (stored in cache)
            execution_time_ms: How long the tool took to execute
            metadata: Additional metadata about the output
        
        Returns:
            ToolOutput metadata object
        """
        tool_output = ToolOutput(
            step_id=step_id,
            tool_name=tool_name,
            output_columns=output_columns,
            row_count=row_count,
            source_step_id=source_step_id,
            execution_time_ms=execution_time_ms,
            metadata=metadata or {}
        )
        
        self.outputs[step_id] = tool_output
        
        # Cache the actual data if provided
        if output_data is not None:
            self.data_cache[step_id] = output_data
        
        return tool_output
    
    def get_output_metadata(self, step_id: str) -> Optional[ToolOutput]:
        """Get metadata for a tool output (without data)."""
        return self.outputs.get(step_id)
    
    def get_output_data(self, step_id: str) -> Optional[Any]:
        """Get the actual output data from cache."""
        return self.data_cache.get(step_id)
    
    def get_full_output(self, step_id: str) -> Optional[Tuple[ToolOutput, Any]]:
        """Get both metadata and data for an output."""
        metadata = self.outputs.get(step_id)
        if metadata:
            data = self.data_cache.get(step_id)
            return metadata, data
        return None
    
    def list_available_outputs(
        self,
        exclude_step_id: Optional[str] = None
    ) -> Dict[str, Dict]:
        """
        List all available outputs that can be used as input to other tools.
        
        Args:
            exclude_step_id: If provided, exclude this step from results
                           (prevents a step from using its own output as input)
        
        Returns:
            Dict mapping step_id to output info (tool_name, columns, shape, etc.)
        """
        available = {}
        
        for step_id, output in self.outputs.items():
            if exclude_step_id and step_id == exclude_step_id:
                continue
            
            available[step_id] = {
                "tool_name": output.tool_name,
                "columns": output.output_columns,
                "output_shape": f"({output.row_count}, {len(output.output_columns)})",
                "execution_time_ms": output.execution_time_ms,
                "created_at": output.created_at,
                "source_step_id": output.source_step_id
            }
        
        return available
    
    def get_output_chain(self, step_id: str) -> List[str]:
        """
        Get the chain of steps that led to this output.
        
        Returns:
            List of step_ids from original data through all transformations
        """
        chain = [step_id]
        current = self.outputs.get(step_id)
        
        while current and current.source_step_id:
            chain.insert(0, current.source_step_id)
            current = self.outputs.get(current.source_step_id)
        
        return chain
    
    def validate_input_source(self, input_step_id: str) -> Tuple[bool, str]:
        """
        Validate that an input source is available and valid.
        
        Returns:
            (is_valid, error_message)
        """
        if input_step_id is None:
            return True, ""  # None means use main dataset, which is always valid
        
        if input_step_id not in self.outputs:
            return False, f"Output from step '{input_step_id}' not found"
        
        output = self.outputs[input_step_id]
        
        if not output.output_columns:
            return False, f"Output from '{output.tool_name}' has no columns"
        
        if output.row_count == 0:
            return False, f"Output from '{output.tool_name}' has no rows"
        
        if input_step_id not in self.data_cache:
            return False, f"Data for step '{input_step_id}' not available in cache"
        
        return True, ""
    
    def clear_output(self, step_id: str) -> bool:
        """Remove an output from registry and cache."""
        if step_id in self.outputs:
            del self.outputs[step_id]
        if step_id in self.data_cache:
            del self.data_cache[step_id]
            return True
        return False
    
    def clear_downstream_outputs(self, step_id: str) -> List[str]:
        """
        Remove all outputs that depend on a given step.
        Returns list of removed step_ids.
        """
        removed = []
        
        for out_id, output in list(self.outputs.items()):
            chain = self.get_output_chain(out_id)
            if step_id in chain:
                self.clear_output(out_id)
                removed.append(out_id)
        
        return removed
    
    def get_pipeline_visualization_data(self) -> Dict[str, Any]:
        """
        Generate data for visualizing the tool pipeline/chain.
        
        Returns:
            Dict with nodes and edges for visualization
        """
        nodes = []
        edges = []
        
        # Add main dataset node
        nodes.append({
            "id": "main_dataset",
            "label": "📊 Main Dataset",
            "type": "source"
        })
        
        # Add tool output nodes
        for step_id, output in self.outputs.items():
            nodes.append({
                "id": step_id,
                "label": f"🔧 {output.tool_name}\n({output.row_count} rows, {len(output.output_columns)} cols)",
                "type": "tool_output",
                "metadata": {
                    "tool_name": output.tool_name,
                    "row_count": output.row_count,
                    "column_count": len(output.output_columns)
                }
            })
            
            # Add edge from source to this output
            source = output.source_step_id or "main_dataset"
            edges.append({
                "from": source,
                "to": step_id,
                "label": f"{len(output.output_columns)} cols"
            })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "total_outputs": len(self.outputs)
        }
    
    def to_dict(self) -> Dict:
        """Serialize registry metadata (not the data cache)."""
        return {
            "outputs": {
                step_id: output.to_dict()
                for step_id, output in self.outputs.items()
            },
            "serialized_at": datetime.now().isoformat()
        }
    
    @staticmethod
    def from_dict(data: Dict) -> "ToolOutputRegistry":
        """Deserialize registry from dict."""
        registry = ToolOutputRegistry()
        
        outputs_data = data.get("outputs", {})
        for step_id, output_data in outputs_data.items():
            registry.outputs[step_id] = ToolOutput.from_dict(output_data)
        
        return registry
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the registered outputs."""
        if not self.outputs:
            return {
                "total_outputs": 0,
                "total_rows": 0,
                "total_columns": 0,
                "tools_used": []
            }
        
        total_rows = sum(output.row_count for output in self.outputs.values())
        total_columns = sum(len(output.output_columns) for output in self.outputs.values())
        tools_used = list(set(output.tool_name for output in self.outputs.values()))
        
        return {
            "total_outputs": len(self.outputs),
            "total_rows": total_rows,
            "total_columns": total_columns,
            "tools_used": sorted(tools_used),
            "average_rows_per_output": total_rows / len(self.outputs) if self.outputs else 0,
            "average_cols_per_output": total_columns / len(self.outputs) if self.outputs else 0
        }
