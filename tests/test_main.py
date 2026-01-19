import json
import pytest
from click.testing import CliRunner

from decisiontrace.cli import cli
from decisiontrace import hasher, logger, replay

# Sample data for testing
DECISION_1 = {
    "model": "test-model-1", "config": {"temp": 1}, "prompt": "prompt 1",
    "context_sources": ["c1"], "output": "output 1", "confidence": 0.1
}
DECISION_2 = {
    "model": "test-model-2", "config": {"temp": 2}, "prompt": "prompt 2",
    "context_sources": ["c2"], "output": "output 2", "confidence": 0.2
}

@pytest.fixture(autouse=True)
def isolated_log(tmp_path, monkeypatch):
    """Fixture to ensure each test uses a temporary, isolated log file."""
    d = tmp_path / "logs"
    d.mkdir()
    log_file = d / "decision_log.jsonl"
    
    # Use monkeypatch to replace the LOG_FILE constant in all modules
    monkeypatch.setattr(logger, "LOG_FILE", log_file)
    monkeypatch.setattr(hasher, "LOG_FILE", log_file)
    monkeypatch.setattr(replay, "LOG_FILE", log_file)
    
    return log_file

def test_log_and_replay(isolated_log):
    """Test logging a decision and then replaying it."""
    runner = CliRunner()
    
    # Create a decision file
    decision_file = isolated_log.parent / "decision.json"
    with open(decision_file, "w") as f:
        json.dump(DECISION_1, f)

    # 1. Log the decision
    result_log = runner.invoke(cli, ["log", str(decision_file)])
    assert result_log.exit_code == 0
    assert "Decision successfully logged." in result_log.output

    # Extract decision ID from output
    decision_id = [line for line in result_log.output.split('\n') if 'Decision ID' in line][0].split(': ')[1].strip()

    # 2. Replay the decision
    result_replay = runner.invoke(cli, ["replay", decision_id])
    assert result_replay.exit_code == 0
    assert "Decision Replay" in result_replay.output
    assert DECISION_1["model"] in result_replay.output
    assert DECISION_1["output"] in result_replay.output

def test_verify_valid_chain(isolated_log):
    """Test that the verify command passes on a valid chain."""
    runner = CliRunner()
    
    # Log two decisions
    for i, decision in enumerate([DECISION_1, DECISION_2]):
        decision_file = isolated_log.parent / f"decision{i}.json"
        with open(decision_file, "w") as f:
            json.dump(decision, f)
        runner.invoke(cli, ["log", str(decision_file)])
    
    # Verify the chain
    result_verify = runner.invoke(cli, ["verify"])
    assert result_verify.exit_code == 0
    assert "Success: The decision log is intact" in result_verify.output

def test_verify_tampered_chain(isolated_log):
    """Test that the verify command fails on a tampered chain."""
    runner = CliRunner()

    # Log two decisions
    for i, decision in enumerate([DECISION_1, DECISION_2]):
        decision_file = isolated_log.parent / f"decision{i}.json"
        with open(decision_file, "w") as f:
            json.dump(decision, f)
        result = runner.invoke(cli, ["log", str(decision_file)])
        assert result.exit_code == 0
    
    # Manually tamper with the log file
    with open(isolated_log, "r") as f:
        lines = f.readlines()
    
    # Corrupt the output of the first record
    record_1 = json.loads(lines[0])
    record_1["output"] = "TAMPERED OUTPUT"
    lines[0] = json.dumps(record_1) + "\n"

    with open(isolated_log, "w") as f:
        f.writelines(lines)
    
    # Verify the chain should now fail
    result_verify = runner.invoke(cli, ["verify"])
    assert result_verify.exit_code != 0 # Should abort
    assert "Critical: The decision log has been tampered with" in result_verify.output
    assert "Tampering Detected on line 1" in result_verify.output
    assert "Integrity Error on line 2" in result_verify.output
