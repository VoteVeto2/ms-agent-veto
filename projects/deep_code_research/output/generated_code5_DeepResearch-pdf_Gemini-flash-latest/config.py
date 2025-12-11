import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

# --- Dependency Check for YAML ---
try:
    import yaml
except ImportError:
    # Define a dummy object if yaml is not installed, preventing file loading
    # but allowing defaults and environment variables to work.
    class DummyYAML:
        class YAMLError(Exception):
            pass
        
        @staticmethod
        def safe_load(*args, **kwargs):
            print("Warning: PyYAML is not installed. Configuration file loading is disabled. Using defaults and environment variables.")
            return None
    yaml = DummyYAML()

# --- Constants ---
DEFAULT_CONFIG_FILE = os.environ.get("DEEPRESEARCH_CONFIG", "config.yaml")
ENV_PREFIX = "DR_" # Deep Research environment variable prefix

@dataclass
class LLMConfig:
    """Configuration for Large Language Models."""
    api_key: Optional[str] = field(default_factory=lambda: os.environ.get(f"{ENV_PREFIX}LLM_API_KEY"))
    model_name: str = "gpt-4o"
    temperature: float = 0.1
    max_tokens: int = 4096
    provider: str = "openai" # e.g., openai, anthropic, local

@dataclass
class PathConfig:
    """Configuration for file paths and directories."""
    base_dir: str = field(default_factory=lambda: os.path.join(os.getcwd(), ".deepresearch"))
    data_dir: str = ""
    log_dir: str = ""
    cache_dir: str = ""
    kb_path: str = ""

    def __post_init__(self):
        """Calculates dependent paths based on base_dir."""
        # This method ensures that if base_dir is loaded from YAML or ENV, 
        # the dependent paths are correctly recalculated.
        self.data_dir = os.path.join(self.base_dir, "data")
        self.log_dir = os.path.join(self.base_dir, "logs")
        self.cache_dir = os.path.join(self.base_dir, "cache")
        self.kb_path = os.path.join(self.data_dir, "local_kb.sqlite")

@dataclass
class SandboxConfig:
    """Configuration for the secure code execution sandbox."""
    enabled: bool = True
    timeout_seconds: int = 10
    allowed_packages: List[str] = field(default_factory=lambda: ["numpy", "scipy", "pandas", "matplotlib"])

@dataclass
class KnowledgeConfig:
    """Configuration for external knowledge sources and APIs."""
    pubmed_api_key: Optional[str] = field(default_factory=lambda: os.environ.get(f"{ENV_PREFIX}PUBMED_API_KEY"))
    arxiv_cache_enabled: bool = True
    s2_api_key: Optional[str] = field(default_factory=lambda: os.environ.get(f"{ENV_PREFIX}S2_API_KEY"))

