from agentic_patterns_lab import JsonMemory


def test_json_memory_round_trip(tmp_path) -> None:
    memory = JsonMemory(tmp_path / "state.json")
    memory.set("status", "ready")
    memory.append("events", {"kind": "created"})
    assert memory.get("status") == "ready"
    assert memory.get("events") == [{"kind": "created"}]
