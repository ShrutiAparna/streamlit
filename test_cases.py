#!/usr/bin/env python3
"""
20 Test Cases for Hardware Simulation Agent
Organized by difficulty: Easy → Medium → Hard → Expert

Now with COMPLETE MEMORY LOGGING for each test run and the whole suite.
"""

from dataclasses import dataclass
from typing import Literal
from pathlib import Path
from datetime import datetime  # NEW: for timestamps
# from hard_test_cases import VERY_HARD_CASES, EXTREME_CASES


@dataclass
class TestCase:
    """Test case structure."""
    id: int
    name: str
    difficulty: Literal["easy", "medium", "hard", "expert"]
    dut_code: str
    test_description: str
    expected_result: str
    min_mode: str  # Minimum mode to test (compile_only, compile_elaborate, full_sim)
    notes: str = ""


# ============================================================================
# EASY CASES (1-5): Basic functionality, simple logic
# ============================================================================

EASY_CASES = [
    TestCase(
        id=1,
        name="Simple AND Gate",
        difficulty="easy",
        dut_code="""
module my_dut (
    input  wire a,
    input  wire b,
    output wire y
);
    assign y = a & b;
endmodule
""",
        test_description="Test a 2-input AND gate. Apply all 4 input combinations (00, 01, 10, 11) and verify output.",
        expected_result="Should pass - simple combinational logic",
        min_mode="compile_only",
        notes="No clock, no state - simplest possible test"
    ),
    
    TestCase(
        id=2,
        name="2-to-1 Multiplexer",
        difficulty="easy",
        dut_code="""
module my_dut (
    input  wire [7:0] a,
    input  wire [7:0] b,
    input  wire       sel,
    output wire [7:0] y
);
    assign y = sel ? b : a;
endmodule
""",
        test_description="Test a 2-to-1 mux. Set a=0xAA, b=0x55. Test sel=0 (expect 0xAA) and sel=1 (expect 0x55).",
        expected_result="Should pass - basic mux test",
        min_mode="compile_only",
        notes="Combinational, multi-bit"
    ),
    
    TestCase(
        id=3,
        name="D Flip-Flop",
        difficulty="easy",
        dut_code="""
module my_dut (
    input  wire clk,
    input  wire d,
    output reg  q
);
    always @(posedge clk) begin
        q <= d;
    end
endmodule
""",
        test_description="Test a D flip-flop. Apply d=1, clock once, verify q=1. Apply d=0, clock once, verify q=0.",
        expected_result="Should pass - simple sequential",
        min_mode="full_sim",
        notes="First sequential test, needs clock"
    ),
    
    TestCase(
        id=4,
        name="4-bit Adder",
        difficulty="easy",
        dut_code="""
module my_dut (
    input  wire [3:0] a,
    input  wire [3:0] b,
    output wire [3:0] sum,
    output wire       carry
);
    assign {carry, sum} = a + b;
endmodule
""",
        test_description="Test 4-bit adder. Try: 3+5=8, 15+1=0 with carry, 7+8=15.",
        expected_result="Should pass - arithmetic logic",
        min_mode="compile_only",
        notes="Tests arithmetic and carry"
    ),
    
    TestCase(
        id=5,
        name="Simple Counter (4-bit)",
        difficulty="easy",
        dut_code="""
module my_dut (
    input  wire       clk,
    input  wire       rst,
    output reg  [3:0] count
);
    always @(posedge clk or posedge rst) begin
        if (rst)
            count <= 4'h0;
        else
            count <= count + 1;
    end
endmodule
""",
        test_description="Test 4-bit counter. Reset to 0, count for 20 clocks, verify count is between 1 and 15.",
        expected_result="Should pass - basic counter",
        min_mode="full_sim",
        notes="Tests reset and counting"
    ),
]


# ============================================================================
# MEDIUM CASES (6-10): More complex logic, multiple features
# ============================================================================

