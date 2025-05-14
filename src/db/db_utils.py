"""Database utility functions for input validation and sanitization."""
import re
from typing import Optional, Any, Union
from datetime import datetime
import bleach
from sqlalchemy import text

class DatabaseInputValidator:
    """Validator class for database inputs."""
    
    @staticmethod
    def sanitize_string(input_str: Optional[str], max_length: int = 256) -> Optional[str]:
        """
        Sanitize string input for database storage.
        
        Args:
            input_str: Input string to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized string or None if input is None
        """
        if input_str is None:
            return None
            
        # Strip whitespace and sanitize HTML/scripts
        cleaned = bleach.clean(str(input_str).strip(), tags=[], attributes={})
        
        # Truncate if too long
        return cleaned[:max_length] if len(cleaned) > max_length else cleaned

    @staticmethod
    def validate_vector(vector: Optional[list[float]], expected_dim: int = 384) -> Optional[list[float]]:
        """
        Validate vector input for database storage.
        
        Args:
            vector: Input vector to validate
            expected_dim: Expected vector dimension
            
        Returns:
            Validated vector or None if input is None
            
        Raises:
            ValueError: If vector is invalid
        """
        if vector is None:
            return None
            
        if not isinstance(vector, list):
            raise ValueError("Vector must be a list")
            
        if len(vector) != expected_dim:
            raise ValueError(f"Vector must have dimension {expected_dim}")
            
        if not all(isinstance(x, (int, float)) for x in vector):
            raise ValueError("Vector must contain only numbers")
            
        return vector

    @staticmethod
    def validate_role(role: str, allowed_roles: set = {'user', 'assistant', 'system', 'assistant-reasoning'}) -> str:
        """
        Validate message role.
        
        Args:
            role: Role to validate
            allowed_roles: Set of allowed role values
            
        Returns:
            Validated role
            
        Raises:
            ValueError: If role is invalid
        """
        role = str(role).strip().lower()
        if role not in allowed_roles:
            raise ValueError(f"Invalid role. Must be one of: {allowed_roles}")
        return role

    @staticmethod
    def validate_id(id_value: Any) -> int:
        """
        Validate ID input.
        
        Args:
            id_value: ID value to validate
            
        Returns:
            Validated ID as integer
            
        Raises:
            ValueError: If ID is invalid
        """
        try:
            id_int = int(id_value)
            if id_int <= 0:
                raise ValueError
            return id_int
        except (TypeError, ValueError):
            raise ValueError("ID must be a positive integer")

    @staticmethod
    def validate_token_count(count: Any) -> int:
        """
        Validate token count input.
        
        Args:
            count: Token count to validate
            
        Returns:
            Validated token count
            
        Raises:
            ValueError: If count is invalid
        """
        try:
            count_int = int(count)
            if count_int < 0:
                raise ValueError
            return count_int
        except (TypeError, ValueError):
            raise ValueError("Token count must be a non-negative integer") 