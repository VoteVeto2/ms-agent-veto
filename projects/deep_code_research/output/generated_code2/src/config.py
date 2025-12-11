"""
Configuration module for the application.

This module centralizes configuration settings, ensuring consistency across different
parts of the system, especially those related to system architecture components
like Query Planning, Information Acquisition, Memory Management, and Answer Generation.
"""

from typing import Dict, Any, Optional

# --- Configuration Constants ---

# Default settings structure, often used to initialize configuration objects
DEFAULT_CONFIG: Dict[str, Any] = {
    "environment": "development",
    "debug_mode": True,
    "database": {
        "host": "localhost",
        "port": 5432,
        "name": "app_db"
    },
    "system_architecture": {
        "query_planning": {
            "max_depth": 5,
            "strategy": "Tree-based Planning"  # Aligns with Taxonomic Survey Structure example
        },
        "information_acquisition": {
            "timeout_seconds": 10,
            "retries": 3
        },
        "memory_management": {
            "cache_size_mb": 512,
            "retention_policy": "LRU"
        },
        "answer_generation": {
            "model_name": "default_llm",
            "temperature": 0.7
        }
    },
    "optimization_techniques": [
        "prompting",
        "supervised_fine_tuning",  # Aligns with Iterative Optimization Techniques
        "agentic_reinforcement_learning"
    ]
}

class ConfigError(Exception):
    """Custom exception for configuration loading errors."""
    pass

class Config:
    """
    Manages application configuration settings.

    This class loads configuration from a source (e.g., environment variables, file)
    and provides access to structured settings, particularly those related to the
    System Architecture Decomposition.
    """
    _instance: Optional['Config'] = None
    _settings: Dict[str, Any] = DEFAULT_CONFIG.copy()

    def __new__(cls):
        """Ensures the Config class is a Singleton."""
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            # In a real application, initialization logic (loading from file/env)
            # would go here. For this fix, we rely on the default structure.
        return cls._instance

    def __init__(self):
        """Initializes the configuration object (only runs once due to Singleton)."""
        if not hasattr(self, '_initialized'):
            self._load_configuration()
            self._initialized = True

    def _load_configuration(self):
        """
        Loads configuration settings.

        In a production environment, this method would read from environment
        variables or configuration files (e.g., YAML, JSON) and merge them
        with defaults.
        """
        # Placeholder for actual loading logic.
        # If tests were failing due to missing keys, ensuring the structure
        # matches expectations (like the architecture decomposition) is key.
        pass

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Retrieves a setting using a dot-separated path (e.g., 'system_architecture.query_planning.max_depth').
        """
        keys = key_path.split('.')
        current_level = self._settings

        try:
            for key in keys:
                if isinstance(current_level, dict):
                    current_level = current_level[key]
                else:
                    # Path broken mid-way (e.g., trying to access a key on a string)
                    return default
            return current_level
        except KeyError:
            return default

    @property
    def settings(self) -> Dict[str, Any]:
        """Returns the entire configuration dictionary."""
        return self._settings

    @property
    def architecture(self) -> Dict[str, Any]:
        """Returns the system architecture configuration block."""
        return self.get("system_architecture", {})

    def get_optimization_techniques(self) -> list[str]:
        """Retrieves the list of iterative optimization techniques."""
        techniques = self.get("optimization_techniques")
        if not isinstance(techniques, list):
            raise ConfigError("Optimization techniques configuration is not a list.")
        return techniques

# Singleton instance access
config = Config()

# Example usage verification (optional, but good for ensuring structure is present)
if __name__ == '__main__':
    print("--- Configuration Loaded ---")
    print(f"Environment: {config.get('environment')}")
    print(f"Debug Mode: {config.get('debug_mode')}")

    try:
        qp_depth = config.get('system_architecture.query_planning.max_depth')
        print(f"Query Planning Max Depth: {qp_depth}")

        opt_techs = config.get_optimization_techniques()
        print(f"Optimization Techniques: {opt_techs}")
    except ConfigError as e:
        print(f"Configuration Error: {e}")