MEDIUM_CASES = [
    TestCase(
        id=6,
        name="8-bit Shift Register (original)",
        difficulty="medium",
        dut_code="""
module my_dut (
    input  wire       clk,
    input  wire       rst,
    input  wire       din,
    output reg  [7:0] dout
);
    always @(posedge clk) begin
        if (rst)
            dout <= 8'h00;
        else
            dout <= {dout[6:0], din};
    end
endmodule
""",
        test_description="8-bit shift register that shifts left on every clock and clears on reset",
        expected_result="Should pass - your working example",
        min_mode="full_sim",
        notes="Baseline case that already works"
    ),
    
    TestCase(
        id=7,
        name="Parameterized Counter with Enable",
        difficulty="medium",
        dut_code="""
module my_dut (
    input  wire       clk,
    input  wire       rst,
    input  wire       en,
    output reg  [7:0] count
);
    always @(posedge clk or posedge rst) begin
        if (rst)
            count <= 8'h00;
        else if (en)
            count <= count + 1;
    end
endmodule
""",
        test_description="Test counter with enable. Reset, then count with en=1 for 10 clocks. Disable (en=0) for 5 clocks and verify count doesn't change. Re-enable and verify counting resumes.",
        expected_result="Should pass - tests enable control",
        min_mode="full_sim",
        notes="Tests conditional counting"
    ),
    
    TestCase(
        id=8,
        name="Bidirectional Shift Register",
        difficulty="medium",
        dut_code="""
module my_dut (
    input  wire       clk,
    input  wire       rst,
    input  wire       dir,   // 0=left, 1=right
    input  wire       din,
    output reg  [7:0] dout
);
    always @(posedge clk) begin
        if (rst)
            dout <= 8'h00;
        else if (dir == 0)
            dout <= {dout[6:0], din};  // shift left
        else
            dout <= {din, dout[7:1]};  // shift right
    end
endmodule
""",
        test_description="Test bidirectional shift register. Shift in 0xAA left (dir=0), then shift right (dir=1) and verify pattern.",
        expected_result="Should pass - tests direction control",
        min_mode="full_sim",
        notes="Tests conditional shifting"
    ),
    
    TestCase(
       id=9,
        name="Simple FIFO (4 deep)",
        difficulty="medium",
        dut_code="""
module my_dut (
    input  wire       clk,
    input  wire       rst,
    input  wire       wr_en,
    input  wire       rd_en,
    input  wire [7:0] din,
    output reg  [7:0] dout,
    output wire       full,
    output wire       empty
);
    reg [7:0] mem [0:3];
    reg [2:0] wr_ptr, rd_ptr;
    reg [2:0] count;
    
    assign full = (count == 4);
    assign empty = (count == 0);
    
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            wr_ptr <= 0;
            rd_ptr <= 0;
            count <= 0;
        end else begin
            if (wr_en && !full) begin
                mem[wr_ptr[1:0]] <= din;
                wr_ptr <= wr_ptr + 1;
                count <= count + 1;
            end
            if (rd_en && !empty) begin
                dout <= mem[rd_ptr[1:0]];
                rd_ptr <= rd_ptr + 1;
                count <= count - 1;
            end
        end
    end
endmodule
""",
        test_description="Test 4-deep FIFO. Write 4 values, verify full flag. Read 4 values in order, verify empty flag. Test simultaneous read/write.",
        expected_result="Should pass with effort - complex state machine",
        min_mode="full_sim",
        notes="Tests memory and pointers - challenging for LLM"
    ),
    
    TestCase(
        id=10,
        name="Gray Code Counter",
        difficulty="medium",
        dut_code="""
module my_dut (
    input  wire       clk,
    input  wire       rst,
    output reg  [3:0] gray
);
    reg [3:0] binary;
    
    always @(posedge clk or posedge rst) begin
        if (rst)
            binary <= 4'h0;
        else
            binary <= binary + 1;
    end
    
    always @(*) begin
        gray = binary ^ (binary >> 1);
    end
endmodule
""",
        test_description="Test Gray code counter. Reset, count for 16 clocks, verify Gray code sequence: 0000, 0001, 0011, 0010, 0110...",
        expected_result="Should pass - tests binary to Gray conversion",
        min_mode="full_sim",
        notes="Tests combinational encoding"
    ),
]


