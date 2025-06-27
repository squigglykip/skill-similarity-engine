"""
Memory-Efficient Base Classes and Mixins

This module provides base classes and mixins that add memory-efficiency features
to core system classes like JobArchitecture, SkillTaxonomy, and various calculators.
These components enable memory-optimized operation when processing large datasets.
"""

import gc
import logging
import weakref
from typing import Any, Dict, List, Optional, Set, TypeVar, Generic, Tuple, Callable
from abc import ABC, abstractmethod

from .performance import (
    memory_profile, 
    get_memory_usage, 
    log_memory_summary,
    trigger_garbage_collection,
    MemoryEfficientDict
)

logger = logging.getLogger(__name__)

T = TypeVar('T')  # For generic type hinting

class MemoryEfficientMixin:
    """
    A mixin class that adds memory efficiency features to any class.
    
    This mixin provides a standardized way to enable memory-efficient operation
    across different components of the system. Classes that inherit from this
    mixin can toggle between normal and memory-efficient modes.
    """
    
    def __init__(self) -> None:
        """Initialize the mixin."""
        self._memory_efficient = False
        self._cleanup_callbacks: List[Callable[[], None]] = []
    
    def set_memory_efficient(self, enabled: bool = True) -> None:
        """
        Enable or disable memory-efficient operation.
        
        Args:
            enabled: Whether to enable memory-efficient operation
        """
        previous = self._memory_efficient
        self._memory_efficient = enabled
        
        # Log the change
        if previous != enabled:
            logger.debug(
                f"Memory-efficient mode {'enabled' if enabled else 'disabled'} "
                f"for {self.__class__.__name__}"
            )
            
            # Perform any necessary transformations
            if enabled:
                self._apply_memory_optimizations()
            else:
                self._remove_memory_optimizations()
    
    @property
    def memory_efficient(self) -> bool:
        """Whether memory-efficient operation is enabled."""
        return self._memory_efficient
    
    def _apply_memory_optimizations(self) -> None:
        """
        Apply memory optimizations when memory-efficient mode is enabled.
        
        This method should be overridden by subclasses to implement
        class-specific memory optimizations.
        """
        pass
    
    def _remove_memory_optimizations(self) -> None:
        """
        Remove memory optimizations when memory-efficient mode is disabled.
        
        This method should be overridden by subclasses to implement
        class-specific cleanup of memory optimizations.
        """
        pass
    
    def register_cleanup_callback(self, callback: Callable[[], None]) -> None:
        """
        Register a callback function that will be called during cleanup.
        
        Args:
            callback: Function to call during cleanup
        """
        self._cleanup_callbacks.append(callback)
    
    def cleanup(self) -> None:
        """
        Perform explicit cleanup to release memory.
        
        This method should be called when the object is no longer needed
        to ensure all memory is properly released.
        """
        # Execute all registered cleanup callbacks
        for callback in self._cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                logger.warning(f"Error in cleanup callback: {e}")
        
        # Clear the callbacks list
        self._cleanup_callbacks.clear()
        
        # Perform class-specific cleanup
        self._perform_cleanup()
        
        # Trigger garbage collection
        gc.collect()
    
    def _perform_cleanup(self) -> None:
        """
        Perform class-specific cleanup operations.
        
        This method should be overridden by subclasses to implement
        class-specific cleanup operations.
        """
        pass
    
    def __del__(self) -> None:
        """Destructor to ensure cleanup when the object is garbage collected."""
        try:
            self.cleanup()
        except Exception as e:
            # Can't log here as logger might be gone during shutdown
            pass


class MemoryEfficientJobArchitectureMixin(MemoryEfficientMixin):
    """
    Memory efficiency features specifically for JobArchitecture.
    
    This mixin adds JobArchitecture-specific memory optimizations, including
    dictionary optimization, lazy loading, and cleanup methods.
    """
    
    def _apply_memory_optimizations(self) -> None:
        """Apply JobArchitecture-specific memory optimizations."""
        # Convert the jobs dictionary to a memory-efficient dictionary
        if hasattr(self, 'jobs') and isinstance(self.jobs, dict):
            self.jobs = MemoryEfficientDict(self.jobs)
        
        # Add other JobArchitecture-specific optimizations here
        # For example, using weakrefs for certain references, etc.
    
    def _perform_cleanup(self) -> None:
        """Perform JobArchitecture-specific cleanup."""
        # Clear the jobs dictionary if it exists
        if hasattr(self, 'jobs') and isinstance(self.jobs, dict):
            self.jobs.clear()


