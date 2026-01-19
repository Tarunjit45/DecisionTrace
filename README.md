# DecisionTrace: An AI Decision Audit Log

(Project name: DecisionTrace)

This is not logging. This is post-hoc accountability for AI decisions.

## 0️⃣ Reality You Need to Accept

Right now, most AI systems:

- Make decisions
- Affect users
- Influence outcomes

…and cannot explain yesterday’s decision.

That’s unacceptable. And regulation is coming whether people like it or not.

## 1️⃣ The Exact Problem You’re Solving

“When an AI system makes a decision, can we later reconstruct how and why it happened?”

Not:

- “What was the output?”
- “What model did we use?”

But:

- What inputs influenced it
- What context was used
- What assumptions were made
- What version of the system was running

This is the difference between toy AI and deployable AI.

## 2️⃣ What You Are NOT Building

Be strict.

- ❌ Chat history viewer
- ❌ Analytics dashboard
- ❌ Model monitoring UI
- ❌ Ethics essay

If you drift into those, you have failed.

## 3️⃣ What You ARE Building

An append-only decision audit layer that records:

- **Prompt**: The input that triggered the decision.
- **Context Sources**: A list of data/document sources the AI used.
- **Model + Config**: The exact model and its settings (e.g., temperature).
- **Output**: The result of the decision.
- **Confidence / Risk Tags**: Metadata about the output's reliability.
- **Timestamp**: When the decision was made.
- **Integrity Hash**: A cryptographic hash to ensure the record is tamper-evident.

Think: **Git commit history for AI decisions.**

## 4️⃣ Minimal but Serious Architecture
```
decisiontrace/
│
├── logger.py        # Append-only decision logger
├── hasher.py        # Integrity & chaining
├── schema.py        # Decision record Pydantic schema
├── replay.py        # Reconstruct a decision
├── cli.py           # Command-Line Interface
├── logs/            # Directory for log files
│   └── .gitkeep
├── requirements.txt
└── README.md
```

If this looks “simple”, good. Simple + correct beats clever.

## 5️⃣ Decision Record Schema (Non-Negotiable)

Every decision **must** log this structure, enforced by `schema.py`:

```json
{
  "decision_id": "uuid",
  "timestamp": "ISO-8601",
  "model": "llama3.2:1b",
  "config": {
    "temperature": 0.7
  },
  "prompt": "...",
  "context_sources": [
    "policy_v3.txt",
    "user_input"
  ],
  "output": "...",
  "confidence": 0.62,
  "risk_flags": ["hallucination_risk"],
  "prev_hash": "abc123...",
  "hash": "def456..."
}
```

If anything here is missing, it’s not auditable.

## 6️⃣ Integrity Chain (This Is the Differentiator)

Each record:

1.  Hashes its own contents.
2.  Includes the hash of the **previous** record.

This creates a cryptographic chain, providing:

-   **Tamper Evidence**: If a record is altered, its hash will no longer match the `prev_hash` of the next record.
-   **Chronological Integrity**: The order of decisions is locked in.

You’re not building blockchain. You’re building basic honesty guarantees.

## 7️⃣ Replay Capability (Critical)

An auditor must be able to run a command to see the full context of any decision.

**If an AI decision can’t be reconstructed, it can’t be defended.**

## 8️⃣ How to Use

### Installation

Clone the repository and install it in editable mode with the required dependencies:
```bash
pip install -e .
```
This will install the `decisiontrace` command in your environment.

### 1. Log a Decision

Create a JSON file (e.g., `decision.json`) with the details of the AI's action:

```json
{
  "model": "llama3.2:1b-instruct",
  "config": {
    "temperature": 0.7,
    "max_tokens": 1024
  },
  "prompt": "Should we approve a loan for user_id 12345?",
  "context_sources": [
    "internal_policy_v4.1.pdf",
    "user_credit_report_-345.json"
  ],
  "output": "Approval recommended based on high credit score and low debt-to-income ratio.",
  "confidence": 0.95,
  "risk_flags": ["user_pii_involved"]
}
```

Now, log it using the CLI:

```bash
decisiontrace log decision.json
```
Output:
```
Decision successfully logged.
  Decision ID: <some-uuid>
  Record Hash: <sha256-hash>
```
This appends the decision to `logs/decision_log.jsonl`, securely chained to the previous entry.

### 2. Replay (Audit) a Decision

Use the `decision_id` from the log output to replay it:

```bash
decisiontrace replay <decision_id>
```

### 3. Verify the Entire Log

To check the integrity of the entire log file for tampering:

```bash
decisiontrace verify
```
The tool will display a success message or a critical error if the chain is broken.