@dataclass
class Config:
    """
    Main configuration object for the DeepResearch framework.

    Settings are loaded in the following order (lowest priority first):
    1. Default values (defined in dataclasses).
    2. YAML configuration file (if specified).
    3. Environment variables (highest priority).
    """
    llm: LLMConfig = field(default_factory=LLMConfig)
    paths: PathConfig = field(default_factory=PathConfig)
    sandbox: SandboxConfig = field(default_factory=SandboxConfig)
    knowledge: KnowledgeConfig = field(default_factory=KnowledgeConfig)
    
    _config_file_path: Optional[str] = field(default=None, init=False)

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> 'Config':
        """
        Loads configuration from defaults, file, and environment variables.

        :param config_path: Optional path to a YAML configuration file. Defaults to config.yaml.
        :return: A fully configured Config object.
        """
        instance = cls()
        
        if config_path is None:
            config_path = DEFAULT_CONFIG_FILE
        
        instance._config_file_path = config_path

        # 1. Load from YAML file if it exists
        instance._load_from_yaml(config_path)
        
        # 2. Environment variables override YAML and defaults
        instance._override_from_env()
        
        # 3. Recalculate paths if base_dir was changed by YAML or ENV
        instance.paths.__post_init__()

        # 4. Ensure necessary directories exist
        instance._initialize_directories()

        return instance

    def _load_from_yaml(self, config_path: str):
        """Loads configuration settings from a YAML file."""
        if not hasattr(yaml, 'safe_load'):
            return # YAML library not available

        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    data = yaml.safe_load(f)
                
                if data:
                    # Merge data into existing dataclass structures
                    self._merge_dict_to_dataclass(self.llm, data.get('llm', {}))
                    self._merge_dict_to_dataclass(self.paths, data.get('paths', {}))
                    self._merge_dict_to_dataclass(self.sandbox, data.get('sandbox', {}))
                    self._merge_dict_to_dataclass(self.knowledge, data.get('knowledge', {}))
                
            except yaml.YAMLError as e:
                print(f"Warning: Could not parse YAML configuration file {config_path}. Error: {e}")
            except Exception as e:
                print(f"Warning: Failed to load configuration file {config_path}. Error: {e}")

    def _merge_dict_to_dataclass(self, target_dataclass: Any, source_dict: Dict[str, Any]):
        """Helper to merge dictionary values into a dataclass instance."""
        for key, value in source_dict.items():
            if hasattr(target_dataclass, key):
                # Attempt type conversion if necessary (especially for bools/ints/floats)
                target_type = type(getattr(target_dataclass, key))
                
                if target_type is bool and isinstance(value, str):
                    value = value.lower() in ('true', '1', 't', 'y', 'yes')
                elif target_type in (int, float) and isinstance(value, str):
                    try:
                        value = target_type(value)
                    except ValueError:
                        continue # Skip if conversion fails
                
                setattr(target_dataclass, key, value)

    def _override_from_env(self):
        """Overrides settings using environment variables (highest priority)."""
        
        # Paths
        if f"{ENV_PREFIX}BASE_DIR" in os.environ:
            self.paths.base_dir = os.environ[f"{ENV_PREFIX}BASE_DIR"]

        # LLM Settings
        if os.environ.get(f"{ENV_PREFIX}LLM_API_KEY"):
            self.llm.api_key = os.environ[f"{ENV_PREFIX}LLM_API_KEY"]
        if f"{ENV_PREFIX}LLM_MODEL_NAME" in os.environ:
            self.llm.model_name = os.environ[f"{ENV_PREFIX}LLM_MODEL_NAME"]
        if f"{ENV_PREFIX}LLM_TEMPERATURE" in os.environ:
            try:
                self.llm.temperature = float(os.environ[f"{ENV_PREFIX}LLM_TEMPERATURE"])
            except ValueError:
                pass

        # Sandbox Settings
        if f"{ENV_PREFIX}SANDBOX_TIMEOUT_SECONDS" in os.environ:
            try:
                self.sandbox.timeout_seconds = int(os.environ[f"{ENV_PREFIX}SANDBOX_TIMEOUT_SECONDS"])
            except ValueError:
                pass
        if f"{ENV_PREFIX}SANDBOX_ENABLED" in os.environ:
            val = os.environ[f"{ENV_PREFIX}SANDBOX_ENABLED"].lower()
            self.sandbox.enabled = val in ('true', '1', 't', 'y', 'yes')

        # Knowledge Keys
        if os.environ.get(f"{ENV_PREFIX}PUBMED_API_KEY"):
            self.knowledge.pubmed_api_key = os.environ[f"{ENV_PREFIX}PUBMED_API_KEY"]
        if os.environ.get(f"{ENV_PREFIX}S2_API_KEY"):
            self.knowledge.s2_api_key = os.environ[f"{ENV_PREFIX}S2_API_KEY"]


    def _initialize_directories(self):
        """Creates necessary directories if they do not exist."""
        paths_to_create = [
            self.paths.base_dir, 
            self.paths.data_dir, 
            self.paths.log_dir, 
            self.paths.cache_dir
        ]
        
        for path in paths_to_create:
            if path and not os.path.exists(path):
                try:
                    os.makedirs(path, exist_ok=True)
                except OSError as e:
                    # This should ideally be logged via the logging system, but config must work first.
                    print(f"Error creating configuration directory {path}: {e}")

# --- Global Configuration Management ---
_GLOBAL_CONFIG: Optional[Config] = None

def get_config() -> Config:
    """
    Retrieves the globally loaded configuration instance. 
    Loads it using default settings if it hasn't been loaded yet.
    """
    global _GLOBAL_CONFIG
    if _GLOBAL_CONFIG is None:
        _GLOBAL_CONFIG = Config.load()
    return _GLOBAL_CONFIG

def initialize_config(config_path: Optional[str] = None) -> Config:
    """
    Initializes and sets the global configuration instance, optionally specifying a config file path.
    
    :param config_path: Path to the configuration file.
    """
    global _GLOBAL_CONFIG
    _GLOBAL_CONFIG = Config.load(config_path=config_path)
    return _GLOBAL_CONFIG

# Optional: Function to reset config for testing purposes
def reset_config():
    """Resets the global configuration instance (useful for testing)."""
    global _GLOBAL_CONFIG
    _GLOBAL_CONFIG = None