class MemoryEfficientSkillTaxonomyMixin(MemoryEfficientMixin):
    """
    Memory efficiency features specifically for SkillTaxonomy.
    
    This mixin adds SkillTaxonomy-specific memory optimizations, including
    dictionary optimization, shared string storage, and cleanup methods.
    """
    
    def _apply_memory_optimizations(self) -> None:
        """Apply SkillTaxonomy-specific memory optimizations."""
        # Convert the skills dictionary to a memory-efficient dictionary
        if hasattr(self, 'skills') and isinstance(self.skills, dict):
            self.skills = MemoryEfficientDict(self.skills)
        
        # Convert the categories dictionary to a memory-efficient dictionary
        if hasattr(self, 'categories') and isinstance(self.categories, dict):
            self.categories = MemoryEfficientDict(self.categories)
        
        # Add other SkillTaxonomy-specific optimizations here
    
    def _perform_cleanup(self) -> None:
        """Perform SkillTaxonomy-specific cleanup."""
        # Clear the skills dictionary if it exists
        if hasattr(self, 'skills') and isinstance(self.skills, dict):
            self.skills.clear()
        
        # Clear the categories dictionary if it exists
        if hasattr(self, 'categories') and isinstance(self.categories, dict):
            self.categories.clear()


class MemoryEfficientCalculatorMixin(MemoryEfficientMixin):
    """
    Memory efficiency features specifically for similarity calculators.
    
    This mixin adds calculator-specific memory optimizations, including
    vector caching, incremental calculation, and cleanup methods.
    """
    
    def __init__(self) -> None:
        """Initialize the calculator mixin."""
        super().__init__()
        self._vector_cache: Dict[str, Any] = {}
        self._use_vector_cache = False
    
    def _apply_memory_optimizations(self) -> None:
        """Apply calculator-specific memory optimizations."""
        # Enable vector caching if appropriate
        self._use_vector_cache = True
        
        # Add other calculator-specific optimizations here
    
    def _remove_memory_optimizations(self) -> None:
        """Remove calculator-specific memory optimizations."""
        # Disable vector caching and clear the cache
        self._use_vector_cache = False
        self._vector_cache.clear()
    
    def _perform_cleanup(self) -> None:
        """Perform calculator-specific cleanup."""
        # Clear the vector cache
        self._vector_cache.clear()
        
        # Additional cleanup specific to calculators
        # For example, releasing any numpy arrays, etc.


class WeakDictOfLists(dict):
    """
    A dictionary of lists that holds weak references to the list items.
    
    This specialized dictionary allows storing lists of objects without
    preventing them from being garbage collected if they're no longer
    referenced elsewhere.
    """
    
    def __setitem__(self, key: Any, value: List[Any]) -> None:
        """
        Set a list value, storing weak references to the list items.
        
        Args:
            key: Dictionary key
            value: List of objects to store
        """
        # Convert list items to weak references
        weak_refs = [weakref.ref(item) for item in value]
        super().__setitem__(key, weak_refs)
    
    def __getitem__(self, key: Any) -> List[Any]:
        """
        Get a list value, resolving weak references to actual objects.
        
        Args:
            key: Dictionary key
            
        Returns:
            List of resolved objects (dead references are filtered out)
        """
        weak_refs = super().__getitem__(key)
        # Resolve weak references and filter out dead references
        return [ref() for ref in weak_refs if ref() is not None]
    
    def get(self, key: Any, default: Any = None) -> Any:
        """
        Get a list value with a default if the key doesn't exist.
        
        Args:
            key: Dictionary key
            default: Default value if key doesn't exist
            
        Returns:
            List of resolved objects or default value
        """
        if key in self:
            return self[key]
        return default


