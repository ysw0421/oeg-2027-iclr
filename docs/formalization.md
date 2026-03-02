# Formalization: Objective--Execution Gap (OEG)

## 1. Setting: Tool-Using Agent as a Constrained Decision Process

We consider an agent interacting with an environment through tool calls.
At each timestep t ∈ {1,...,T}, the agent observes state s_t ∈ S,
chooses an action a_t ∈ A, and the environment transitions to s\_{t+1}.

### Tool-call action

An action is a tool invocation with structured arguments: a_t = (tool_t,
args_t, confirmed_t).

The environment implements each tool as a transition operator: s\_{t+1}
\~ T(s_t, a_t).

### Trajectory

A trajectory of length T is: τ = (s_1, a_1, s_2, a_2, ..., s_T, a_T,
s\_{T+1}).

------------------------------------------------------------------------

## 2. Objective Success vs Execution Correctness

### Task objective (Success)

Each task defines an objective predicate on the terminal state (or
trajectory): S(τ) ∈ {0,1}.

### Execution constraints (Violations)

Separately from the objective, API and environment constraints impose
rules. We represent violations as events: V(τ) = {v_1, v_2, ..., v_K},

where each violation has a type t(v_k) (e.g., schema missing field,
missing confirmation, duplicate side-effect, precondition failure).

------------------------------------------------------------------------

## 3. Execution Violation Cost and Execution Correctness Score (ECS)

### Weighted violation cost

Let w assign a nonnegative severity weight to each violation type.

C(τ) = Σ w(t(v))

### Execution Correctness Score

ECS(τ) = f(C(τ)) ∈ (0,1\]

Current implementation: ECS = 1 / (1 + C)

------------------------------------------------------------------------

## 4. Objective--Execution Gap (OEG)

Core metric: OEG(ε) = P(ECS(τ) \< ε \| S(τ) = 1)

Additional metrics: μ_succ = E\[ECS(τ) \| S(τ) = 1\] ρ = corr(S(τ),
ECS(τ))

------------------------------------------------------------------------

## 5. Distribution Shift as Constraint Drift

Constraint weights may change: w → w'

ECS(τ; w) = f( Σ w(t(v)) ) ECS(τ; w') = f( Σ w'(t(v)) )

Shift effect: Δμ_succ = E\[ECS(τ; w') \| S=1\] - E\[ECS(τ; w) \| S=1\]

------------------------------------------------------------------------

## 6. Structural Hypothesis

There exist agent policies and constraint regimes such that:

-   P(S=1) is high
-   OEG(ε) is nontrivial
-   Under constraint drift, P(S=1) remains stable while μ_succ
    decreases.

This forms the empirical and theoretical core of the OEG framework.
