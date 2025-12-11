"""
Few-shot learning examples for testbench generation.
Organized by complexity and common patterns.
"""

# ============================================================================
# BASIC EXAMPLES
# ============================================================================

EXAMPLE_COMBINATIONAL_2INPUT = """
EXAMPLE: Simple 2-Input Combinational Logic
DUT Ports: 
  input wire a
  input wire b
  output wire y

Correct Testbench:
module tb_top;
    reg a, b;
    wire y;
    
    my_dut dut(.a(a), .b(b), .y(y));
    
    initial begin
        a=0; b=0; #10;
        a=0; b=1; #10;
        a=1; b=0; #10;
        a=1; b=1; #10;
        $finish;
    end
endmodule
"""


EXAMPLE_MULTIBIT_COMBINATIONAL = """
EXAMPLE: Multi-bit Combinational Logic
DUT Ports:
  input wire [7:0] a
  input wire [7:0] b
  output wire [7:0] sum
  output wire carry

Correct Testbench:
module tb_top;
    reg [7:0] a, b;
    wire [7:0] sum;
    wire carry;
    
    my_dut dut(.a(a), .b(b), .sum(sum), .carry(carry));
    
    initial begin
        a=8'd5; b=8'd3; #10;
        a=8'd255; b=8'd1; #10;
        a=8'd128; b=8'd128; #10;
        $finish;
    end
endmodule
"""


# ============================================================================
# SEQUENTIAL EXAMPLES
# ============================================================================

EXAMPLE_SIMPLE_SEQUENTIAL = """
EXAMPLE: Simple Sequential Logic with Clock
DUT Ports:
  input wire clk
  input wire d
  output reg q

Correct Testbench:
module tb_top;
    reg clk, d;
    wire q;
    
    my_dut dut(.clk(clk), .d(d), .q(q));
    
    initial clk = 0;
    always #5 clk = ~clk;
    
    initial begin
        d=0; #10;
        d=1; #10;
        d=0; #10;
        $finish;
    end
endmodule
"""


EXAMPLE_WITH_RESET = """
EXAMPLE: Sequential with Clock and Reset
DUT Ports:
  input wire clk
  input wire rst
  input wire [7:0] data
  output reg [7:0] out

Correct Testbench:
module tb_top;
    reg clk, rst;
    reg [7:0] data;
    wire [7:0] out;
    
    my_dut dut(.clk(clk), .rst(rst), .data(data), .out(out));
    
    initial clk = 0;
    always #5 clk = ~clk;
    
    initial begin
        rst=1; data=0; #20;
        rst=0; data=8'hAA; #50;
        data=8'h55; #50;
        $finish;
    end
endmodule
"""


EXAMPLE_COUNTER = """
EXAMPLE: Counter with Enable
DUT Ports:
  input wire clk
  input wire rst
  input wire en
  output reg [3:0] count

Correct Testbench:
module tb_top;
    reg clk, rst, en;
    wire [3:0] count;
    
    my_dut dut(.clk(clk), .rst(rst), .en(en), .count(count));
    
    initial clk = 0;
    always #5 clk = ~clk;
    
    initial begin
        rst=1; en=0; #20;
        rst=0; en=1; #100;
        en=0; #50;
        $finish;
    end
endmodule
"""


# ============================================================================
# COMPLEX EXAMPLES
# ============================================================================

EXAMPLE_SHIFT_REGISTER = """
EXAMPLE: Shift Register
DUT Ports:
  input wire clk
  input wire rst
  input wire din
  output reg [7:0] dout

Correct Testbench:
module tb_top;
    reg clk, rst, din;
    wire [7:0] dout;
    
    my_dut dut(.clk(clk), .rst(rst), .din(din), .dout(dout));
    
    initial clk = 0;
    always #5 clk = ~clk;
    
    initial begin
        rst=1; din=0; #20;
        rst=0;
        din=1; #10;
        din=0; #10;
        din=1; #10;
        #100;
        $finish;
    end
endmodule
"""


EXAMPLE_FSM = """
EXAMPLE: Simple FSM
DUT Ports:
  input wire clk
  input wire rst
  input wire start
  output reg busy
  output reg done

Correct Testbench:
module tb_top;
    reg clk, rst, start;
    wire busy, done;
    
    my_dut dut(.clk(clk), .rst(rst), .start(start), .busy(busy), .done(done));
    
    initial clk = 0;
    always #5 clk = ~clk;
    
    initial begin
        rst=1; start=0; #20;
        rst=0; #10;
        start=1; #10;
        start=0;
        wait(done);
        #20;
        $finish;
    end
endmodule
"""


# ============================================================================
# ORGANIZED COLLECTIONS
# ============================================================================

FEW_SHOT_EXAMPLES = {
    "combinational": [
        EXAMPLE_COMBINATIONAL_2INPUT,
        EXAMPLE_MULTIBIT_COMBINATIONAL,
    ],
    "sequential": [
        EXAMPLE_SIMPLE_SEQUENTIAL,
        EXAMPLE_WITH_RESET,
        EXAMPLE_COUNTER,
    ],
    "complex": [
        EXAMPLE_SHIFT_REGISTER,
        EXAMPLE_FSM,
    ],
    "all": [
        EXAMPLE_COMBINATIONAL_2INPUT,
        EXAMPLE_WITH_RESET,
    ]
}


def get_examples_for_category(category: str = "all", max_examples: int = 2) -> str:
    """
    Get few-shot examples for a specific category.
    
    Args:
        category: One of "combinational", "sequential", "complex", "all"
        max_examples: Maximum number of examples to return
    
    Returns:
        Formatted examples string
    """
    if category not in FEW_SHOT_EXAMPLES:
        category = "all"
    
    examples = FEW_SHOT_EXAMPLES[category][:max_examples]
    return "\n\n".join(examples)


def get_examples_by_ports(has_clk: bool = False, has_rst: bool = False, 
                          multibit: bool = False) -> str:
    """
    Get examples based on DUT port characteristics.
    
    Args:
        has_clk: DUT has clock input
        has_rst: DUT has reset input
        multibit: DUT has multi-bit signals
    
    Returns:
        Most relevant examples
    """
    if has_clk and has_rst:
        return EXAMPLE_WITH_RESET
    elif has_clk:
        return EXAMPLE_SIMPLE_SEQUENTIAL
    elif multibit:
        return EXAMPLE_MULTIBIT_COMBINATIONAL
    else:
        return EXAMPLE_COMBINATIONAL_2INPUT