# ============================================================================
# HARD CASES (11-15): Complex state machines, timing, edge cases
# ============================================================================

HARD_CASES = [
    TestCase(
        id=11,
        name="UART Transmitter (simplified)",
        difficulty="hard",
        dut_code="""
module my_dut (
    input  wire       clk,
    input  wire       rst,
    input  wire [7:0] data,
    input  wire       send,
    output reg        tx,
    output reg        busy
);
    reg [3:0] bit_cnt;
    reg [8:0] shift_reg;  // start + 8 data bits
    
    localparam IDLE = 0, TRANSMIT = 1;
    reg state;
    
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            state <= IDLE;
            tx <= 1;
            busy <= 0;
            bit_cnt <= 0;
        end else begin
            case (state)
                IDLE: begin
                    tx <= 1;
                    if (send) begin
                        shift_reg <= {data, 1'b0};  // data + start bit
                        bit_cnt <= 9;
                        state <= TRANSMIT;
                        busy <= 1;
                    end
                end
                TRANSMIT: begin
                    tx <= shift_reg[0];
                    shift_reg <= {1'b1, shift_reg[8:1]};
                    bit_cnt <= bit_cnt - 1;
                    if (bit_cnt == 1) begin
                        state <= IDLE;
                        busy <= 0;
                    end
                end
            endcase
        end
    end
endmodule
""",
        test_description="Test UART transmitter. Send byte 0x55. Verify start bit (0), then data bits LSB first, then idle (1). Check busy flag.",
        expected_result="May struggle - complex state machine with bit timing",
        min_mode="full_sim",
        notes="Tests FSM and serial protocol"
    ),
    
    TestCase(
        id=12,
        name="PWM Generator",
        difficulty="hard",
        dut_code="""
module my_dut (
    input  wire       clk,
    input  wire       rst,
    input  wire [7:0] duty_cycle,  // 0-255
    output reg        pwm_out
);
    reg [7:0] counter;
    
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            counter <= 0;
            pwm_out <= 0;
        end else begin
            counter <= counter + 1;
            pwm_out <= (counter < duty_cycle);
        end
    end
endmodule
""",
        test_description="Test PWM generator. Set duty_cycle=128 (50%), count 256 clocks, verify pwm_out is high for ~128 clocks and low for ~128 clocks.",
        expected_result="Should pass - but needs counting logic in TB",
        min_mode="full_sim",
        notes="Tests pulse width measurement"
    ),
    
    TestCase(
        id=13,
        name="Simple ALU (4 operations)",
        difficulty="hard",
        dut_code="""
module my_dut (
    input  wire [7:0]  a,
    input  wire [7:0]  b,
    input  wire [1:0]  op,  // 00=add, 01=sub, 10=and, 11=or
    output reg  [7:0]  result,
    output reg         overflow
);
    always @(*) begin
        overflow = 0;
        case (op)
            2'b00: {overflow, result} = a + b;
            2'b01: {overflow, result} = a - b;
            2'b10: result = a & b;
            2'b11: result = a | b;
        endcase
    end
endmodule
""",
        test_description="Test ALU with all 4 operations. Test add: 200+100=44 with overflow. Test sub: 10-5=5. Test AND: 0xFF&0x0F=0x0F. Test OR: 0xF0|0x0F=0xFF.",
        expected_result="Should pass - multiple operations to test",
        min_mode="compile_only",
        notes="Tests case statement and arithmetic"
    ),
    
    TestCase(
        id=14,
        name="Debouncer (button input)",
        difficulty="hard",
        dut_code="""
module my_dut (
    input  wire clk,
    input  wire rst,
    input  wire button_in,
    output reg  button_out
);
    parameter DEBOUNCE_CYCLES = 4;
    reg [2:0] counter;
    reg button_sync;
    
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            counter <= 0;
            button_sync <= 0;
            button_out <= 0;
        end else begin
            if (button_in == button_sync) begin
                counter <= 0;
            end else begin
                counter <= counter + 1;
                if (counter == DEBOUNCE_CYCLES-1) begin
                    button_sync <= button_in;
                    button_out <= button_in;
                    counter <= 0;
                end
            end
        end
    end
endmodule
""",
        test_description="Test debouncer. Toggle button_in with glitches (rapid 0-1-0 within 3 clocks). Verify button_out only changes after stable input for 4 clocks.",
        expected_result="May struggle - needs precise timing control",
        min_mode="full_sim",
        notes="Tests timing-dependent behavior"
    ),
    
    TestCase(
        id=15,
        name="Simple Cache Controller (2-way)",
        difficulty="hard",
        dut_code="""
module my_dut (
    input  wire        clk,
    input  wire        rst,
    input  wire [7:0]  addr,
    input  wire        rd_en,
    output reg  [7:0]  data_out,
    output reg         hit
);
    reg [7:0] cache_tag [0:1];
    reg [7:0] cache_data [0:1];
    reg [0:1] valid;
    reg       lru;  // 0 or 1
    
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            valid <= 2'b00;
            lru <= 0;
            hit <= 0;
        end else if (rd_en) begin
            if (valid[0] && cache_tag[0] == addr) begin
                data_out <= cache_data[0];
                hit <= 1;
                lru <= 1;
            end else if (valid[1] && cache_tag[1] == addr) begin
                data_out <= cache_data[1];
                hit <= 1;
                lru <= 0;
            else begin
                hit <= 0;
                cache_tag[lru] <= addr;
                cache_data[lru] <= addr;  // simple: data = addr
                valid[lru] <= 1;
                lru <= ~lru;
            end
        end
    end
endmodule
""",
        test_description="Test 2-way cache. Read addr 0x10 (miss), read again (hit). Read 0x20 (miss), read 0x30 (miss, evicts 0x10). Read 0x10 again (miss). Verify hit/miss pattern.",
        expected_result="Likely to fail - very complex logic",
        min_mode="full_sim",
        notes="Tests memory hierarchy - very challenging"
    ),
]


