"""
DUT port extraction utilities.
"""

import re
from pathlib import Path


def extract_dut_ports(dut_file: Path) -> dict:
    """
    Parse DUT Verilog file and extract module name and ports.
    
    Args:
        dut_file: Path to Verilog DUT file
    
    Returns:
        Dict with module_name, inputs list, outputs list
    """
    if not dut_file.exists():
        return {"module_name": "my_dut", "inputs": [], "outputs": []}
    
    content = dut_file.read_text()
    
    # Extract module name
    module_match = re.search(r'module\s+(\w+)', content)
    module_name = module_match.group(1) if module_match else "my_dut"
    
    inputs = []
    outputs = []
    
    # Input patterns
    input_patterns = [
        r'input\s+wire\s+\[(\d+):(\d+)\]\s+(\w+)',
        r'input\s+wire\s+(\w+)',
        r'input\s+reg\s+\[(\d+):(\d+)\]\s+(\w+)',
        r'input\s+reg\s+(\w+)',
    ]
    
    for pattern in input_patterns:
        for match in re.finditer(pattern, content):
            if len(match.groups()) == 3 and ':' not in match.group(3):
                width = f"[{match.group(1)}:{match.group(2)}]"
                name = match.group(3)
                inputs.append((name, width))
            else:
                name = match.group(1) if len(match.groups()) == 1 else match.group(3)
                inputs.append((name, ""))
    
    # Output patterns
    output_patterns = [
        r'output\s+wire\s+\[(\d+):(\d+)\]\s+(\w+)',
        r'output\s+wire\s+(\w+)',
        r'output\s+reg\s+\[(\d+):(\d+)\]\s+(\w+)',
        r'output\s+reg\s+(\w+)',
    ]
    
    for pattern in output_patterns:
        for match in re.finditer(pattern, content):
            if len(match.groups()) == 3 and ':' not in match.group(3):
                width = f"[{match.group(1)}:{match.group(2)}]"
                name = match.group(3)
                outputs.append((name, width))
            else:
                name = match.group(1) if len(match.groups()) == 1 else match.group(3)
                outputs.append((name, ""))
    
    return {
        "module_name": module_name,
        "inputs": inputs,
        "outputs": outputs
    }


def format_port_info(ports: dict) -> str:
    """
    Format port information for LLM prompt.
    
    Args:
        ports: Port information dict from extract_dut_ports
    
    Returns:
        Formatted string with module name and port list
    """
    lines = [f"Module Name: {ports['module_name']}", ""]
    
    if ports['inputs']:
        lines.append("Input Ports:")
        for name, width in ports['inputs']:
            if width:
                lines.append(f"  - input wire {width:8} {name}")
            else:
                lines.append(f"  - input wire          {name}")
    
    if ports['outputs']:
        lines.append("\nOutput Ports:")
        for name, width in ports['outputs']:
            if width:
                lines.append(f"  - output {width:8} {name}")
            else:
                lines.append(f"  - output          {name}")
    
    return "\n".join(lines)


def detect_port_features(ports: dict) -> dict:
    """
    Detect characteristics of DUT ports for smart example selection.
    
    Args:
        ports: Port information dict
    
    Returns:
        Dict with boolean flags for port features
    """
    features = {
        "has_clk": False,
        "has_rst": False,
        "has_multibit": False,
        "max_width": 0,
        "num_inputs": len(ports['inputs']),
        "num_outputs": len(ports['outputs']),
    }
    
    # Check for clock
    for name, _ in ports['inputs']:
        if name.lower() in ['clk', 'clock']:
            features["has_clk"] = True
        if name.lower() in ['rst', 'reset']:
            features["has_rst"] = True
    
    # Check for multi-bit signals
    for name, width in ports['inputs'] + ports['outputs']:
        if width:
            features["has_multibit"] = True
            # Extract width number
            match = re.search(r'\[(\d+):', width)
            if match:
                w = int(match.group(1)) + 1
                features["max_width"] = max(features["max_width"], w)
    
    return features