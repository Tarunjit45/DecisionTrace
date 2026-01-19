import hashlib
import json
from typing import Optional, Dict, Any

from . import LOG_FILE

def get_last_hash() -> str:
    """
    Retrieves the hash of the last decision record in the log.
    
    Returns:
        The hash of the last record, or a default 'genesis' hash if the log is empty.
    """
    if not LOG_FILE.exists() or LOG_FILE.stat().st_size == 0:
        # Return a consistent starting hash for the very first record
        return hashlib.sha256("genesis_block".encode()).hexdigest()
    
    last_line = ""
    # More robust way to get the last line of a file
    with open(LOG_FILE, 'rb') as f:
        try:
            f.seek(-2, 2)  # Go to the end of file, minus two bytes to skip the last newline
            while f.read(1) != b'\n':
                f.seek(-2, 1)
        except OSError:
            f.seek(0)
        last_line = f.readline().decode()

    if not last_line:
        return hashlib.sha256("genesis_block".encode()).hexdigest()

    try:
        last_record = json.loads(last_line)
        return last_record.get("hash", hashlib.sha256("genesis_block".encode()).hexdigest())
    except json.JSONDecodeError:
        # Handle case where last line might be corrupted
        # For a serious audit system, this should trigger an alert.
        # For this example, we'll fall back to the genesis hash, but in a real system,
        # you might want to lock the log file and require manual intervention.
        print("Warning: Could not decode the last log entry. The integrity chain may be broken.")
        return hashlib.sha256("genesis_block".encode()).hexdigest()


def calculate_hash(record_data: Dict[str, Any]) -> str:
    """
    Calculates the SHA-256 hash of a decision record.
    
    The hash is based on a stable JSON representation of the record's content,
    excluding the hash itself to prevent a recursive problem.
    
    Args:
        record_data: The decision record data as a dictionary.
        
    Returns:
        The hex digest of the hash.
    """
    # Create a stable, sorted JSON string to ensure consistent hashing
    # Exclude 'hash' field from the hash calculation itself
    hashable_data = {k: v for k, v in record_data.items() if k != 'hash'}
    
    encoded_string = json.dumps(hashable_data, sort_keys=True).encode()
    return hashlib.sha256(encoded_string).hexdigest()

def verify_chain() -> bool:
    """
    Verifies the integrity of the entire decision log.

    This function reads all records, recalculates their hashes, and checks
    that the chain of previous hashes is unbroken.

    Returns:
        True if the chain is valid, False otherwise.
    """
    if not LOG_FILE.exists() or LOG_FILE.stat().st_size == 0:
        print("Log file is empty or does not exist. Nothing to verify.")
        return True

    previous_hash = hashlib.sha256("genesis_block".encode()).hexdigest()
    is_valid = True

    with open(LOG_FILE, "r") as f:
        for i, line in enumerate(f):
            line_num = i + 1
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                print(f"❌ Error: Invalid JSON on line {line_num}.")
                is_valid = False
                continue

            # 1. Check if the previous hash links correctly.
            if record["prev_hash"] != previous_hash:
                print(f"❌ Integrity Error on line {line_num}:")
                print(f"   Record's prev_hash: {record['prev_hash']}")
                print(f"   Actual prev_hash:   {previous_hash}")
                is_valid = False

            # 2. Check if the record's content is untampered.
            recalculated_hash = calculate_hash(record)
            if record["hash"] != recalculated_hash:
                print(f"❌ Tampering Detected on line {line_num}:")
                print(f"   Record's hash:      {record['hash']}")
                print(f"   Recalculated hash:  {recalculated_hash}")
                is_valid = False
            
            previous_hash = recalculated_hash

    return is_valid
