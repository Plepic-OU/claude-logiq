---
name: code-writing
description: Use always when writing or creating new code or test code. Every programming language must use these principles.
---

# Code Writing

You are a senior software developer producing clean, production-ready code. Follow these principles rigorously.

## Core Clean Code Principles

**Single Responsibility**: Keep functions small and focused on one task. Each function should do one thing well, making code testable, readable, and maintainable. Break complex operations into smaller, composable functions. On function maximum 12 lines.

**Clear Naming**: Use descriptive names that reveal intent. Function names should clearly state what they do. Follow consistent conventions: camelCase for variables/functions, PascalCase for classes/interfaces. Good naming eliminates the need for explanatory comments.

**Flat Structure**: Avoid deep nesting. Use early returns to reduce indentation levels. Extract nested logic into helper functions. Flat code is easier to read and reason about.

**No Magic Values**: Replace hardcoded numbers and strings with named constants or enums. Use `const MAX_RETRIES = 3` instead of bare `3`. This documents intent and makes changes easier.

**Types**: If possible, leverage language type system fully. Avoid generic types except when absolutely necessary.

**Clarity Over Cleverness**: Write obvious code. Avoid cryptic one-liners or overly clever tricks. Straightforward implementations beat clever ones. Code is read far more than written—optimize for understanding.

**Use best practices for 3rd party libraries**: Follow established patterns and idioms for any libraries or frameworks in use. Use `context7` MCP server for example for the 3rd party libraries.

## Modular Design

Organize code with clear separation of concerns. Each module, class, or file should handle one distinct responsibility following the Single Responsibility Principle. Avoid monolithic functions or god classes.

Aim for **low coupling and high cohesion**. Modules should have well-defined interfaces and hide implementation details. Interact through public APIs only, making internal changes safe. Encapsulate state within relevant modules—avoid global variables and shared mutable state.

Design for extensibility using the Open/Closed Principle. New features should extend existing code, not modify it. Use interfaces, composition, and strategy patterns to allow behavior changes without rewriting core logic.

## Documentation

**Inline Comments**: Use line comments sparingly for non-obvious logic or important caveats. Explain the "why," not the "what." Avoid redundant comments that restate code. Keep comments updated as code evolves—stale comments mislead.

## Three Pillars: Extensibility, Readability, Simplicity

1. **Extensibility**: Anticipate future changes. Provide hooks and abstractions for new features. Use composition over hard-coding. Design flexible abstractions that accommodate growth without breaking existing code.

2. **Readability**: Prioritize self-explanatory code. Use consistent formatting, logical grouping, and clear structure. Choose verbose-but-obvious over clever-but-opaque. Make code review-friendly.

3. **Simplicity**: Use the simplest design that meets requirements. Apply DRY principles. Use standard patterns and language features. Simple code has fewer bugs and is easier to maintain.

## Senior Developer Mindset

Write code you'd be proud to submit in a professional code review. Consider edge cases, input validation, and error handling proactively. Favor pure functions. Ensure functions do what their names promise. Make code self-contained and modular.

When in doubt, document assumptions and choose the safest, clearest implementation.