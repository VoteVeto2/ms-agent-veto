import os
import logging
import json
from pathlib import Path
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, field

# Configure logging
logger = logging.getLogger(__name__)

# Check for PyYAML support
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    logger.warning("PyYAML not found. YAML configuration files will be ignored.")

def _parse_bool(value: Union[str, bool]) -> bool:
    """Helper to parse boolean values from environment variables."""
    if isinstance(value, bool):
        return value
    return value.lower() in ("true", "1", "t", "yes", "y")

def _get_env_var(key: str, default: Any = None, cast_type: type = str) -> Any:
    """Helper to get environment variables with type casting."""
    value = os.getenv(key)
    if value is None:
        return default
    try:
        if cast_type == bool:
            return _parse_bool(value)
        return cast_type(value)
    except (ValueError, TypeError):
        logger.warning(f"Failed to cast environment variable {key} to {cast_type}. Using default.")
        return default

@dataclass
class LLMConfig:
    """Configuration for Large Language Models."""
    provider: str = "openai"
    api_key: Optional[str] = None
    model_name: str = "gpt-4"
    base_url: Optional[str] = None
    temperature: float = 0.0
    max_tokens: int = 4096
    timeout: int = 60
    
    def __post_init__(self):
        # Load from env if not set
        prefix = "LLM_"
        if not self.api_key:
            self.api_key = os.getenv(f"{prefix}API_KEY") or os.getenv("OPENAI_API_KEY")
        
        # Override with specific env vars if present
        self.provider = _get_env_var(f"{prefix}PROVIDER", self.provider)
        self.model_name = _get_env_var(f"{prefix}MODEL", self.model_name)
        self.base_url = _get_env_var(f"{prefix}BASE_URL", self.base_url)
        self.temperature = _get_env_var(f"{prefix}TEMPERATURE", self.temperature, float)
        self.max_tokens = _get_env_var(f"{prefix}MAX_TOKENS", self.max_tokens, int)
        self.timeout = _get_env_var(f"{prefix}TIMEOUT", self.timeout, int)

@dataclass
class SearchConfig:
    """Configuration for Information Acquisition (Search)."""
    provider: str = "tavily"  # tavily, serper, google, bing
    api_key: Optional[str] = None
    max_results: int = 5
    search_depth: str = "advanced"  # basic, advanced
    
    def __post_init__(self):
        prefix = "SEARCH_"
        if not self.api_key:
            self.api_key = os.getenv(f"{prefix}API_KEY") or os.getenv("TAVILY_API_KEY") or os.getenv("SERPER_API_KEY")
            
        self.provider = _get_env_var(f"{prefix}PROVIDER", self.provider)
        self.max_results = _get_env_var(f"{prefix}MAX_RESULTS", self.max_results, int)
        self.search_depth = _get_env_var(f"{prefix}DEPTH", self.search_depth)

@dataclass
class MemoryConfig:
    """Configuration for Memory Management and Vector Store."""
    vector_store_path: Path = field(default_factory=lambda: Path("./data/vector_store"))
    embedding_model: str = "text-embedding-3-small"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    def __post_init__(self):
        prefix = "MEMORY_"
        path_str = _get_env_var(f"{prefix}PATH")
        if path_str:
            self.vector_store_path = Path(path_str)
            
        self.embedding_model = _get_env_var(f"{prefix}EMBEDDING_MODEL", self.embedding_model)
        self.chunk_size = _get_env_var(f"{prefix}CHUNK_SIZE", self.chunk_size, int)
        self.chunk_overlap = _get_env_var(f"{prefix}CHUNK_OVERLAP", self.chunk_overlap, int)

@dataclass
class PlannerConfig:
    """Configuration for Query Planning."""
    max_subtasks: int = 5
    max_depth: int = 3
    planning_strategy: str = "tree"  # parallel, sequential, tree
    
    def __post_init__(self):
        prefix = "PLANNER_"
        self.max_subtasks = _get_env_var(f"{prefix}MAX_SUBTASKS", self.max_subtasks, int)
        self.max_depth = _get_env_var(f"{prefix}MAX_DEPTH", self.max_depth, int)
        self.planning_strategy = _get_env_var(f"{prefix}STRATEGY", self.planning_strategy)

@dataclass
class PathsConfig:
    """Configuration for project paths."""
    root: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    data: Path = field(default_factory=lambda: Path(__file__).parent.parent / "data")
    logs: Path = field(default_factory=lambda: Path(__file__).parent.parent / "logs")
    output: Path = field(default_factory=lambda: Path(__file__).parent.parent / "output")
    
    def __post_init__(self):
        # Ensure directories exist
        try:
            self.data.mkdir(parents=True, exist_ok=True)
            self.logs.mkdir(parents=True, exist_ok=True)
            self.output.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(f"Could not create default directories: {e}")

@dataclass
class Settings:
    """
    Global Configuration Settings.
    Aggregates component-specific configurations.
    """
    env: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    
    # Components
    llm: LLMConfig = field(default_factory=LLMConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    planner: PlannerConfig = field(default_factory=PlannerConfig)
    paths: PathsConfig = field(default_factory=PathsConfig)
    
    def __post_init__(self):
        self.env = _get_env_var("ENV", self.env)
        self.debug = _get_env_var("DEBUG", self.debug, bool)
        self.log_level = _get_env_var("LOG_LEVEL", self.log_level)
        
        # Configure root logger based on settings
        logging.basicConfig(
            level=getattr(logging, self.log_level.upper(), logging.INFO),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    @classmethod
    def load_from_yaml(cls, config_path: Union[str, Path]) -> "Settings":
        """Load configuration from a YAML file."""
        if not HAS_YAML:
            raise ImportError("PyYAML is required to load configuration from YAML files.")
            
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
            
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            
        # Helper to update dataclass from dict
        def update_config(cfg_obj, data_dict):
            for k, v in data_dict.items():
                if hasattr(cfg_obj, k):
                    current_val = getattr(cfg_obj, k)
                    if isinstance(current_val, (LLMConfig, SearchConfig, MemoryConfig, PlannerConfig, PathsConfig)) and isinstance(v, dict):
                        update_config(current_val, v)
                    else:
                        setattr(cfg_obj, k, v)
        
        # Create default settings
        settings = cls()
        
        # Update with YAML data
        update_config(settings, data)
        
        # Re-run post_init to ensure env vars take precedence if needed
        # (Optional: usually env vars override config files, or vice versa depending on policy)
        # Here we assume Config File > Defaults, but Env Vars > Config File is a common pattern.
        # To strictly enforce Env > Yaml, we would need to re-apply env logic.
        # For simplicity, we return the settings as modified by YAML.
        return settings

# Global settings instance
try:
    # Attempt to load from default config locations
    _default_config_path = Path("config.yaml")
    if _default_config_path.exists() and HAS_YAML:
        settings = Settings.load_from_yaml(_default_config_path)
    else:
        settings = Settings()
except Exception as e:
    logger.error(f"Failed to initialize settings: {e}")
    # Fallback to defaults
    settings = Settings()

# Export commonly used variables for easier import
ROOT_DIR = settings.paths.root
DATA_DIR = settings.paths.data
LOG_DIR = settings.paths.logs