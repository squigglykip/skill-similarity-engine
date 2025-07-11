"""
Base Workflow Classes for Orchestration

Provides abstract base classes for implementing workflow orchestrators following
the Orchestrator pattern established by BusinessContextOrchestrator.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
from datetime import datetime

from .session_manager import get_session_manager
from ..config.architectural_config_manager import get_config_manager
from ..error_handling.registry import ErrorRegistry
from ..logging.structured import log_structured


class WorkflowStepStatus(Enum):
    """Status of workflow step execution."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    """
    Represents a single step in a workflow.
    
    Attributes:
        name: Step name for identification
        description: Human-readable step description
        status: Current execution status
        execute_func: Function to execute for this step
        dependencies: List of step names that must complete first
        optional: Whether this step can be skipped if it fails
        metadata: Additional step metadata
    """
    name: str
    description: str
    execute_func: Callable[[], 'StepResult']
    dependencies: List[str] = field(default_factory=list)
    optional: bool = False
    status: WorkflowStepStatus = WorkflowStepStatus.PENDING
    metadata: Dict[str, Any] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    
    @property
    def duration(self) -> Optional[float]:
        """Get step execution duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).seconds
        return None
    
    def mark_started(self):
        """Mark step as started."""
        self.status = WorkflowStepStatus.IN_PROGRESS
        self.start_time = datetime.now()
    
    def mark_completed(self):
        """Mark step as completed."""
        self.status = WorkflowStepStatus.COMPLETED
        self.end_time = datetime.now()
    
    def mark_failed(self, error_message: str):
        """Mark step as failed."""
        self.status = WorkflowStepStatus.FAILED
        self.end_time = datetime.now()
        self.error_message = error_message
    
    def mark_skipped(self, reason: str = ""):
        """Mark step as skipped."""
        self.status = WorkflowStepStatus.SKIPPED
        self.error_message = reason


@dataclass
class StepResult:
    """
    Result of workflow step execution.
    
    Attributes:
        success: Whether the step succeeded
        message: Human-readable result message
        data: Optional result data
        metadata: Additional metadata about execution
    """
    success: bool
    message: str
    data: Optional[Any] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class WorkflowResult:
    """
    Result of workflow execution.
    
    Attributes:
        success: Whether the workflow completed successfully
        message: Human-readable result message
        steps_completed: Number of steps that completed successfully
        steps_failed: Number of steps that failed
        total_steps: Total number of steps in the workflow
        execution_time: Total workflow execution time in seconds
        data: Optional result data
        step_results: Individual step execution results
    """
    success: bool
    message: str
    steps_completed: int = 0
    steps_failed: int = 0
    total_steps: int = 0
    execution_time: Optional[float] = None
    data: Optional[Any] = None
    step_results: Dict[str, StepResult] = field(default_factory=dict)
    
    @property
    def completion_percentage(self) -> float:
        """Get workflow completion percentage."""
        if self.total_steps == 0:
            return 0.0
        return (self.steps_completed / self.total_steps) * 100


