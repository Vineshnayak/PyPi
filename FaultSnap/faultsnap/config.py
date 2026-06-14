import os
import re
from dataclasses import dataclass, field
from typing import List, Optional, Union

# Default regex patterns for sensitive keys/variables
DEFAULT_PATTERNS = [
    r'(?i).*pass(word)?.*',
    r'(?i).*secret.*',
    r'(?i).*token.*',
    r'(?i).*api_?key.*',
    r'(?i).*auth.*',
    r'(?i).*credential.*',
]

@dataclass
class FaultSnapConfig:
    """Configuration object for FaultSnap."""
    
    # Environment variables to capture ("safe" captures only a whitelist, True captures all, False captures none)
    capture_environment: Union[str, bool] = "safe"
    
    # Crash Repository Directory
    repository_dir: str = "FaultSnaps"
    
    # Where to output .faultsnap files (deprecated in favor of repository_dir)
    output_dir: str = "."
    
    # Retention Management
    max_reports_per_fingerprint: int = 100
    max_days_to_keep: int = 30
    
    # Serializer constraints
    max_depth: int = 5
    max_items: int = 50
    max_string_len: int = 500
    max_total_items: int = 10000
    
    # Secret Masking
    masking_patterns: List[str] = field(default_factory=lambda: list(DEFAULT_PATTERNS))
    
    # Pre-compiled regex patterns for performance
    _compiled_patterns: List[re.Pattern] = field(default_factory=list, init=False)
    
    def __post_init__(self):
        self._compile_patterns()
        
    def _compile_patterns(self):
        self._compiled_patterns = [re.compile(p) for p in self.masking_patterns]
        
    def add_masking_pattern(self, pattern: str):
        if pattern not in self.masking_patterns:
            self.masking_patterns.append(pattern)
            self._compile_patterns()

# Global configuration instance
config = FaultSnapConfig()

def configure(**kwargs):
    """Update global configuration."""
    for key, value in kwargs.items():
        if hasattr(config, key) and not key.startswith("_"):
            setattr(config, key, value)
            
    if "masking_patterns" in kwargs:
        config._compile_patterns()