# ============================================================================
# EXPERT CASES (16-20): Edge cases, tricky timing, advanced features
# ============================================================================

EXPERT_CASES = [
    TestCase(
        id=16,
        name="Metastability Synchronizer",
        difficulty="expert",
        dut_code="""
module my_dut (
    input  wire clk,
    input  wire rst,
    input  wire async_in,
    output reg  sync_out
);
    reg sync_stage1;
    
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            sync_stage1 <= 0;
            sync_out <= 0;
        end else begin
            sync_stage1 <= async_in;
            sync_out <= sync_stage1;
        end
    end
endmodule
""",
        test_description="Test 2-stage synchronizer. Apply async_in changes at random times. Verify sync_out changes only on clock edges, with 2-cycle latency.",
        expected_result="Very hard - needs async input timing",
        min_mode="full_sim",
        notes="Tests CDC (clock domain crossing)"
    ),
    
    TestCase(
        id=17,
        name="Priority Encoder (8-bit)",
        difficulty="expert",
        dut_code="""
module my_dut (
    input  wire [7:0] data_in,
    output reg  [2:0] pos,
    output reg        valid
);
    always @(*) begin
        valid = 0;
        pos = 0;
        if (data_in[7]) begin pos = 7; valid = 1; end
        else if (data_in[6]) begin pos = 6; valid = 1; end
        else if (data_in[5]) begin pos = 5; valid = 1; end
        else if (data_in[4]) begin pos = 4; valid = 1; end
        else if (data_in[3]) begin pos = 3; valid = 1; end
        else if (data_in[2]) begin pos = 2; valid = 1; end
        else if (data_in[1]) begin pos = 1; valid = 1; end
        else if (data_in[0]) begin pos = 0; valid = 1; end
    end
endmodule
""",
        test_description="Test priority encoder. Try: 0x80→pos=7, 0x0F→pos=3, 0x01→pos=0, 0x00→valid=0. Test all 8 positions.",
        expected_result="Should pass but needs 8+ test vectors",
        min_mode="compile_only",
        notes="Tests priority logic with many cases"
    ),
    
    TestCase(
        id=18,
        name="Johnson Counter (8-bit)",
        difficulty="expert",
        dut_code="""
module my_dut (
    input  wire       clk,
    input  wire       rst,
    output reg  [7:0] count
);
    always @(posedge clk or posedge rst) begin
        if (rst)
            count <= 8'b00000000;
        else
            count <= {count[6:0], ~count[7]};
    end
endmodule
""",
        test_description="Test Johnson counter. Reset to 0x00, verify sequence: 0x00, 0x01, 0x03, 0x07, 0x0F, 0x1F, 0x3F, 0x7F, 0xFF, 0xFE, 0xFC, 0xF8, 0xF0, 0xE0, 0xC0, 0x80, 0x00 (repeats). Check full 16-state cycle.",
        expected_result="Hard - needs sequence verification",
        min_mode="full_sim",
        notes="Tests specific bit pattern sequence"
    ),
    
    TestCase(
        id=19,
        name="Parameterized Divider (divide by N)",
        difficulty="expert",
        dut_code="""
module my_dut (
    input  wire       clk,
    input  wire       rst,
    input  wire [3:0] divisor,  // divide by (divisor+1)
    output reg        clk_out
);
    reg [3:0] counter;
    
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            counter <= 0;
            clk_out <= 0;
        end else begin
            if (counter == divisor) begin
                counter <= 0;
                clk_out <= ~clk_out;
            end else begin
                counter <= counter + 1;
            end
        end
    end
endmodule
""",
        test_description="Test clock divider. Set divisor=3 (divide by 4), verify clk_out toggles every 4 input clocks. Test divisor=7 (divide by 8).",
        expected_result="Tricky - needs to count output toggles",
        min_mode="full_sim",
        notes="Tests frequency division and counting"
    ),
    
    TestCase(
        id=20,
        name="CRC-8 Calculator",
        difficulty="expert",
        dut_code="""
module my_dut (
    input  wire       clk,
    input  wire       rst,
    input  wire       data_in,
    input  wire       data_valid,
    output reg  [7:0] crc_out
);
    parameter POLY = 8'h07;  // x^8 + x^2 + x + 1
    
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            crc_out <= 8'h00;
        end else if (data_valid) begin
            crc_out <= {crc_out[6:0], 1'b0} ^ (crc_out[7] ? POLY : 8'h00) ^ {7'b0, data_in};
        end
    end
endmodule
""",
        test_description="Test CRC-8 calculator. Send byte 0x31 (bit by bit), verify final CRC matches expected value (0x?? - compute offline). Test with multiple bytes.",
        expected_result="Very hard - requires CRC algorithm knowledge",
        min_mode="full_sim",
        notes="Tests serial CRC computation - extremely challenging"
    ),
]