class MemoryEfficientFactory:
    """
    Factory for creating memory-efficient versions of core objects.
    
    This factory provides methods to create memory-efficient instances
    of JobArchitecture, SkillTaxonomy, and calculators.
    """
    
    @staticmethod
    def create_memory_efficient_job_architecture(jobs: Optional[Dict[str, Any]] = None) -> Any:
        """
        Create a memory-efficient JobArchitecture instance.
        
        Args:
            jobs: Optional dictionary of jobs
            
        Returns:
            A JobArchitecture instance with memory efficiency enabled
        """
        # Import here to avoid circular imports
        from skill_similarity_engine.models.jobs import JobArchitecture
        
        # Create a new instance
        arch = JobArchitecture(jobs=jobs)
        
        # If it's already a MemoryEfficientMixin, enable memory efficiency
        if isinstance(arch, MemoryEfficientMixin):
            arch.set_memory_efficient(True)
        
        return arch
    
    @staticmethod
    def create_memory_efficient_skill_taxonomy() -> Any:
        """
        Create a memory-efficient SkillTaxonomy instance.
        
        Returns:
            A SkillTaxonomy instance with memory efficiency enabled
        """
        # Import here to avoid circular imports
        from skill_similarity_engine.models.skills import SkillTaxonomy
        
        # Create a new instance
        taxonomy = SkillTaxonomy()
        
        # If it's already a MemoryEfficientMixin, enable memory efficiency
        if isinstance(taxonomy, MemoryEfficientMixin):
            taxonomy.set_memory_efficient(True)
        
        return taxonomy
    
    @staticmethod
    def create_memory_efficient_calculator(
        calculator_type: str, 
        taxonomy: Any, 
        job_architecture: Any
    ) -> Any:
        """
        Create a memory-efficient calculator instance.
        
        Args:
            calculator_type: Type of calculator ("cosine", etc.)
            taxonomy: SkillTaxonomy instance
            job_architecture: JobArchitecture instance
            
        Returns:
            A calculator instance with memory efficiency enabled
        """
        # Import here to avoid circular imports
        if calculator_type.lower() == "cosine":
            from skill_similarity_engine.similarity.cosine import (
                CosineSimilarityCalculator,
                TfidfVectorizer
            )
            
            # Create vectorizer
            vectorizer = TfidfVectorizer(taxonomy)
            
            # Create calculator
            calculator = CosineSimilarityCalculator(
                vectorizer=vectorizer,
                skill_taxonomy=taxonomy,
                job_architecture=job_architecture
            )
            
            # If it's already a MemoryEfficientMixin, enable memory efficiency
            if isinstance(calculator, MemoryEfficientMixin):
                calculator.set_memory_efficient(True)
            
            return calculator
        
        raise ValueError(f"Unsupported calculator type: {calculator_type}")


class MemoryEfficientContainer(Generic[T]):
    """
    A memory-efficient container for storing collections of objects.
    
    This container provides memory-efficient storage for collections by
    using specialized data structures and aggressive cleanup.
    """
    
    def __init__(self, max_size: Optional[int] = None) -> None:
        """
        Initialize the container.
        
        Args:
            max_size: Optional maximum size of the container
        """
        self.max_size = max_size
        self._items: Dict[Any, T] = MemoryEfficientDict()
        self._order: List[Any] = []
    
    def add(self, key: Any, item: T) -> None:
        """
        Add an item to the container.
        
        Args:
            key: Key to identify the item
            item: The item to store
        """
        # If the key already exists, update its order
        if key in self._items:
            self._order.remove(key)
        
        # If we're at max capacity, remove the oldest item
        elif self.max_size and len(self._items) >= self.max_size:
            oldest_key = self._order.pop(0)
            del self._items[oldest_key]
        
        # Add the new item
        self._items[key] = item
        self._order.append(key)
    
    def get(self, key: Any) -> Optional[T]:
        """
        Get an item from the container.
        
        Args:
            key: Key to identify the item
            
        Returns:
            The item if found, None otherwise
        """
        return self._items.get(key)
    
    def remove(self, key: Any) -> None:
        """
        Remove an item from the container.
        
        Args:
            key: Key of the item to remove
        """
        if key in self._items:
            self._order.remove(key)
            del self._items[key]
    
    def clear(self) -> None:
        """Clear all items from the container."""
        self._items.clear()
        self._order.clear()
    
    def keys(self) -> List[Any]:
        """Get the keys in the container."""
        return list(self._items.keys())
    
    def items(self) -> List[Tuple[Any, T]]:
        """Get the (key, item) pairs in the container."""
        return list(self._items.items())
    
    def values(self) -> List[T]:
        """Get the items in the container."""
        return list(self._items.values())
    
    def __len__(self) -> int:
        """Get the number of items in the container."""
        return len(self._items)
    
    def __contains__(self, key: Any) -> bool:
        """Check if a key exists in the container."""
        return key in self._items
    
    def __iter__(self):
        """Iterate over the items in the container."""
        for key in self._order:
            yield key, self._items[key]


