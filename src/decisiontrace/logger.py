import json
from typing import Dict, Any, List, Optional

from . import LOG_FILE
from .hasher import get_last_hash, calculate_hash
from .schema import DecisionRecord

def log_decision(
    model: str,
    config: Dict[str, Any],
    prompt: str,
    context_sources: List[str],
    output: str,
    confidence: Optional[float] = None,
    risk_flags: Optional[List[str]] = None,
) -> DecisionRecord:
    """
    Constructs, validates, and logs a new decision record.

    This function orchestrates the creation of a decision record, ensuring it's
    correctly formatted, hashed, and appended to the audit log.

    Args:
        model: The model used for the decision.
        config: The model configuration.
        prompt: The prompt that triggered the decision.
        context_sources: A list of context sources.
        output: The model's output.
        confidence: The model's confidence score.
        risk_flags: Any identified risk flags.

    Returns:
        The validated and logged DecisionRecord object.
    """
    if risk_flags is None:
        risk_flags = []

    # 1. Get the hash of the previous record to create the chain.
    prev_hash = get_last_hash()

    # 2. Assemble the record data that we know.
    # We leave out decision_id, timestamp, and hash for now.
    partial_data = {
        "model": model,
        "config": config,
        "prompt": prompt,
        "context_sources": context_sources,
        "output": output,
        "confidence": confidence,
        "risk_flags": risk_flags or [],
        "prev_hash": prev_hash,
    }

    # 3. Use the Pydantic model to generate the timestamp and decision_id.
    # We create a temporary record to get these generated values.
    # A dummy hash is needed to satisfy the schema during this temporary creation.
    temp_record = DecisionRecord(**partial_data, hash="dummy_hash")
    
    # 4. Now, build the full data set for hashing, including the generated fields.
    record_data_for_hashing = partial_data.copy()
    record_data_for_hashing["decision_id"] = temp_record.decision_id
    record_data_for_hashing["timestamp"] = temp_record.timestamp

    # 5. Calculate the hash of the nearly complete record's content.
    current_hash = calculate_hash(record_data_for_hashing)

    # 6. Create the final, validated record object with the real hash.
    final_record = DecisionRecord(
        **record_data_for_hashing,
        hash=current_hash,
    )

    # 7. Append the record to the log file.
    # The .jsonl format (JSON Lines) is robust for append-only logs.
    LOG_FILE.parent.mkdir(exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(final_record.json() + "\n")

    return final_record
