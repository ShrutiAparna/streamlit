"""
Prompt management package for test simulation agent.
"""

from .system_prompts import (
    TB_SYSTEM_PROMPT, 
    TB_SYSTEM_PROMPT_DETAILED,
    build_system_prompt_with_examples
)
from .user_prompts import (
    TB_USER_PROMPT_FIRST, 
    TB_USER_PROMPT_REFINED,
    TB_USER_PROMPT_MINIMAL,
    TB_USER_PROMPT_BASIC
)
from .few_shot_examples import (
    FEW_SHOT_EXAMPLES,
    get_examples_for_category,
    get_examples_by_ports
)

__all__ = [
    'TB_SYSTEM_PROMPT',
    'TB_SYSTEM_PROMPT_DETAILED',
    'build_system_prompt_with_examples',
    'TB_USER_PROMPT_FIRST',
    'TB_USER_PROMPT_REFINED',
    'TB_USER_PROMPT_MINIMAL',
    'TB_USER_PROMPT_BASIC',
    'FEW_SHOT_EXAMPLES',
    'get_examples_for_category',
    'get_examples_by_ports',
]