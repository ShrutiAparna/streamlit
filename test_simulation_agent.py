# File: test_simulation_agent.py
"""
Test Simulation Agent - Main orchestration with comprehensive logging.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

from rtl_runner import RTLRunner, Mode

# Import modular components
from prompts import (
    TB_SYSTEM_PROMPT,
    build_system_prompt_with_examples,
    TB_USER_PROMPT_FIRST,
    TB_USER_PROMPT_REFINED,
    get_examples_for_category,
    get_examples_by_ports
)
from templates import generate_targeted_error_prompt
from utils import (
    extract_dut_ports,
    format_port_info,
    generate_signal_declarations,
    generate_port_connections,
    sanitize_verilog_code,
    detect_port_features
)


def get_llm(model: str = "qwen2.5-coder:7b"):
    """Initialize LLM with optimized settings."""
    return ChatOllama(
        model=model,
        temperature=0.1,
        num_predict=512,
    )


def extract_error_summary(results: dict, failing_step: str) -> str:
    """Extract key errors from Verilator output."""
    if failing_step not in results:
        return "Unknown error"
    
    stderr = results[failing_step].get('stderr', '')
    errors = []
    
    for line in stderr.split('\n'):
        if any(keyword in line for keyword in ['Error', 'Warning', 'PINMISSING', 'WIDTH']):
            if 'verilator lint' not in line.lower():
                errors.append(line.strip())
    
    return "\n".join(errors[:10]) if errors else stderr[:500]


def generate_testbench(
    llm, 
    user_request: str, 
    dut_path: Path, 
    tb_path: Path,
    iteration: int = 0,
    previous_error: dict = None
) -> Dict[str, Any]:
    """
    Generate testbench using modular prompts and templates.
    
    Returns:
        Dict with complete generation metadata for logging
    """
    
    # Extract port information
    ports = extract_dut_ports(dut_path)
    port_info = format_port_info(ports)
    signal_decls = generate_signal_declarations(ports)
    port_conns = generate_port_connections(ports)
    
    print(f"[agent] DUT Ports Detected:")
    print(f"{port_info}")
    print()
    
    # Read DUT code
    dut_code = dut_path.read_text() if dut_path.exists() else ""
    
    # Initialize generation log
    generation_log = {
        "iteration": iteration,
        "timestamp": datetime.now().isoformat(),
        "dut_file": str(dut_path),
        "dut_code": dut_code,
        "ports_detected": {
            "module_name": ports['module_name'],
            "inputs": ports['inputs'],
            "outputs": ports['outputs']
        },
        "port_info_formatted": port_info,
    }
    
    if iteration == 0 or previous_error is None:
        # First attempt - include few-shot examples
        features = detect_port_features(ports)
        
        generation_log["port_features"] = features
        
        # Select appropriate examples
        examples = get_examples_by_ports(
            has_clk=features["has_clk"],
            has_rst=features["has_rst"],
            multibit=features["has_multibit"]
        )
        
        generation_log["few_shot_examples_used"] = examples
        
        # Build system prompt with examples
        system_prompt = build_system_prompt_with_examples(examples)
        
        generation_log["system_prompt"] = system_prompt
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", TB_USER_PROMPT_FIRST),
        ])
        
        # Prepare prompt variables
        prompt_vars = {
            "user_request": user_request,
            "port_info": port_info,
            "module_name": ports['module_name'],
            "signal_declarations": signal_decls,
            "port_connections": port_conns,
        }
        
        generation_log["user_prompt_template"] = TB_USER_PROMPT_FIRST
        generation_log["prompt_variables"] = prompt_vars
        
        chain = prompt | llm
        
        # Format the actual prompt sent to LLM
        formatted_user_prompt = TB_USER_PROMPT_FIRST.format(**prompt_vars)
        generation_log["formatted_user_prompt"] = formatted_user_prompt
        generation_log["complete_llm_input"] = f"SYSTEM:\n{system_prompt}\n\nUSER:\n{formatted_user_prompt}"
        
        # Call LLM
        raw_tb = chain.invoke(prompt_vars).content
        
        generation_log["llm_raw_output"] = raw_tb
        
    else:
        # Refined attempt - use error templates
        error_summary = extract_error_summary(
            previous_error["results"],
            previous_error["failing_step"]
        )
        
        generation_log["previous_error_summary"] = error_summary
        generation_log["previous_failing_step"] = previous_error["failing_step"]
        
        # Generate targeted fixes using templates
        targeted_fixes = generate_targeted_error_prompt(error_summary, ports)
        
        generation_log["targeted_fixes"] = targeted_fixes
        
        # Use base prompt without examples on retry
        system_prompt = TB_SYSTEM_PROMPT
        generation_log["system_prompt"] = system_prompt
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", TB_USER_PROMPT_REFINED),
        ])
        
        # Prepare prompt variables
        prompt_vars = {
            "user_request": user_request,
            "failing_step": previous_error["failing_step"],
            "error_summary": error_summary,
            "targeted_fixes": targeted_fixes,
            "port_info": port_info,
            "module_name": ports['module_name'],
            "signal_declarations": signal_decls,
            "port_connections": port_conns,
        }
        
        generation_log["user_prompt_template"] = TB_USER_PROMPT_REFINED
        generation_log["prompt_variables"] = prompt_vars
        
        chain = prompt | llm
        
        # Format the actual prompt sent to LLM
        formatted_user_prompt = TB_USER_PROMPT_REFINED.format(**prompt_vars)
        generation_log["formatted_user_prompt"] = formatted_user_prompt
        generation_log["complete_llm_input"] = f"SYSTEM:\n{system_prompt}\n\nUSER:\n{formatted_user_prompt}"
        
        # Call LLM
        raw_tb = chain.invoke(prompt_vars).content
        
        generation_log["llm_raw_output"] = raw_tb

    # Sanitize and save
    try:
        tb_code = sanitize_verilog_code(raw_tb)
        generation_log["sanitization_success"] = True
    except RuntimeError as e:
        print(f"[agent] ERROR: {e}")
        generation_log["sanitization_success"] = False
        generation_log["sanitization_error"] = str(e)
        raise
    
    generation_log["testbench_code"] = tb_code
    generation_log["testbench_length"] = len(tb_code)
    
    tb_path.parent.mkdir(exist_ok=True)
    tb_path.write_text(tb_code)
    
    generation_log["testbench_file"] = str(tb_path)
    
    print(f"[agent] Generated testbench (iteration {iteration}, {len(tb_code)} chars)")
    
    # Preview
    lines = tb_code.split('\n')[:15]
    print("[agent] Testbench preview:")
    for line in lines:
        print(f"  {line}")
    
    return generation_log


def analyze_with_llm(llm, mode: Mode, user_request: str, results: dict, iteration: int = 0) -> Dict[str, Any]:
    """
    Quick analysis without heavy LLM usage.
    
    Returns:
        Dict with analysis metadata
    """
    
    analysis_log = {
        "iteration": iteration,
        "timestamp": datetime.now().isoformat(),
        "mode": mode,
    }
    
    if all(r.get('returncode') == 0 for r in results.values()):
        analysis_text = "✅ All verification steps passed successfully."
        analysis_log["success"] = True
        analysis_log["analysis_text"] = analysis_text
        return analysis_log
    
    failed_steps = [name for name, r in results.items() if r.get('returncode') != 0]
    
    if not failed_steps:
        analysis_text = "Verification completed."
        analysis_log["success"] = True
        analysis_log["analysis_text"] = analysis_text
        return analysis_log
    
    analysis_log["success"] = False
    analysis_log["failed_steps"] = failed_steps
    
    error_lines = []
    for step in failed_steps:
        stderr = results[step].get('stderr', '')
        if 'PINMISSING' in stderr:
            error_lines.append("- Missing port connections")
        elif 'WIDTH' in stderr:
            error_lines.append("- Bit width mismatch")
        elif 'Cannot find' in stderr:
            error_lines.append("- Module or signal not found")
        else:
            error_lines.append(f"- {step} failed")
    
    analysis_text = f"Failed at {', '.join(failed_steps)}:\n" + "\n".join(error_lines)
    analysis_log["analysis_text"] = analysis_text
    analysis_log["error_categories"] = error_lines
    
    return analysis_log


def save_to_memory(memory_data: dict, path: Path) -> None:
    """Save run data to memory with pretty formatting."""
    path.parent.mkdir(exist_ok=True)
    
    if path.exists():
        try:
            data = json.loads(path.read_text())
        except:
            data = []
    else:
        data = []
    
    memory_data["saved_at"] = datetime.now().isoformat()
    data.append(memory_data)
    
    # Save with pretty formatting (2-space indent)
    path.write_text(json.dumps(data, indent=2, default=str))
    
    print(f"[memory] Saved comprehensive log #{len(data)} to {path}")


def run_with_refinement(
    runner: RTLRunner,
    llm,
    user_request: str,
    mode: Mode,
    max_iterations: int = 3,
    test_case_id: int = None,
    test_case_name: str = None
) -> tuple[bool, str, dict, str, int]:
    """Run with automatic refinement and COMPLETE LOGGING."""
    
    # Initialize comprehensive run log
    run_log = {
        "test_case_id": test_case_id,
        "test_case_name": test_case_name,
        "user_request": user_request,
        "mode": mode,
        "max_iterations": max_iterations,
        "llm_model": "qwen2.5-coder:7b",
        "llm_temperature": 0.1,
        "started_at": datetime.now().isoformat(),
        "iterations": []  # Will contain detailed logs for each iteration
    }
    
    previous_error = None
    final_analysis = ""
    
    for iteration in range(max_iterations):
        print(f"\n{'='*70}")
        print(f"ITERATION {iteration + 1}/{max_iterations}")
        print(f"{'='*70}")
        
        # Initialize iteration log
        iteration_log = {
            "iteration_number": iteration,
            "started_at": datetime.now().isoformat(),
        }
        
        # Generate testbench
        print(f"\n[agent] Generating testbench (iteration {iteration})...")
        try:
            generation_log = generate_testbench(
                llm, 
                user_request, 
                runner.dut_file, 
                runner.tb_file,
                iteration=iteration,
                previous_error=previous_error
            )
            
            iteration_log["generation"] = generation_log
            
        except Exception as e:
            print(f"[agent] ERROR: {e}")
            
            iteration_log["generation_error"] = str(e)
            iteration_log["completed_at"] = datetime.now().isoformat()
            
            run_log["iterations"].append(iteration_log)
            run_log["final_status"] = "generation_failed"
            run_log["success"] = False
            run_log["iterations_used"] = iteration + 1
            run_log["completed_at"] = datetime.now().isoformat()
            
            # Save before returning
            memory_path = Path(__file__).resolve().parent / "agent_memory.json"
            save_to_memory(run_log, memory_path)
            
            return False, "testbench_generation", {}, str(e), iteration + 1
        
        # Run RTL flow
        print(f"\n[agent] Running Verilator flow in mode: {mode}")
        success, failing_step, results = runner.run_flow(mode)
        
        # Log simulation details
        iteration_log["simulation"] = {
            "mode": mode,
            "success": success,
            "failing_step": failing_step,
            "verilator_results": results,  # Complete stdout/stderr for each step
            "timestamp": datetime.now().isoformat(),
        }
        
        # Analyze
        print(f"[agent] Analyzing...")
        analysis_log = analyze_with_llm(llm, mode, user_request, results, iteration)
        final_analysis = analysis_log["analysis_text"]
        
        iteration_log["analysis"] = analysis_log
        iteration_log["completed_at"] = datetime.now().isoformat()
        
        # Save iteration log
        run_log["iterations"].append(iteration_log)
        
        if success:
            print(f"\n✅ SUCCESS on iteration {iteration + 1}!")
            
            run_log["final_status"] = "success"
            run_log["success"] = True
            run_log["iterations_used"] = iteration + 1
            run_log["final_analysis"] = final_analysis
            run_log["completed_at"] = datetime.now().isoformat()
            
            # Save complete log
            memory_path = Path(__file__).resolve().parent / "agent_memory.json"
            save_to_memory(run_log, memory_path)
            
            return True, "ok", results, final_analysis, iteration + 1
        
        print(f"\n❌ FAILED at step: {failing_step}")
        
        if iteration < max_iterations - 1:
            print(f"[agent] Will refine and retry...\n")
            
            error_summary = extract_error_summary(results, failing_step)
            print(f"--- Error Summary ---")
            print(error_summary[:300])
            print(f"---\n")
            
            previous_error = {
                "failing_step": failing_step,
                "results": results,
                "analysis": final_analysis
            }
            
            # Log refinement decision
            iteration_log["will_retry"] = True
            iteration_log["error_for_next_iteration"] = error_summary
        else:
            print(f"[agent] Max iterations reached.")
            iteration_log["will_retry"] = False
            iteration_log["reason"] = "max_iterations_reached"
    
    print(f"\n⚠️ Max iterations ({max_iterations}) reached without success")
    
    run_log["final_status"] = "max_iterations_reached"
    run_log["success"] = False
    run_log["iterations_used"] = max_iterations
    run_log["final_analysis"] = final_analysis
    run_log["completed_at"] = datetime.now().isoformat()
    
    # Save complete log
    memory_path = Path(__file__).resolve().parent / "agent_memory.json"
    save_to_memory(run_log, memory_path)
    
    return False, failing_step, results, final_analysis, max_iterations


def main():
    runner = RTLRunner()
    llm = get_llm()

    print("=== Hardware Simulation Agent (Complete Logging) ===")
    user_request = input("Your request [default: shift register]: ").strip()

    if not user_request:
        user_request = "8-bit shift register that shifts left on every clock and clears on reset"

    print("\nChoose mode:")
    print("  1) compile_only")
    print("  2) compile_elaborate")  
    print("  3) full_sim")
    mode_choice = input("Enter 1/2/3 [default=2]: ").strip()

    if mode_choice == "1":
        mode: Mode = "compile_only"
    elif mode_choice == "3":
        mode = "full_sim"
    else:
        mode = "compile_elaborate"

    success, failing_step, results, analysis, iterations_used = run_with_refinement(
        runner, llm, user_request, mode, max_iterations=3
    )

    print("\n" + "="*70)
    print("========== FINAL SUMMARY ==========")
    print("="*70)
    print(f"Success: {'✅ PASS' if success else '❌ FAIL'}")
    print(f"Iterations: {iterations_used}/3")
    print(f"Analysis: {analysis}")
    print("="*70)


if __name__ == "__main__":
    main()