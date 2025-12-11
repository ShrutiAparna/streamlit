"""
Verilog code generation utilities.
"""

import re


def generate_signal_declarations(ports: dict) -> str:
    """
    Generate testbench signal declarations.
    
    Args:
        ports: Port information dict
    
    Returns:
        Formatted signal declaration block
    """
    lines = []
    
    if ports['inputs']:
        lines.append("    // DUT Inputs (use 'reg')")
    for name, width in ports['inputs']:
        if width:
            lines.append(f"    reg  {width:8} {name};")
        else:
            lines.append(f"    reg           {name};")
    
    if ports['outputs']:
        lines.append("    // DUT Outputs (use 'wire')")
    for name, width in ports['outputs']:
        if width:
            lines.append(f"    wire {width:8} {name};")
        else:
            lines.append(f"    wire          {name};")
    
    return "\n".join(lines)


def generate_port_connections(ports: dict) -> str:
    """
    Generate DUT instantiation port connections.
    
    Args:
        ports: Port information dict
    
    Returns:
        Formatted port connection list
    """
    lines = []
    all_ports = ports['inputs'] + ports['outputs']
    
    for i, (name, width) in enumerate(all_ports):
        comma = "," if i < len(all_ports) - 1 else ""
        lines.append(f"        .{name}({name}){comma}")
    
    return "\n".join(lines)


def sanitize_verilog_code(raw_code: str) -> str:
    """
    Clean up LLM-generated Verilog code.
    
    Args:
        raw_code: Raw LLM output
    
    Returns:
        Cleaned Verilog code
    
    Raises:
        RuntimeError: If no valid module found
    """
    # Remove markdown code blocks
    code = re.sub(r'```verilog\n?', '', raw_code)
    code = re.sub(r'```systemverilog\n?', '', code)
    code = re.sub(r'```\n?', '', code)
    
    # Extract module
    start = code.find("module")
    end = code.rfind("endmodule")
    
    if start == -1 or end == -1:
        raise RuntimeError(
            f"No valid Verilog module found in output.\n"
            f"Output preview:\n{raw_code[:200]}"
        )
    
    clean_code = code[start:end + len("endmodule")]
    
    # Ensure ends with newline
    if not clean_code.endswith('\n'):
        clean_code += '\n'
    
    return clean_code


def validate_testbench(tb_code: str, ports: dict) -> tuple[bool, list[str]]:
    """
    Validate testbench code before running Verilator.
    
    Args:
        tb_code: Testbench code to validate
        ports: Expected DUT ports
    
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    # Check module name
    if "module tb_top" not in tb_code:
        issues.append("Module name is not 'tb_top'")
    
    # Check all ports are connected
    for name, _ in ports['inputs'] + ports['outputs']:
        if f".{name}({name})" not in tb_code:
            issues.append(f"Port '{name}' not connected in instantiation")
    
    # Check for $finish
    if "$finish" not in tb_code:
        issues.append("Missing $finish statement")
    
    # Check for endmodule
    if "endmodule" not in tb_code:
        issues.append("Missing endmodule")
    
    return len(issues) == 0, issues