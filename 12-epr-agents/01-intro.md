# Introduction to Agents

In practical terms, an agent is a program that uses a language model to make
decisions, calls tools to act on those decisions, observes the results, and
loops until the task is complete or something goes wrong. The canned description
is "autonomous AI that executes multi-step tasks." The real description is a
program with a while loop, a model in the middle, and access to things that can
cause harm if misused.

---

## The Execution Loop

State machine: `idle -> thinking -> executing -> completed / failed`

Loop cycle:

- Package conversation history, system prompt, and tools
- Send to model
- Text response: completed state
- Tool call: intercept, validate, execute, append observation, repeat

---

## Tool Calls

Agents typically call tools to perform specific actions. These tools can be
anything from APIs, databases, or even other programs. The agent uses the
language model to decide which tool to call and what parameters to pass to it.
This allows the agent to interact with the world and perform complex tasks that
go beyond just generating text.

In a local harness, the model emits a tool use request, your code dispatches to
a local function, and the result comes back as a tool result. The tool is code
you wrote, running in the same process or at most a subprocess you control. You
can read it, audit it, and change it.

---

## Conclusion

Agents are a powerful way to use language models, but they also come with risks.
The model is making decisions and taking actions on its own, which can lead to
unintended consequences if not properly designed and monitored. It's important
to understand the capabilities and limitations of agents, as well as the ethical
considerations involved in their use.

---
