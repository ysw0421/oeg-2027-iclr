# Objective–Execution Gap (OEG)
Trajectory-level correctness for tool-using LLM agents  
Target: ICLR 2027 (Main Track, S-tier ambition)

---

## 🎯 Core Hypothesis

Success-based evaluation systematically overestimates reliability in tool-using agents.

We define the **Objective–Execution Gap (OEG)** as the discrepancy between:
- Output-level success
- Execution-level correctness

---

## 🚀 Long-Term Vision (2027 Goal)

By 2027, this project aims to:

1. Formally define OEG
2. Empirically demonstrate large-scale OEG across multiple agent setups
3. Analyze structural causes of OEG
4. Propose mitigation strategies
5. Release a benchmark for trajectory-level correctness

The goal is not incremental improvement, but **evaluation reformulation** in agent research.

---

## 🗺 Research Roadmap

### Phase 1 (Mar–Jun 2026)
- Validate existence of OEG
- Build sandbox + task-based success
- Generate failure library
- Produce Success vs ECS separation plots

### Phase 2 (Jul–Dec 2026)
- Conduct distribution shift experiments
- Identify structural causes
- Develop contract-aware mitigation
- Expand to at least one public benchmark

### Phase 3 (Jan–Aug 2027)
- Refine formalization
- Scale experiments
- Strengthen theoretical framing
- Internal reviews and iteration

### Submission Target
ICLR 2027 (September submission cycle)

---

## 📌 Current Status (March 2026)

- Sandbox environment implemented
- Violation detection working
- ECS scoring implemented
- Task-based success implemented
- Initial OEG separation observed

Current focus:
→ Strengthen empirical evidence
→ Expand task coverage
→ Stress-test OEG under policy shifts

---

## 🔁 Operating Principle

We prioritize:
- Evidence over speculation
- Iteration over perfection
- Structural insight over engineering

---

