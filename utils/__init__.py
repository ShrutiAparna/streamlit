"""
Utility functions for test simulation agent.
"""

from .port_extractor import extract_dut_ports, format_port_info, detect_port_features
from .code_generator import (
    generate_signal_declarations,
    generate_port_connections,
    sanitize_verilog_code
)

__all__ = [
    'extract_dut_ports',
    'format_port_info',
    'generate_signal_declarations',
    'generate_port_connections',
    'sanitize_verilog_code',
    'detect_port_features',
]