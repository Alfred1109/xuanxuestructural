import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
START_SCRIPT = REPO_ROOT / "start.sh"
STOP_SCRIPT = REPO_ROOT / "stop.sh"


class TestServiceScriptSafety(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(prefix="xuanxue-service-script-test-")
        self.root = Path(self.temp_dir.name)
        self.bin_dir = self.root / "bin"
        self.bin_dir.mkdir()
        self.log_path = self.root / "mock-lsof.log"

    def tearDown(self):
        self.temp_dir.cleanup()

    def env(self):
        env = os.environ.copy()
        env["PATH"] = str(self.bin_dir) + os.pathsep + env.get("PATH", "/usr/bin:/bin")
        env["MOCK_LSOF_LOG"] = str(self.log_path)
        return env

    def run_bash(self, script, env=None):
        return subprocess.run(
            ["bash", "-c", script],
            cwd=REPO_ROOT,
            env=env or self.env(),
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )

    def start_function_prefix(self):
        source = START_SCRIPT.read_text(encoding="utf-8")
        return source.split("# 加载 AI 环境变量", 1)[0]

    def stop_function_prefix(self):
        source = STOP_SCRIPT.read_text(encoding="utf-8")
        return source.split("# 停止后端服务", 1)[0]

    def install_mock_lsof(self):
        mock_lsof = self.bin_dir / "lsof"
        mock_lsof.write_text(
            "#!/bin/sh\n"
            "printf '%s\\n' \"$*\" >> \"$MOCK_LSOF_LOG\"\n"
            "case \" $* \" in\n"
            "  *' -sTCP:LISTEN '*) if [ -n \"${MOCK_LSOF_TEST_PID:-}\" ]; then printf '%s\\n' \"$MOCK_LSOF_TEST_PID\"; exit 0; else exit 1; fi ;;\n"
            "  *) printf '4242\\n4343\\n'; exit 0 ;;\n"
            "esac\n",
            encoding="utf-8",
        )
        mock_lsof.chmod(0o755)

    def test_lsof_pid_discovery_filters_to_tcp_listeners(self):
        self.install_mock_lsof()
        harness = self.start_function_prefix() + "\n" + """
        pids=$(list_port_pids 8123)
        [ "$pids" = "4242" ] || exit 21
        is_port_in_use 8123 || exit 22
        """
        env = self.env()
        env["MOCK_LSOF_TEST_PID"] = "4242"
        result = self.run_bash(harness, env)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        calls = self.log_path.read_text(encoding="utf-8").splitlines()
        self.assertGreaterEqual(len(calls), 2)
        self.assertTrue(all("-sTCP:LISTEN" in call and "-iTCP:8123" in call for call in calls))

    def test_start_cleanup_does_not_probe_frontend_port_in_nginx_mode(self):
        self.install_mock_lsof()
        harness = self.start_function_prefix() + "\n" + """
        FRONTEND_MODE=nginx
        BACKEND_PORT=18002
        FRONTEND_PORT="$TEST_FRONTEND_PORT"
        BACKEND_PID_FILE="$TEST_DIR/backend.pid"
        FRONTEND_PID_FILE="$TEST_DIR/frontend.pid"
        cleanup_existing_services
        """
        for port in ("8003", "19003"):
            with self.subTest(frontend_port=port):
                self.log_path.write_text("", encoding="utf-8")
                env = self.env()
                env["TEST_DIR"] = str(self.root)
                env["TEST_FRONTEND_PORT"] = port
                result = self.run_bash(harness, env)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                calls = self.log_path.read_text(encoding="utf-8").splitlines()
                self.assertTrue(calls)
                self.assertTrue(all("-iTCP:18002" in call for call in calls))
                self.assertFalse(any(f"-iTCP:{port}" in call for call in calls))

    def test_stop_frontend_branch_does_not_probe_nginx_default_or_configured_port(self):
        source = STOP_SCRIPT.read_text(encoding="utf-8")
        end_marker = '\necho ""\necho "======================================"\necho "  服务已停止"'
        frontend_start = source.index('if [ -f "$FRONTEND_PID_FILE" ]; then')
        frontend_branch = source[frontend_start:].split(end_marker, 1)[0]
        harness = self.stop_function_prefix() + "\nFRONTEND_PID_FILE=\"$TEST_PID_FILE\"\n" + frontend_branch + "\n"
        self.install_mock_lsof()
        for port in ("8003", "19003"):
            with self.subTest(frontend_port=port):
                self.log_path.write_text("", encoding="utf-8")
                env = self.env()
                env["FRONTEND_MODE"] = "nginx"
                env["FRONTEND_PORT"] = port
                env["TEST_PID_FILE"] = str(self.root / "missing-frontend.pid")
                result = self.run_bash(harness, env)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertFalse(self.log_path.exists() and self.log_path.read_text(encoding="utf-8"))

    def test_pid_stop_helpers_reject_a_live_process_outside_project_directory(self):
        child_cwd = self.root / "unrelated-process"
        child_cwd.mkdir()
        child = subprocess.Popen(["sleep", "60"], cwd=child_cwd)
        try:
            time.sleep(0.05)
            harness = self.start_function_prefix() + "\n" + self.stop_function_prefix() + "\n" + """
            kill() { printf '%s\\n' "$*" >> "$TEST_KILL_LOG"; }
            sleep() { :; }
            expected_dir="$SCRIPT_DIR/xuanxue-web/frontend"
            if ensure_process_stopped "$TEST_PID" "frontend" "$expected_dir"; then exit 31; fi
            if stop_pid_if_running "$TEST_PID" "frontend" "$expected_dir"; then exit 32; fi
            [ ! -s "$TEST_KILL_LOG" ] || exit 33
            """
            env = self.env()
            env["TEST_PID"] = str(child.pid)
            env["TEST_KILL_LOG"] = str(self.root / "kill.log")
            result = self.run_bash(harness, env)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse(Path(env["TEST_KILL_LOG"]).exists())
            self.assertIsNone(child.poll(), "guarded unrelated process should remain alive")
        finally:
            child.terminate()
            child.wait(timeout=3)


if __name__ == "__main__":
    unittest.main()
