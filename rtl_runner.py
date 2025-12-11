# File: rtl_runner.py
import subprocess
from pathlib import Path
from typing import Dict, Literal, Tuple

Mode = Literal["compile_only", "compile_elaborate", "full_sim"]


class RTLRunner:
    """
    Thin wrapper around Verilator with three modes:
      1) compile_only      -> compile_dut + compile_tb
      2) compile_elaborate -> compile_dut + elaborate_dut + compile_tb
      3) full_sim          -> compile_dut + elaborate_dut + compile_tb + run_simulation
    """

    def __init__(self) -> None:
        # Project root = folder where this file lives
        self.project_root = Path(__file__).resolve().parent
        self.rtl_dir = self.project_root / "rtl"
        self.tb_dir = self.project_root / "tb"
        self.logs_dir = self.project_root / "logs"
        self.logs_dir.mkdir(exist_ok=True)

        # Default DUT/TB filenames
        self.dut_file = self.rtl_dir / "my_dut.v"
        self.tb_file = self.tb_dir / "generated_tb.sv"

    # ----------------- low-level helper -----------------

    def _run_cmd(self, cmd: list[str], log_name: str) -> Dict:
        """Run a shell command, capture stdout/stderr and save to logs."""
        result = subprocess.run(
            cmd,
            cwd=self.project_root,
            capture_output=True,
            text=True,
        )

        log_path = self.logs_dir / f"{log_name}.log"
        with open(log_path, "w") as f:
            f.write(f"$ {' '.join(cmd)}\n\n")
            f.write("=== STDOUT ===\n")
            f.write(result.stdout or "")
            f.write("\n\n=== STDERR ===\n")
            f.write(result.stderr or "")

        return {
            "step": log_name,
            "cmd": " ".join(cmd),
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "log_path": str(log_path),
        }

    # ----------------- individual steps -----------------

    def compile_dut(self) -> Dict:
        """Verilator lint for DUT."""
        if not self.dut_file.exists():
            return {
                "step": "compile_dut",
                "cmd": "",
                "returncode": 1,
                "stdout": "",
                "stderr": f"DUT file not found: {self.dut_file}",
                "log_path": "",
            }

        cmd = ["verilator", "--lint-only", str(self.dut_file)]
        print(f"[rtl_runner] Running: {' '.join(cmd)}")
        return self._run_cmd(cmd, "compile_dut")

    def elaborate_dut(self) -> Dict:
        """
        Elaboration step.

        For simplicity, we just run verilator with --cc on the DUT.
        (In a more advanced flow you’d add TB, sim_main, etc.)
        """
        if not self.dut_file.exists():
            return {
                "step": "elaborate_dut",
                "cmd": "",
                "returncode": 1,
                "stdout": "",
                "stderr": f"DUT file not found: {self.dut_file}",
                "log_path": "",
            }

        cmd = [
            "verilator",
            "--cc",
            str(self.dut_file),
        ]
        print(f"[rtl_runner] Running: {' '.join(cmd)}")
        return self._run_cmd(cmd, "elaborate_dut")

    def compile_tb(self) -> Dict:
        """
        Compile testbench with proper flags.
        
        Key fixes:
        1. Add -I flag to include DUT directory
        2. Add --timing flag for delay support
        3. Include both DUT and TB files
        """
        if not self.tb_file.exists():
            return {
                "step": "compile_tb",
                "cmd": "",
                "returncode": 1,
                "stdout": "",
                "stderr": f"Testbench file not found: {self.tb_file}",
                "log_path": "",
            }
        
        if not self.dut_file.exists():
            return {
                "step": "compile_tb",
                "cmd": "",
                "returncode": 1,
                "stdout": "",
                "stderr": f"DUT file not found: {self.dut_file}",
                "log_path": "",
            }

        # FIX: Include DUT directory and add timing support
        cmd = [
            "verilator",
            "--lint-only",
            "--timing",                    # NEW: Support delays (#10, forever, etc.)
            "-I" + str(self.rtl_dir),     # NEW: Tell Verilator where to find my_dut
            str(self.dut_file),           # NEW: Include DUT file
            str(self.tb_file)             # Testbench file
        ]
        
        print(f"[rtl_runner] Running: {' '.join(cmd)}")
        return self._run_cmd(cmd, "compile_tb")

    def run_simulation(self) -> Dict:
        """
        Minimal placeholder simulation step.

        If you later create a full Verilator C++ sim, you can replace this
        with the usual:
          verilator --cc --exe ...
          make -C obj_dir ...
          obj_dir/V<top>
        """
        # For now just a “fake” success so the agent workflow is complete.
        stdout = "Simulation step not fully implemented yet; this is a stub.\n"
        return {
            "step": "run_simulation",
            "cmd": "(stub) no command run",
            "returncode": 0,
            "stdout": stdout,
            "stderr": "",
            "log_path": "",
        }

    # ----------------- high-level flow -----------------

    def run_flow(self, mode: Mode) -> Tuple[bool, str, Dict[str, Dict]]:
        """
        Run the selected mode and return:
          (success_flag, failing_step_name or 'ok', results_dict_per_step)
        """
        results: Dict[str, Dict] = {}

        # 1) compile_dut
        results["compile_dut"] = self.compile_dut()
        if results["compile_dut"]["returncode"] != 0:
            return False, "compile_dut", results

        # Mode 1: compile_only
        if mode == "compile_only":
            results["compile_tb"] = self.compile_tb()
            if results["compile_tb"]["returncode"] != 0:
                return False, "compile_tb", results
            return True, "ok", results

        # 2) elaborate_dut
        results["elaborate_dut"] = self.elaborate_dut()
        if results["elaborate_dut"]["returncode"] != 0:
            return False, "elaborate_dut", results

        # compile_elaborate: no sim
        if mode == "compile_elaborate":
            results["compile_tb"] = self.compile_tb()
            if results["compile_tb"]["returncode"] != 0:
                return False, "compile_tb", results
            return True, "ok", results

        # Mode 3: full_sim
        results["compile_tb"] = self.compile_tb()
        if results["compile_tb"]["returncode"] != 0:
            return False, "compile_tb", results

        results["run_simulation"] = self.run_simulation()
        if results["run_simulation"]["returncode"] != 0:
            return False, "run_simulation", results

        return True, "ok", results
