from dataclasses import dataclass, asdict
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

class DebugLogger:
    """Store debug outputs and intermediate results"""
    
    def __init__(self, output_dir: str = "./debug_logs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.output_dir / self.session_id
        self.session_dir.mkdir(exist_ok=True)
        self.logs: Dict[str, Any] = {}
    
    def _serialize_object(self, obj: Any) -> Any:
        """Convert a single object to serializable format"""
        if hasattr(obj, "to_dict") and callable(obj.to_dict):
            return obj.to_dict()
        elif hasattr(obj, "__dict__"):
            return obj.__dict__
        else:
            return obj
    def _serialize_data(self, data: Any) -> Any:
        """Recursively convert data to serializable format (handles lists, dicts, objects)"""
        if isinstance(data, list):
            return [self._serialize_data(item) for item in data]
        elif isinstance(data, dict):
            return {key: self._serialize_data(value) for key, value in data.items()}
        else:
            return self._serialize_object(data)
        
    def to_json(self, data: Any) -> str:
        serialized = self._serialize_data(data)
        return json.dumps(serialized, ensure_ascii=False)

    def log_step(self, step_name: str, data: Any, step_number: int = None):
        """Log a processing step"""
        # Convert to serializable format
        try:
            serialized_str = self.to_json(data)
        except Exception as e:
            print(f"⚠ Warning: Failed to serialize {step_name}: {e}")
            serialized_str = str(data)
        
        self.logs[step_name] = {
            "timestamp": datetime.now().isoformat(),
            "step_number": step_number,
            "data": serialized_str
        }
        
        # Also save to individual file
        filename = f"{step_number:02d}_{step_name}.json" if step_number else f"{step_name}.json"
        filepath = self.session_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(serialized_str)
        
        print(f"✓ Logged: {filepath}")
    
    def log_response(self, name: str, response: str, step_number: int = None):
        """Log LLM response or API response"""
        filename = f"{step_number:02d}_{name}_response.txt" if step_number else f"{name}_response.txt"
        filepath = self.session_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(response)
        
        self.logs[f"{name}_response"] = {
            "timestamp": datetime.now().isoformat(),
            "filepath": str(filepath)
        }
        
        print(f"✓ Logged: {filepath}")
    
    def save_summary(self):
        """Save summary of all logs"""
        summary_path = self.session_dir / "summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(self.logs, f, ensure_ascii=False)
        print(f"✓ Debug session saved: {self.session_dir}")
        return str(self.session_dir)
