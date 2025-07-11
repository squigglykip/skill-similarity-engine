"""
Base Command Classes for CLI Operations

Provides abstract base classes for implementing CLI commands following the Command pattern.
Integrates with SSE's configuration system and error handling framework.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional, List
from pathlib import Path

from ...config.architectural_config_manager import get_config_manager
from ...error_handling.registry import ErrorRegistry
from ...logging.structured import log_structured


@dataclass
class CommandResult:
    """
    Result of command execution.
    
    Attributes:
        success: Whether the command succeeded
        message: Human-readable result message
        data: Optional result data
        errors: List of error messages if any
        metadata: Additional metadata about execution
    """
    success: bool
    message: str
    data: Optional[Any] = None
    errors: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.metadata is None:
            self.metadata = {}


class BaseCommand(ABC):
    """
    Abstract base class for CLI commands.
    
    Provides common functionality for command execution, error handling,
    and configuration access following SSE's architectural patterns.
    """
    
    def __init__(self, name: str, description: str = ""):
        """
        Initialize base command.
        
        Args:
            name: Command name for logging and identification
            description: Human-readable command description
        """
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"command.{name}")
        self.config_manager = get_config_manager()
        self.error_registry = ErrorRegistry()
        
    @abstractmethod
    def execute(self, **kwargs) -> CommandResult:
        """
        Execute the command.
        
        Args:
            **kwargs: Command-specific arguments
            
        Returns:
            CommandResult with execution status and data
        """
        pass
    
    def validate_args(self, **kwargs) -> CommandResult:
        """
        Validate command arguments before execution.
        
        Args:
            **kwargs: Arguments to validate
            
        Returns:
            CommandResult indicating validation success/failure
        """
        # Default implementation accepts all arguments
        return CommandResult(
            success=True,
            message=f"Arguments validated for {self.name}",
            metadata={'validated_args': list(kwargs.keys())}
        )
    
    def run(self, **kwargs) -> CommandResult:
        """
        Run the command with validation and error handling.
        
        Args:
            **kwargs: Command arguments
            
        Returns:
            CommandResult with execution status
        """
        log_structured(
            self.logger, 
            level="info",
            msg=f"Starting command execution: {self.name}",
            command=self.name,
            args=list(kwargs.keys())
        )
        
        try:
            # Validate arguments first
            validation_result = self.validate_args(**kwargs)
            if not validation_result.success:
                return validation_result
            
            # Execute the command
            result = self.execute(**kwargs)
            
            # Log the result
            log_structured(
                self.logger,
                level="info" if result.success else "error",
                msg=f"Command completed: {self.name}",
                command=self.name,
                success=result.success,
                error_count=len(result.errors) if result.errors else 0
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Command execution failed: {self.name}", exc_info=True)
            self.error_registry.register(e)
            
            return CommandResult(
                success=False,
                message=f"Command {self.name} failed with error: {str(e)}",
                errors=[str(e)],
                metadata={'exception_type': type(e).__name__}
            )
    
    def get_config_value(self, *keys, default: Any = None) -> Any:
        """
        Get configuration value using the architectural config manager.
        
        Args:
            *keys: Configuration key path
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        try:
            return self.config_manager.get_nested_value(*keys, default=default)
        except Exception as e:
            self.logger.warning(f"Failed to get config value {keys}: {e}")
            return default
    
    def get_file_path(self, file_key: str) -> Path:
        """
        Get file path from configuration.
        
        Args:
            file_key: Configuration key for file path
            
        Returns:
            Path object for the file
        """
        try:
            return self.config_manager.get_file_path(file_key)
        except Exception as e:
            self.logger.error(f"Failed to get file path for {file_key}: {e}")
            raise
    
    def get_directory_path(self, dir_key: str) -> Path:
        """
        Get directory path from configuration.
        
        Args:
            dir_key: Configuration key for directory path
            
        Returns:
            Path object for the directory
        """
        try:
            return self.config_manager.get_directory(dir_key)
        except Exception as e:
            self.logger.error(f"Failed to get directory path for {dir_key}: {e}")
            raise
    
    def __str__(self) -> str:
        return f"{self.name}: {self.description}"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}')>" 