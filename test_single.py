#!/usr/bin/env python3
"""Test a single case by ID with COMPLETE LOGGING."""

import sys
from pathlib import Path
from datetime import datetime
from test_cases import EASY_CASES, MEDIUM_CASES, HARD_CASES, EXPERT_CASES, save_test_case_to_file
from test_simulation_agent import run_with_refinement, RTLRunner, get_llm, save_to_memory

def test_single(test_id: int):
    """Run a single test case by ID with complete memory logging."""
    
    all_cases = EASY_CASES + MEDIUM_CASES + HARD_CASES + EXPERT_CASES
    test_case = next((tc for tc in all_cases if tc.id == test_id), None)
    
    if not test_case:
        print(f"❌ Test case {test_id} not found!")
        return
    
    print(f"="*80)
    print(f"TEST CASE #{test_id}: {test_case.name}")
    print(f"Difficulty: {test_case.difficulty.upper()}")
    print(f"="*80)
    print(f"\nDescription:")
    print(f"  {test_case.test_description}")
    print(f"\nExpected: {test_case.expected_result}")
    print(f"\n{'='*80}\n")
    
    # Setup
    runner = RTLRunner()
    save_test_case_to_file(test_case, runner.project_root)
    llm = get_llm()
    
    # Prepare memory structure
    test_memory = {
        "test_case_id": test_case.id,
        "test_case_name": test_case.name,
        "difficulty": test_case.difficulty,
        "test_description": test_case.test_description,
        "dut_code": test_case.dut_code,
        "expected_result": test_case.expected_result,
        "notes": test_case.notes,
        "timestamp_start": datetime.now().isoformat(),
    }
    
    # Run
    success, failing_step, results, analysis, iters = run_with_refinement(
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
    
    # Save to memory
    memory_path = Path("single_test_memory.json")
    save_to_memory(test_memory, memory_path)
    
    # Summary
    print(f"\n{'='*80}")
    print(f"RESULT: {'✅ PASS' if success else '❌ FAIL'}")
    print(f"Iterations: {iters}/3")
    if not success:
        print(f"Failed at: {failing_step}")
    print(f"{'='*80}")
    print(f"\n📁 Complete logs saved to: {memory_path}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_id = int(sys.argv[1])
    else:
        print("Usage: python test_single.py <test_id>")
        print("Example: python test_single.py 6")
        sys.exit(1)
    
    test_single(test_id)