# ============================================================================
# Test Suite Runner
# ============================================================================

def save_test_case_to_file(test_case: TestCase, base_dir: Path):
    """Save a test case DUT to file."""
    rtl_dir = base_dir / "rtl"
    rtl_dir.mkdir(exist_ok=True)
    
    dut_file = rtl_dir / "my_dut.v"
    dut_file.write_text(test_case.dut_code.strip())
    
    return dut_file


def run_test_suite():
    """Run all 20 test cases WITH MEMORY LOGGING."""
    from test_simulation_agent import run_with_refinement, RTLRunner, get_llm, save_to_memory
    from pathlib import Path
    
    all_cases = EASY_CASES + MEDIUM_CASES + HARD_CASES 

    
    results = []
    llm = get_llm()
    
    # --- Suite-level memory object ---
    suite_memory = {
        "suite_name": "20_test_cases",
        "timestamp_start": datetime.now().isoformat(),
        "total_cases": len(all_cases),
        "test_runs": []
    }
    
    print("="*80)
    print("RUNNING 20 TEST CASES WITH MEMORY LOGGING")
    print("="*80)
    
    for i, test_case in enumerate(all_cases, 1):
        print(f"\n{'='*80}")
        print(f"TEST {i}/20: {test_case.name} [{test_case.difficulty.upper()}]")
        print(f"{'='*80}")
        print(f"Description: {test_case.test_description[:100]}...")
        
        # Save DUT to file
        runner = RTLRunner()
        save_test_case_to_file(test_case, runner.project_root)
        
        # Per-test memory object
        test_memory = {
            "test_case_id": test_case.id,
            "test_case_name": test_case.name,
            "difficulty": test_case.difficulty,
            "test_description": test_case.test_description,
            "dut_code": test_case.dut_code,
            "notes": test_case.notes,
            "timestamp_start": datetime.now().isoformat(),
        }
        
        # Run agent
        try:
            success, failing_step, run_results, analysis, iters = run_with_refinement(
                runner,
                llm,
                test_case.test_description,
                "full_sim",
                max_iterations=3,
                test_case_id=test_case.id,
                test_case_name=test_case.name
            )
            
            test_memory.update({
                "success": success,
                "iterations_used": iters,
                "failing_step": failing_step,
                "final_analysis": analysis,
                "timestamp_end": datetime.now().isoformat(),
            })
            
            results.append({
                "id": test_case.id,
                "name": test_case.name,
                "difficulty": test_case.difficulty,
                "success": success,
                "iterations": iters,
                "failing_step": failing_step
            })
            
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"\n{status} in {iters} iteration(s)")
            
        except Exception as e:
            print(f"\n💥 ERROR: {e}")
            test_memory.update({
                "success": False,
                "iterations_used": 0,
                "failing_step": "exception",
                "error": str(e),
                "timestamp_end": datetime.now().isoformat(),
            })
            
            results.append({
                "id": test_case.id,
                "name": test_case.name,
                "difficulty": test_case.difficulty,
                "success": False,
                "iterations": 0,
                "failing_step": "exception"
            })
        
        # Add per-test memory to suite memory
        suite_memory["test_runs"].append(test_memory)
    
    # Close suite memory and save
    suite_memory["timestamp_end"] = datetime.now().isoformat()
    memory_path = Path("test_suite_memory.json")
    save_to_memory(suite_memory, memory_path)
    
    # Summary
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)
    
    by_difficulty = {
        "easy": [r for r in results if r["difficulty"] == "easy"],
        "medium": [r for r in results if r["difficulty"] == "medium"],
        "hard": [r for r in results if r["difficulty"] == "hard"],
        "expert": [r for r in results if r["difficulty"] == "expert"],
    }
    
    for diff, cases in by_difficulty.items():
        passed = sum(1 for c in cases if c["success"])
        total = len(cases)
        pct = (passed/total*100) if total > 0 else 0
        print(f"\n{diff.upper():10} {passed}/{total} passed ({pct:.0f}%)")
        for case in cases:
            status = "✅" if case["success"] else "❌"
            print(f"  {status} #{case['id']:2} {case['name']:40} ({case['iterations']} iters)")
    
    total_passed = sum(1 for r in results if r["success"])
    print(f"\n{'='*80}")
    print(f"OVERALL: {total_passed}/20 passed ({total_passed/20*100:.0f}%)")
    print(f"{'='*80}")
    print(f"\n📁 Complete suite memory saved to: {memory_path}")
    
    return results


if __name__ == "__main__":
    run_test_suite()
