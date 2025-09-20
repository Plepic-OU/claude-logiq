Title: Create Unit Tests

You are to generate unit tests for the provided code or description.

Scope & Intent:
- Focus ONLY on true unit tests (single unit: function, class, module).
- No external I/O, network, filesystem, time, randomness (unless explicitly allowed—then isolate).

Before Writing Tests (perform mentally):
1. Summarize the unit's responsibilities.
2. Identify pure vs impure parts.
3. Enumerate: happy paths, edge cases, invalid inputs, boundary conditions, idempotency, error propagation.
4. Detect invariants and contracts (preconditions, postconditions).
5. Highlight potential ambiguity or undefined behavior.

Test Style & Structure:
- Use clear, intention-revealing names: methodUnderTest_condition_expectedOutcome
- Prefer Arrange / Act / Assert (AAA). Keep sections visually distinct.
- One logical assertion per test concept; multiple asserts allowed only if validating one scenario.
- Keep tests deterministic. Replace nondeterminism (time, UUID, randomness) with injected fakes.
- Mock/stub ONLY external collaborators; avoid over-mocking internal details.
- Avoid asserting on implementation details (private state, call counts) unless behaviorally necessary.
- Prefer value equality over structural coincidence (no magic numbers without explanation).

Coverage Philosophy:
- Aim for meaningful path & branch coverage, not just a % metric.
- Cover: nominal case, each branch, failure modes, edge boundaries, null/empty/min/max, ordering sensitivity (if any), immutability or mutation effects.
- For algorithms: include complexity trigger (e.g., large input), degenerate input, representative typical input.

Negative & Defensive Cases:
- Invalid arguments raise correct errors.
- Ensure no silent swallowing of exceptions (unless specified).
- Test that error messages or codes are precise (if part of contract).

Optional Enhancements (include only if relevant):
- Property-based style cases (describe properties, do not implement engine unless allowed).
- Snapshot tests: avoid unless stable, deterministic representation.
- Table-driven tests: when many similar variations exist.

Anti-Patterns to Avoid:
- Sleep-based timing.
- Depending on test execution order.
- Overlapping responsibilities between tests.
- Duplicating production logic inside tests.
- Blindly mocking every dependency.
- Copy-pasting large fixtures—centralize or generate minimal fixtures.

If Requirements Are Ambiguous:
- Output: "Assumptions" section listing each assumption.
- Do NOT fabricate undocumented behavior; request clarification if critical.

Output Format:
1. Brief "Test Plan" summary (bulleted).
2. List of assumptions (if any).
3. The unit test code (placeholder language OR adapt to requested stack).
4. Notes on further test opportunities (if gaps remain).

If the user supplies:
- Only a description: derive test cases from inferred contract.
- Partial code: test only visible behavior; mark gaps.
- Full module: prefer black-box perspective; minimal white-box hints.

Example Skeleton (language-neutral pseudo-structure):

Test: functionName_givenSpecificCondition_returnsExpectedValue
Arrange:
  - Minimal setup
Act:
  - Call function with inputs
Assert:
  - Exact expected output
  - No side effects (if applicable)

Return ONLY the requested artifacts—no extra commentary beyond sections.

Now proceed using the above standards.

