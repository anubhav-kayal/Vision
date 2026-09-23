# Week 2 Day 5 - Next-Best-Evidence Selection

The V0 selector uses a transparent heuristic rather than formal Bayesian information gain. Each candidate records whether documentation supports it, which hypotheses it discriminates, whether it is already available or requested, whether it is realistic for a technician, its safety status, a score, and a human-readable selection reason.

The selector prefers documented, not-yet-available, not-yet-requested observations that test multiple hypotheses. `SAFETY_BLOCK` and `UNKNOWN` candidates are not selected; `REQUIRES_SUPERVISION` candidates are allowed into the candidate list but receive a penalty and retain their explicit boundary.

This is a safety placeholder, not a production safety engine. It does not determine whether a technician is qualified, whether a site is isolated, or whether local procedures permit an action. Future workflow code must enforce those decisions.
