"""
Error fix templates for targeted refinement.
"""

from .error_fixes import (
    ERROR_FIX_TEMPLATES,
    generate_targeted_error_prompt,
    get_fix_for_error_type
)

__all__ = [
    'ERROR_FIX_TEMPLATES',
    'generate_targeted_error_prompt',
    'get_fix_for_error_type',
]