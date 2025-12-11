"""
Error-specific fix templates for common Verilator errors.
"""

import re

# ============================================================================
# ERROR FIX TEMPLATES
# ============================================================================

ERROR_FIX_TEMPLATES = {
    "PINMISSING": """
╔════════════════════════════════════════════════════════════════╗
║ CRITICAL ERROR: Missing Port Connection                       ║
╚════════════════════════════════════════════════════════════════╝

You forgot to connect port '{port}'.

REQUIRED FIX:
In your DUT instantiation, you MUST have this line:
    .{port}({port})

Complete instantiation template (COPY THIS):
{module_name} dut (
{port_connections}
);

Every line above MUST appear in your testbench.
""",

    "WIDTHTRUNC": """
╔════════════════════════════════════════════════════════════════╗
║ CRITICAL ERROR: Bit Width Mismatch                            ║
╚════════════════════════════════════════════════════════════════╝

Wrong bit width for port '{port}'.

Port expects: {expected_width}
You provided: {actual_width}

REQUIRED FIX:
Declare the signal correctly:
    {correct_declaration}

Examples:
  Single bit:  reg signal;
  8-bit:       reg [7:0] signal;
  4-bit:       reg [3:0] signal;
""",

    "WIDTHEXPAND": """
╔════════════════════════════════════════════════════════════════╗
║ CRITICAL ERROR: Bit Width Expansion                           ║
╚════════════════════════════════════════════════════════════════╝

Signal is too narrow for the port.

REQUIRED FIX:
Match the exact bit width from DUT specification.
Check your signal declarations.
""",

    "SIGNAL_UNDECLARED": """
╔════════════════════════════════════════════════════════════════╗
║ CRITICAL ERROR: Undeclared Signal                             ║
╚════════════════════════════════════════════════════════════════╝

Signal '{signal}' used but not declared.

REQUIRED FIX:
Add this declaration BEFORE using the signal:
    {declaration}

All signals must be declared in the testbench before use.
""",

    "WIRE_REG_MISMATCH": """
╔════════════════════════════════════════════════════════════════╗
║ CRITICAL ERROR: Wire/Reg Type Mismatch                        ║
╚════════════════════════════════════════════════════════════════╝

RULE: 
  - DUT INPUTS  → declare as 'reg' in testbench
  - DUT OUTPUTS → declare as 'wire' in testbench

FIX YOUR DECLARATIONS:
{corrected_declarations}
""",

    "MODULE_NOT_FOUND": """
╔════════════════════════════════════════════════════════════════╗
║ CRITICAL ERROR: Module Not Found                              ║
╚════════════════════════════════════════════════════════════════╝

Verilator cannot find module '{module}'.

COMMON CAUSES:
1. Typo in module name
2. Module name doesn't match file

REQUIRED FIX:
Use the EXACT module name from DUT: {correct_module_name}
""",

    "SYNTAX_ERROR": """
╔════════════════════════════════════════════════════════════════╗
║ ERROR: Verilog Syntax Error                                   ║
╚════════════════════════════════════════════════════════════════╝

General syntax error detected.

COMMON ISSUES:
- Missing semicolon
- Unmatched begin/end
- Wrong keyword spelling

Check your code structure carefully.
""",

    "TIMING_ERROR": """
╔════════════════════════════════════════════════════════════════╗
║ ERROR: Timing Construct Not Supported                         ║
╚════════════════════════════════════════════════════════════════╝

Verilator requires --timing flag for delays.

This is already enabled. Check your delay syntax:
  Correct:   #10 signal = 1;
  Incorrect: signal = #10 1;
""",
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_fix_for_error_type(error_type: str, **kwargs) -> str:
    """
    Get fix template for specific error type with variable substitution.
    
    Args:
        error_type: Error type (PINMISSING, WIDTHTRUNC, etc.)
        **kwargs: Variables to substitute in template
    
    Returns:
        Formatted fix template
    """
    template = ERROR_FIX_TEMPLATES.get(error_type, ERROR_FIX_TEMPLATES["SYNTAX_ERROR"])
    
    try:
        return template.format(**kwargs)
    except KeyError as e:
        # Missing required parameter, return template as-is
        return template


def parse_pinmissing_error(error_text: str) -> list[str]:
    """
    Extract missing pin names from PINMISSING error.
    
    Args:
        error_text: Verilator error output
    
    Returns:
        List of missing port names
    """
    missing_ports = []
    for line in error_text.split('\n'):
        match = re.search(r"missing pin: '(\w+)'", line)
        if match:
            missing_ports.append(match.group(1))
    return missing_ports


def parse_width_error(error_text: str) -> dict:
    """
    Extract bit width information from WIDTH error.
    
    Args:
        error_text: Verilator error output
    
    Returns:
        Dict with expected_width, actual_width, port_name
    """
    info = {}
    
    # Try to extract port name
    port_match = re.search(r"port '(\w+)'", error_text)
    if port_match:
        info['port'] = port_match.group(1)
    
    # Try to extract widths
    width_match = re.search(r"(\d+) bits.+?(\d+) bits", error_text)
    if width_match:
        info['expected_width'] = width_match.group(1)
        info['actual_width'] = width_match.group(2)
    
    return info


def generate_targeted_error_prompt(error_summary: str, ports: dict) -> str:
    """
    Generate specific fix instructions based on error type and context.
    
    Args:
        error_summary: Error text from Verilator
        ports: DUT port information dict
    
    Returns:
        Targeted fix prompt
    """
    fixes = []
    
    # Handle PINMISSING errors
    if "PINMISSING" in error_summary:
        missing_ports = parse_pinmissing_error(error_summary)
        
        if missing_ports:
            # Generate complete port connection list
            all_ports = [(name, width) for name, width in ports['inputs']] + \
                       [(name, width) for name, width in ports['outputs']]
            
            port_conns = []
            for name, width in all_ports:
                port_conns.append(f"        .{name}({name})")
            
            fix = get_fix_for_error_type(
                "PINMISSING",
                port=', '.join(missing_ports),
                module_name=ports['module_name'],
                port_connections=',\n'.join(port_conns)
            )
            fixes.append(fix)
    
    # Handle WIDTH errors
    if "WIDTHTRUNC" in error_summary or "WIDTHEXPAND" in error_summary:
        width_info = parse_width_error(error_summary)
        
        if 'port' in width_info:
            # Find correct declaration
            port_name = width_info['port']
            port_width = ""
            
            for name, width in ports['inputs'] + ports['outputs']:
                if name == port_name:
                    port_width = width
                    break
            
            if port_width:
                correct_decl = f"reg {port_width} {port_name};" if port_width else f"reg {port_name};"
            else:
                correct_decl = f"reg {port_name};"
            
            fix = get_fix_for_error_type(
                "WIDTHTRUNC",
                port=port_name,
                expected_width=width_info.get('expected_width', 'N bits'),
                actual_width=width_info.get('actual_width', 'M bits'),
                correct_declaration=correct_decl
            )
            fixes.append(fix)
        else:
            fixes.append(ERROR_FIX_TEMPLATES["WIDTHTRUNC"])
    
    # Handle module not found
    if "Cannot find" in error_summary and "module" in error_summary.lower():
        fix = get_fix_for_error_type(
            "MODULE_NOT_FOUND",
            module="<module>",
            correct_module_name=ports['module_name']
        )
        fixes.append(fix)
    
    # Generic syntax error
    if not fixes and ("Error" in error_summary or "error" in error_summary):
        fixes.append(ERROR_FIX_TEMPLATES["SYNTAX_ERROR"])
    
    return "\n\n".join(fixes) if fixes else "Review and fix the errors shown above."


def generate_corrected_declarations(ports: dict) -> str:
    """
    Generate complete corrected signal declarations.
    
    Args:
        ports: DUT port information
    
    Returns:
        Formatted declaration block
    """
    lines = []
    
    lines.append("// DUT Inputs (use 'reg' type)")
    for name, width in ports['inputs']:
        if width:
            lines.append(f"reg  {width:8} {name};")
        else:
            lines.append(f"reg           {name};")
    
    lines.append("\n// DUT Outputs (use 'wire' type)")
    for name, width in ports['outputs']:
        if width:
            lines.append(f"wire {width:8} {name};")
        else:
            lines.append(f"wire          {name};")
    
    return "\n".join(lines)