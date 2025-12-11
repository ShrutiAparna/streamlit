"""
User prompts for testbench generation (first attempt and refined).
"""

TB_USER_PROMPT_FIRST = """DUT SPECIFICATION:
{port_info}

Required Signal Declarations (COPY THIS EXACTLY):
{signal_declarations}

Required Instantiation (COPY THIS EXACTLY):
{module_name} dut (
{port_connections}
);

Test Description:
{user_request}

INSTRUCTIONS:
1. Copy the signal declarations above exactly
2. Copy the instantiation above exactly
3. Add clock generation if there's a 'clk' port: initial clk=0; always #5 clk=~clk;
4. Add reset sequence if there's 'rst' port: initial begin rst=1; #20; rst=0; ... end
5. Add test logic based on description
6. Add $finish at end

Output ONLY the complete testbench code. No explanations."""


TB_USER_PROMPT_REFINED = """PREVIOUS ATTEMPT FAILED. 

ERROR DETAILS:
{error_summary}

SPECIFIC FIXES REQUIRED:
{targeted_fixes}

DUT SPECIFICATION (UNCHANGED):
{port_info}

CORRECT Signal Declarations (USE EXACTLY):
{signal_declarations}

CORRECT Instantiation (USE EXACTLY):
{module_name} dut (
{port_connections}
);

Test Description (same as before):
{user_request}

STEP-BY-STEP FIX:
1. Start with: module tb_top;
2. Copy signal declarations from above
3. Copy DUT instantiation from above - DO NOT SKIP ANY PORTS
4. Add clock/reset if needed
5. Add test logic
6. Add $finish
7. End with: endmodule

Output ONLY the corrected testbench code."""


TB_USER_PROMPT_MINIMAL = """Generate testbench for:
{module_name} with ports: {port_list}

Test: {user_request}

Requirements:
- Module name: tb_top
- Connect all ports
- Add test logic
- Call $finish

Output code only."""


# Template for extremely simple cases
TB_USER_PROMPT_BASIC = """module {module_name}
Ports: {port_info}
Test: {user_request}

Generate tb_top that:
1. Declares: {signal_declarations}
2. Instantiates DUT with all ports
3. Tests as described
4. Calls $finish"""