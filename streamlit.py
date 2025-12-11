"""
Streamlit Web UI for Hardware Simulation Agent
Provides an interactive interface for testing RTL designs
"""

import streamlit as st
import sys
from pathlib import Path
import json
from datetime import datetime
import time

# Add project to path
sys.path.append(str(Path(__file__).parent / "test_simulation_agent"))

from test_simulation_agent import (
    run_with_refinement,
    RTLRunner,
    get_llm,
)
from test_cases import (
    EASY_CASES,
    MEDIUM_CASES,
    HARD_CASES,
    TestCase
)

# Page config
st.set_page_config(
    page_title="Hardware Simulation Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stProgress > div > div > div > div {
        background-color: #00cc00;
    }
    .success-box {
        padding: 20px;
        border-radius: 5px;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .error-box {
        padding: 20px;
        border-radius: 5px;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    .info-box {
        padding: 20px;
        border-radius: 5px;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
    }
    .code-box {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #007bff;
        font-family: 'Courier New', monospace;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'run_history' not in st.session_state:
    st.session_state.run_history = []
if 'current_run' not in st.session_state:
    st.session_state.current_run = None


def get_all_test_cases():
    """Get all available test cases."""
    return {
        "Easy": EASY_CASES,
        "Medium": MEDIUM_CASES,
        "Hard": HARD_CASES,     
    }


def save_dut_to_file(dut_code: str, runner: RTLRunner):
    """Save DUT code to file."""
    rtl_dir = runner.project_root / "rtl"
    rtl_dir.mkdir(exist_ok=True)
    
    dut_file = rtl_dir / "my_dut.v"
    dut_file.write_text(dut_code.strip())
    
    return dut_file


def run_simulation(dut_code: str, test_description: str, mode: str, max_iterations: int, llm_model: str):
    """Run the simulation agent."""
    runner = RTLRunner()
    
    # Save DUT
    save_dut_to_file(dut_code, runner)
    
    # Get LLM
    llm = get_llm(model=llm_model)
    
    # Run agent
    success, failing_step, results, analysis, iterations_used = run_with_refinement(
        runner,
        llm,
        test_description,
        mode,
        max_iterations=max_iterations,
        test_case_id=None,
        test_case_name="Custom Test"
    )
    
    # Read generated testbench
    tb_file = runner.tb_file
    tb_code = tb_file.read_text() if tb_file.exists() else "No testbench generated"
    
    return {
        "success": success,
        "failing_step": failing_step,
        "results": results,
        "analysis": analysis,
        "iterations_used": iterations_used,
        "tb_code": tb_code,
        "timestamp": datetime.now().isoformat()
    }


def display_run_result(result: dict):
    """Display simulation run result."""
    if result["success"]:
        st.markdown(f"""
        <div class="success-box">
            <h3> Success!</h3>
            <p><strong>Iterations:</strong> {result['iterations_used']}</p>
            <p><strong>Status:</strong> All verification steps passed</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="error-box">
            <h3> Failed</h3>
            <p><strong>Iterations:</strong> {result['iterations_used']}</p>
            <p><strong>Failing Step:</strong> {result['failing_step']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Analysis
    with st.expander(" Analysis", expanded=True):
        st.text(result["analysis"])
    
    # Generated Testbench
    with st.expander(" Generated Testbench", expanded=False):
        st.code(result["tb_code"], language="verilog")
    
    # Verilator Results
    with st.expander(" Verilator Output", expanded=False):
        for step_name, step_result in result["results"].items():
            st.subheader(f"Step: {step_name}")
            st.text(f"Return Code: {step_result.get('returncode', 'N/A')}")
            
            if step_result.get("stderr"):
                st.text("STDERR:")
                st.code(step_result["stderr"][:1000], language="text")
            
            if step_result.get("stdout"):
                st.text("STDOUT:")
                st.code(step_result["stdout"][:1000], language="text")


# ============================================================================
# MAIN APP
# ============================================================================

# Header
st.title(" Hardware Simulation Agent")

# Sidebar
with st.sidebar:
    st.header(" Configuration")
    
    # Mode selection
    mode = st.selectbox(
        "Verification Mode",
        ["compile_only", "compile_elaborate", "full_sim"],
        index=2,
        help="Choose verification level"
    )
    
    # Max iterations
    max_iterations = st.slider(
        "Max Iterations",
        min_value=1,
        max_value=5,
        value=3,
        help="Number of refinement attempts"
    )
    
    # LLM model
    llm_model = st.selectbox(
        "LLM Model",
        ["qwen2.5-coder:7b"],
        index=0,
    )
    
    st.markdown("---")
    
    # Statistics
    st.header(" Statistics")
    if st.session_state.run_history:
        total_runs = len(st.session_state.run_history)
        successful_runs = sum(1 for r in st.session_state.run_history if r["success"])
        success_rate = (successful_runs / total_runs) * 100
        
        st.metric("Total Runs", total_runs)
        st.metric("Success Rate", f"{success_rate:.1f}%")
        st.metric("Avg Iterations", f"{sum(r['iterations_used'] for r in st.session_state.run_history) / total_runs:.1f}")
    else:
        st.info("No runs yet")
    
    st.markdown("---")
    

# Main content tabs
tab1, tab2, tab3, tab4 = st.tabs([" Quick Test", " Custom Test", " Test Suite", " History"])

# ============================================================================
# TAB 1: QUICK TEST (Predefined Cases)
# ============================================================================
with tab1:
    st.header("Test with Predefined Cases")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Difficulty selection
        all_cases = get_all_test_cases()
        difficulty = st.selectbox(
            "Difficulty Level",
            list(all_cases.keys()),
            help="Select test difficulty"
        )
        
        # Test case selection
        cases = all_cases[difficulty]
        case_names = [f"#{c.id}: {c.name}" for c in cases]
        selected_idx = st.selectbox(
            "Test Case",
            range(len(cases)),
            format_func=lambda i: case_names[i]
        )
        
        selected_case = cases[selected_idx]
        
        
    
    with col2:
        # DUT Code
        st.subheader("DUT Code")
        st.code(selected_case.dut_code, language="verilog", line_numbers=True)
        
        # Test Description
        st.subheader("Test Description")
        st.info(selected_case.test_description)
    
    # Run button
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        run_button = st.button(" Run Test", type="primary", use_container_width=True)
    with col2:
        if st.button(" Reset", use_container_width=True):
            st.session_state.current_run = None
            st.rerun()
    
    if run_button:
        with st.spinner(f"Running test case #{selected_case.id}... This may take 1-2 minutes..."):
            progress_bar = st.progress(0)
            
            # Simulate progress
            for i in range(0, 30, 10):
                progress_bar.progress(i)
                time.sleep(0.5)
            
            result = run_simulation(
                selected_case.dut_code,
                selected_case.test_description,
                mode,
                max_iterations,
                llm_model
            )
            
            progress_bar.progress(100)
            
            # Save to history
            result["test_case_name"] = selected_case.name
            result["difficulty"] = selected_case.difficulty
            st.session_state.run_history.append(result)
            st.session_state.current_run = result
    
    # Display results
    if st.session_state.current_run:
        st.markdown("---")
        st.header(" Results")
        display_run_result(st.session_state.current_run)


# ============================================================================
# TAB 2: CUSTOM TEST
# ============================================================================
with tab2:
    st.header("Custom Test")
    st.markdown("Write your own DUT and test description")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("DUT Verilog Code")
        custom_dut = st.text_area(
            "Enter your DUT code",
            value="""module my_dut (
    input  wire       clk,
    input  wire       rst,
    input  wire [7:0] data_in,
    output reg  [7:0] data_out
);
    always @(posedge clk or posedge rst) begin
        if (rst)
            data_out <= 8'h00;
        else
            data_out <= data_in + 1;
    end
endmodule""",
            height=300,
            help="Paste your Verilog/SystemVerilog DUT code"
        )
    
    with col2:
        st.subheader("Test Description")
        custom_description = st.text_area(
            "Describe the test in natural language",
            value="Test the incrementer. Reset to 0, then apply various input values and verify output is input + 1.",
            height=150,
            help="Describe what the testbench should do"
        )
        
        # Syntax check
        if st.checkbox("Show DUT Analysis"):
            if "module" in custom_dut and "endmodule" in custom_dut:
                st.success("✅ Valid module structure detected")
                
                # Simple port detection
                import re
                inputs = re.findall(r'input\s+(?:wire|reg)?\s*(?:\[\d+:\d+\])?\s*(\w+)', custom_dut)
                outputs = re.findall(r'output\s+(?:wire|reg)?\s*(?:\[\d+:\d+\])?\s*(\w+)', custom_dut)
                
                if inputs:
                    st.write(f"**Inputs detected:** {', '.join(inputs)}")
                if outputs:
                    st.write(f"**Outputs detected:** {', '.join(outputs)}")
            else:
                st.error("⚠️ Module structure not detected")
    
    # Run button
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        custom_run_button = st.button("▶️ Run Custom Test", type="primary", use_container_width=True, key="custom_run")
    with col2:
        if st.button("🔄 Reset", use_container_width=True, key="custom_reset"):
            st.session_state.current_run = None
            st.rerun()
    
    if custom_run_button:
        if not custom_dut.strip() or not custom_description.strip():
            st.error("Please provide both DUT code and test description")
        else:
            with st.spinner("Running custom test... This may take 1-2 minutes..."):
                progress_bar = st.progress(0)
                
                for i in range(0, 30, 10):
                    progress_bar.progress(i)
                    time.sleep(0.5)
                
                result = run_simulation(
                    custom_dut,
                    custom_description,
                    mode,
                    max_iterations,
                    llm_model
                )
                
                progress_bar.progress(100)
                
                # Save to history
                result["test_case_name"] = "Custom Test"
                result["difficulty"] = "custom"
                st.session_state.run_history.append(result)
                st.session_state.current_run = result
    
    # Display results
    if st.session_state.current_run and st.session_state.current_run.get("test_case_name") == "Custom Test":
        st.markdown("---")
        st.header("📊 Results")
        display_run_result(st.session_state.current_run)


# ============================================================================
# TAB 3: TEST SUITE
# ============================================================================
with tab3:
    st.header("Test Suite Runner")
    st.markdown("Run multiple test cases in sequence")
    
    # Suite selection
    all_cases = get_all_test_cases()
    selected_difficulties = st.multiselect(
        "Select Difficulty Levels",
        list(all_cases.keys()),
        default=["Easy"],
        help="Choose which difficulty levels to run"
    )
    
    if selected_difficulties:
        # Collect selected cases
        suite_cases = []
        for diff in selected_difficulties:
            suite_cases.extend(all_cases[diff])
        
        st.info(f"Selected {len(suite_cases)} test cases")
        
        # Show case list
        with st.expander("📋 Test Case List", expanded=False):
            for case in suite_cases:
                st.markdown(f"- #{case.id}: {case.name} [{case.difficulty}]")
        
        # Run suite button
        if st.button("▶️ Run Test Suite", type="primary"):
            suite_results = []
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for idx, case in enumerate(suite_cases):
                status_text.text(f"Running {idx+1}/{len(suite_cases)}: {case.name}")
                progress_bar.progress((idx) / len(suite_cases))
                
                try:
                    result = run_simulation(
                        case.dut_code,
                        case.test_description,
                        mode,
                        max_iterations,
                        llm_model
                    )
                    result["test_case_name"] = case.name
                    result["difficulty"] = case.difficulty
                    suite_results.append(result)
                    
                except Exception as e:
                    st.error(f"Error on case #{case.id}: {e}")
                    suite_results.append({
                        "success": False,
                        "test_case_name": case.name,
                        "difficulty": case.difficulty,
                        "error": str(e)
                    })
            
            progress_bar.progress(100)
            status_text.text("Suite complete!")
            
            # Display summary
            st.markdown("---")
            st.header("📊 Suite Results")
            
            total = len(suite_results)
            passed = sum(1 for r in suite_results if r.get("success"))
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Tests", total)
            col2.metric("Passed", passed)
            col3.metric("Success Rate", f"{(passed/total)*100:.1f}%")
            
            # Detailed results
            st.subheader("Detailed Results")
            for result in suite_results:
                status_icon = "✅" if result.get("success") else "❌"
                with st.expander(f"{status_icon} {result['test_case_name']} [{result['difficulty']}]"):
                    if result.get("success"):
                        st.success(f"Passed in {result.get('iterations_used', 'N/A')} iterations")
                    else:
                        st.error(f"Failed: {result.get('failing_step', result.get('error', 'Unknown'))}")
                    
                    if result.get("analysis"):
                        st.text(result["analysis"])


# ============================================================================
# TAB 4: HISTORY
# ============================================================================
with tab4:
    st.header("Run History")
    
    if not st.session_state.run_history:
        st.info("No runs in history yet. Complete a test to see results here.")
    else:
        # Summary stats
        total_runs = len(st.session_state.run_history)
        successful = sum(1 for r in st.session_state.run_history if r["success"])
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Runs", total_runs)
        col2.metric("Successful", successful)
        col3.metric("Failed", total_runs - successful)
        col4.metric("Success Rate", f"{(successful/total_runs)*100:.1f}%")
        
        st.markdown("---")
        
        # Clear history button
        if st.button("🗑️ Clear History", type="secondary"):
            st.session_state.run_history = []
            st.session_state.current_run = None
            st.rerun()
        
        # Display each run
        for idx, result in enumerate(reversed(st.session_state.run_history)):
            status_icon = "✅" if result["success"] else "❌"
            timestamp = result.get("timestamp", "Unknown")
            
            with st.expander(f"{status_icon} Run #{total_runs - idx}: {result.get('test_case_name', 'Unknown')} - {timestamp}"):
                col1, col2, col3 = st.columns(3)
                col1.write(f"**Difficulty:** {result.get('difficulty', 'N/A')}")
                col2.write(f"**Iterations:** {result.get('iterations_used', 'N/A')}")
                col3.write(f"**Status:** {'Success' if result['success'] else 'Failed'}")
                
                if result.get("analysis"):
                    st.text("Analysis:")
                    st.code(result["analysis"], language="text")
                
                if result.get("tb_code"):
                    st.text("Generated Testbench:")
                    st.code(result["tb_code"][:500] + "..." if len(result["tb_code"]) > 500 else result["tb_code"], language="verilog")