class BaseWorkflow(ABC):
    """
    Abstract base class for workflow orchestrators.
    
    Provides common functionality for workflow execution, step management,
    and error handling following SSE's architectural patterns.
    """
    
    def __init__(self, name: str, description: str = ""):
        """
        Initialize base workflow.
        
        Args:
            name: Workflow name for logging and identification
            description: Human-readable workflow description
        """
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"workflow.{name}")
        self.config_manager = get_config_manager()
        self.session_manager = get_session_manager()
        self.error_registry = ErrorRegistry()
        
        # Workflow state
        self.steps: List[WorkflowStep] = []
        self.current_step_index: int = 0
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.is_running: bool = False
        
    @abstractmethod
    def define_steps(self) -> List[WorkflowStep]:
        """
        Define the workflow steps.
        
        Returns:
            List of WorkflowStep objects defining the workflow
        """
        pass
    
    def add_step(self, step: WorkflowStep) -> None:
        """Add a step to the workflow."""
        self.steps.append(step)
    
    def get_step(self, step_name: str) -> Optional[WorkflowStep]:
        """Get a step by name."""
        for step in self.steps:
            if step.name == step_name:
                return step
        return None
    
    def validate_dependencies(self) -> List[str]:
        """
        Validate workflow step dependencies.
        
        Returns:
            List of validation error messages
        """
        errors = []
        step_names = {step.name for step in self.steps}
        
        for step in self.steps:
            for dependency in step.dependencies:
                if dependency not in step_names:
                    errors.append(f"Step '{step.name}' depends on unknown step '{dependency}'")
        
        return errors
    
    def can_execute_step(self, step: WorkflowStep) -> bool:
        """
        Check if a step can be executed based on its dependencies.
        
        Args:
            step: The step to check
            
        Returns:
            True if the step can be executed
        """
        for dependency_name in step.dependencies:
            dependency_step = self.get_step(dependency_name)
            if not dependency_step:
                return False
            if dependency_step.status != WorkflowStepStatus.COMPLETED:
                return False
        return True
    
    def execute_step(self, step: WorkflowStep) -> StepResult:
        """
        Execute a single workflow step.
        
        Args:
            step: The step to execute
            
        Returns:
            StepResult with execution status
        """
        log_structured(
            self.logger,
            level="info", 
            msg=f"Executing workflow step: {step.name}",
            workflow=self.name,
            step=step.name,
            description=step.description
        )
        
        step.mark_started()
        
        try:
            result = step.execute_func()
            
            if result.success:
                step.mark_completed()
                log_structured(
                    self.logger,
                    level="info",
                    msg=f"Step completed successfully: {step.name}",
                    workflow=self.name,
                    step=step.name,
                    duration=step.duration
                )
            else:
                step.mark_failed(result.message)
                log_structured(
                    self.logger,
                    level="error",
                    msg=f"Step failed: {step.name}",
                    workflow=self.name,
                    step=step.name,
                    error=result.message,
                    duration=step.duration
                )
            
            return result
            
        except Exception as e:
            error_msg = f"Step execution error: {str(e)}"
            step.mark_failed(error_msg)
            self.error_registry.register(e)
            
            log_structured(
                self.logger,
                level="error",
                msg=f"Step execution failed with exception: {step.name}",
                workflow=self.name,
                step=step.name,
                error=str(e),
                duration=step.duration
            )
            
            return StepResult(
                success=False,
                message=error_msg,
                metadata={'exception_type': type(e).__name__}
            )
    
    def execute(self, **kwargs) -> WorkflowResult:
        """
        Execute the complete workflow.
        
        Args:
            **kwargs: Workflow-specific arguments
            
        Returns:
            WorkflowResult with execution status and results
        """
        if self.is_running:
            return WorkflowResult(
                success=False,
                message="Workflow is already running",
                total_steps=len(self.steps)
            )
        
        log_structured(
            self.logger,
            level="info",
            msg=f"Starting workflow execution: {self.name}",
            workflow=self.name,
            total_steps=len(self.steps),
            args=list(kwargs.keys())
        )
        
        self.is_running = True
        self.start_time = datetime.now()
        
        try:
            # Define steps if not already done
            if not self.steps:
                self.steps = self.define_steps()
            
            # Validate dependencies
            dependency_errors = self.validate_dependencies()
            if dependency_errors:
                raise ValueError(f"Workflow dependency validation failed: {dependency_errors}")
            
            # Execute steps
            step_results = {}
            completed_count = 0
            failed_count = 0
            
            for step in self.steps:
                if not self.can_execute_step(step):
                    if step.optional:
                        step.mark_skipped("Dependencies not met")
                        continue
                    else:
                        step.mark_failed("Dependencies not met")
                        failed_count += 1
                        step_results[step.name] = StepResult(
                            success=False,
                            message="Dependencies not met"
                        )
                        continue
                
                result = self.execute_step(step)
                step_results[step.name] = result
                
                if result.success:
                    completed_count += 1
                else:
                    failed_count += 1
                    if not step.optional:
                        # Non-optional step failed, stop workflow
                        break
            
            self.end_time = datetime.now()
            self.is_running = False
            
            execution_time = (self.end_time - self.start_time).seconds
            success = failed_count == 0 or all(
                step.optional for step in self.steps 
                if step.status == WorkflowStepStatus.FAILED
            )
            
            result = WorkflowResult(
                success=success,
                message=f"Workflow {'completed' if success else 'failed'}: {completed_count}/{len(self.steps)} steps successful",
                steps_completed=completed_count,
                steps_failed=failed_count,
                total_steps=len(self.steps),
                execution_time=execution_time,
                step_results=step_results
            )
            
            log_structured(
                self.logger,
                level="info" if success else "error",
                msg=f"Workflow execution completed: {self.name}",
                workflow=self.name,
                success=success,
                completed=completed_count,
                failed=failed_count,
                total=len(self.steps),
                duration=execution_time
            )
            
            return result
            
        except Exception as e:
            self.end_time = datetime.now()
            self.is_running = False
            self.error_registry.register(e)
            
            log_structured(
                self.logger,
                level="error",
                msg=f"Workflow execution failed with exception: {self.name}",
                workflow=self.name,
                error=str(e)
            )
            
            return WorkflowResult(
                success=False,
                message=f"Workflow execution failed: {str(e)}",
                total_steps=len(self.steps),
                execution_time=(self.end_time - self.start_time).seconds if self.start_time else 0
            )
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get a summary of the workflow status."""
        return {
            'name': self.name,
            'description': self.description,
            'is_running': self.is_running,
            'total_steps': len(self.steps),
            'completed_steps': sum(1 for step in self.steps if step.status == WorkflowStepStatus.COMPLETED),
            'failed_steps': sum(1 for step in self.steps if step.status == WorkflowStepStatus.FAILED),
            'current_step': self.current_step_index,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'steps': [
                {
                    'name': step.name,
                    'description': step.description,
                    'status': step.status.value,
                    'duration': step.duration,
                    'optional': step.optional
                }
                for step in self.steps
            ]
        }
    
    def __str__(self) -> str:
        return f"{self.name}: {self.description}"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}', steps={len(self.steps)})>" 