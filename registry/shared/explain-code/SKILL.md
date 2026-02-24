---
name: explain-code
description: >
  Explains code with visual ASCII diagrams and plain-language analogies.
  Use when explaining how code works, teaching about a codebase architecture,
  or when someone asks "how does this work?" or "walk me through this."
---

# Explain Code

When explaining any piece of code, always follow this structure:

1. **Start with an analogy** — compare what the code does to something from
   everyday life before touching the implementation details

2. **Draw a diagram** — use ASCII art to show the data flow, call graph,
   class hierarchy, or state transitions (whichever is most illuminating)

3. **Walk through the code** — explain step by step what happens at runtime,
   referencing specific line numbers or function names

4. **Highlight a gotcha** — identify one common mistake, edge case, or
   non-obvious behaviour that a new reader is likely to misunderstand

Keep explanations conversational. For complex concepts use multiple analogies
before committing to one. Prefer concrete examples over abstract descriptions.

## Example diagram style

```
  User request
       │
       ▼
  ┌─────────┐     cache hit    ┌───────────┐
  │  Router │ ───────────────► │   Cache   │
  └─────────┘                  └───────────┘
       │ cache miss
       ▼
  ┌─────────┐
  │   DB    │
  └─────────┘
```