class MemoryLeakageDetector:
    """
    Utility for detecting potential memory leaks.
    
    This class helps detect potential memory leaks by tracking object counts
    and monitoring memory usage over time.
    """
    
    def __init__(self) -> None:
        """Initialize the detector."""
        self._object_counts: Dict[type, int] = {}
        self._memory_samples: List[Tuple[float, int]] = []
        self._reference_chains: Dict[type, List[List[Any]]] = {}
        
        # Initialize type counts
        self._update_object_counts()
    
    def _update_object_counts(self) -> None:
        """Update the object counts."""
        self._object_counts.clear()
        
        # Count objects by type
        for obj in gc.get_objects():
            obj_type = type(obj)
            self._object_counts[obj_type] = self._object_counts.get(obj_type, 0) + 1
    
    def take_sample(self) -> None:
        """Take a memory usage sample."""
        # Update object counts
        self._update_object_counts()
        
        # Take a memory sample
        snapshot = get_memory_usage()
        self._memory_samples.append((snapshot.timestamp, snapshot.current_process_usage))
    
    def find_growing_types(self) -> List[Tuple[type, int, int]]:
        """
        Find types with growing instance counts.
        
        Returns:
            List of (type, old_count, new_count) tuples for types with growing counts
        """
        # Take a fresh sample
        old_counts = self._object_counts.copy()
        self._update_object_counts()
        
        # Find types with growing counts
        growing = []
        for obj_type, new_count in self._object_counts.items():
            old_count = old_counts.get(obj_type, 0)
            if new_count > old_count:
                growing.append((obj_type, old_count, new_count))
        
        # Sort by absolute growth
        growing.sort(key=lambda x: x[2] - x[1], reverse=True)
        
        return growing
    
    def track_references(self, target_type: type, max_chains: int = 5) -> None:
        """
        Track reference chains to instances of the specified type.
        
        Args:
            target_type: Type to track references to
            max_chains: Maximum number of reference chains to find
        """
        # Reset reference chains for this type
        self._reference_chains[target_type] = []
        
        # Find instances of the target type
        targets = [obj for obj in gc.get_objects() if isinstance(obj, target_type)]
        
        # Limit the number of targets to investigate
        targets = targets[:min(len(targets), max_chains)]
        
        for target in targets:
            # Find referrers (objects that refer to the target)
            referrers = gc.get_referrers(target)
            
            # Build reference chains
            for referrer in referrers:
                # Skip frames, modules, and dictionaries (too many)
                if isinstance(referrer, (dict, list, tuple, set)):
                    continue
                
                # Build a chain
                chain = [target, referrer]
                
                # Follow the chain up to 3 levels
                for _ in range(3):
                    next_referrers = gc.get_referrers(chain[-1])
                    if not next_referrers:
                        break
                    
                    # Skip common container types
                    for next_ref in next_referrers:
                        if not isinstance(next_ref, (dict, list, tuple, set)):
                            chain.append(next_ref)
                            break
                
                # Add the chain
                self._reference_chains[target_type].append(chain)
                
                # Limit the number of chains
                if len(self._reference_chains[target_type]) >= max_chains:
                    break
    
    def get_report(self) -> str:
        """
        Get a report of potential memory leaks.
        
        Returns:
            A formatted report string
        """
        growing = self.find_growing_types()
        
        lines = ["Memory Leakage Detection Report"]
        lines.append("-" * 40)
        
        if not growing:
            lines.append("No growing type counts detected.")
        else:
            lines.append("Types with growing instance counts:")
            for i, (obj_type, old_count, new_count) in enumerate(growing[:10], 1):
                growth = new_count - old_count
                lines.append(f"{i}. {obj_type.__name__}: {old_count} -> {new_count} (+{growth})")
        
        lines.append("\nMemory usage trend:")
        if len(self._memory_samples) >= 2:
            first_time, first_mem = self._memory_samples[0]
            last_time, last_mem = self._memory_samples[-1]
            
            duration = last_time - first_time
            mem_change = (last_mem - first_mem) / (1024 * 1024)  # Convert to MB
            
            lines.append(f"Duration: {duration:.2f} seconds")
            lines.append(f"Memory change: {mem_change:+.2f} MB")
            
            if mem_change > 0:
                rate = mem_change / duration if duration > 0 else 0
                lines.append(f"Growth rate: {rate:.2f} MB/sec")
        else:
            lines.append("Not enough samples to determine trend.")
        
        # Add reference chain information
        if self._reference_chains:
            lines.append("\nReference chains for tracked types:")
            for target_type, chains in self._reference_chains.items():
                lines.append(f"\n{target_type.__name__}:")
                
                if not chains:
                    lines.append("  No reference chains found.")
                else:
                    for i, chain in enumerate(chains, 1):
                        chain_desc = " -> ".join(type(obj).__name__ for obj in chain)
                        lines.append(f"  {i}. {chain_desc}")
        
        return "\n".join(lines) 
