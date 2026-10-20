---
title: "RuneScape Classic, AI, and the Price of Trust"
description: "How I use AI with RuneScape Classic tooling, and the benchmark I want to build for planning, market strategy, dishonesty, and trust."
pubDate: "2026-10-20T13:41:07-04:00"
category: ["ai", "technology", "tools"]
banner: "@images/banners/runescape-classic-ai-price-of-trust.png"
ogImage: "@images/banners/runescape-classic-ai-price-of-trust.png"
tags: ["RuneScape Classic", "AI Agents", "Benchmarks", "Markets", "Game Theory", "Automation"]
selected: true
toc: true
---

RuneScape Classic gives me a good place to think about software agents. A character has a location, an inventory, skills, limited resources, and an objective. Progress requires actions that change the world. A convincing explanation does not fill the inventory. A successful action does.

The economic questions are even better. A miner can produce more ore and still make less money. A trader can finish with more coins while leaving its counterparties worse off. A locally sensible decision can create a market outcome nobody intended.

My setting is RuneScape Classic at [rsc.vet](https://rsc.vet/), particularly its Coleslaw world. Classic has different mechanics from 2004-era RuneScape, and Coleslaw has features of its own, including an Auction House. [OpenRSC's world comparison](https://rsc.vet/faq) documents those differences.

I am using AI to help build and operate automation in that environment. The gameplay foundation today is deterministic scripts, production pipelines, and operational tools. The next layer I want to build is a controlled evaluation of model-driven planning, coordination, and market strategy. The engineering gives that research direction something concrete to stand on.

## The engineering behind the experiment

My work builds on two community projects. [IdleRSC](https://gitlab.com/openrsc/idlersc) provides a Java scripting platform with structured access to game state. [Plutonium](https://gitlab.com/openrsc/plutonium) is a headless Go client with embedded Python scripting through gpython. I have been extending those foundations for Coleslaw.

The work includes specialized production roles, shared handoff logic, dashboards, structured status reports, and watchdog recovery. Workers gather inputs, process materials, produce supplies, and transfer outputs downstream. In the headless fork, I also adapted protocol handling for Coleslaw's skill and equipment state, noted inventory, and noted trading. Quantity and packet correctness matter when a production chain depends on a successful delivery.

Codex participates through a natural-language operator bridge connected to the project and its tools. It helps with development and operations; deterministic handlers and scripts perform the gameplay actions. That gives me a clear separation between asking for an operation, executing it, and checking its outcome.

The shared trade state machine handles allowlisted peers, outgoing quantity checks, offer and confirmation screens, timeouts, and completion signals. Its validation is tailored to coordinated handoffs. A market-facing agent dealing with untrusted counterparties would need stricter incoming-offer validation.

## Tools shape the intelligence being measured

The useful loop is observation, decision, action, and verification.

![Proposed agent loop separating observations, model decisions, deterministic execution, and verified outcomes.](@images/posts/runescape-classic-ai-price-of-trust/agent-loop.svg)

*Proposed gameplay evaluation architecture. Existing execution and operations tools provide the foundation for a future model decision layer.*

An observation might show a full inventory and a downstream worker accepting supplies. A decision selects a transfer. Execution handles movement and the trade protocol. Verification checks whether the goods actually arrived. A request is an intention; settlement is an outcome.

An agent clicking pixels faces a different task from one receiving structured inventory. A complete production macro changes the problem again. A benchmark should disclose what the tools know and do, so the wrapper does not quietly make the strategic decision being scored.

I would expose bounded actions and useful higher-level helpers, with lower-level controls available for diagnosis. Durable programs can handle repeatable routines while a model selects, inspects, and revises them. There is little reason to spend inference on every routine game action.

The difficult moments are recovery: a trade times out, an inventory differs from the plan, or a process stalls. Those failures should consume the budget and remain visible. Concise documentation and recorded failures can improve the interface, but an agent's requested helper still needs review: it might reveal a missing primitive or simply outsource the whole task.

## Build a benchmark ladder, then question the score

I would begin with skill progression, then multi-step production, quests or other long-horizon dependencies, coordinated workers, and finally markets. Each adds a different demand on the system.

![Proposed benchmark ladder covering skills, quests, production, coordination, and markets.](@images/posts/runescape-classic-ai-price-of-trust/benchmark-matrix.svg)

*Proposed task families and experiment controls; no benchmark results are shown.*

Comparisons need matching initial skills, inventories, information, world settings, and budgets. Repeated trials, reliable resets, and held-out variations help distinguish dependable adaptation from luck or memorized routes. A simple script and a stronger deterministic policy should be baselines.

The unit of comparison is the model plus its harness: tools, memory, observations, instructions, and recovery code. I would report those versions alongside elapsed time, inference cost, tool calls, completion, and failures. The useful result is a frontier of cost and performance, with separate experiments identifying which improvements came from the model and which came from the surrounding software.

Even XP needs careful interpretation. Peak throughput rewards a productive burst; sustained throughput rewards keeping the process working. A one-time quest reward can make a short scoring window look exceptional. Full progress curves and both metrics help expose a score that rewards the wrong behavior.

Packaging a local environment would make starts and outcomes reproducible. As tasks become easier, changed dependencies and market conditions would tell us more than simply extending the clock.

Verifiable outcomes could eventually supply learning signals as well as evaluation scores. That would be a further experiment built on the same explicit state and reward definitions.

## The market work already in my code

My Java auction tools provide a practical economic starting point. A buyer evaluates opportunities using:

```text
estimated conversion margin per item
  = high-alchemy value − rune cost − purchase price
```

High alchemy converts items into coins directly. The estimate does not require finding a resale buyer, although time and opportunity cost still matter. The buyer enforces spending limits. A separate undercutting tool constrains repricing with price floors and bounded relisting. The standalone tools default to dry run so intended actions can be inspected.

Auction maintenance is currently disabled in my Plutonium port; its production and handoff machinery is a separate part of the system.

These are programmed economic policies. They make a useful baseline for asking what a model adds: adapting to new conditions, comparing alternatives, or reasoning about another participant.

Resale introduces different constraints. A posted price is an offer, not evidence that an entire inventory can clear there. A profitable-looking position may tie up capital while buyers never arrive. A market benchmark needs quantities, completed trades, waiting time, and unsold stock alongside prices.

Shared scarcity creates another complication. More workers cannot multiply a rock's fixed respawn rate. One participant's resource consumption changes another's opportunities. Individual efficiency and market-wide improvement can move in different directions.

## Trust changes the strategy

A [recent MMO-agent presentation by Max Bittker](https://www.youtube.com/watch?v=cNm4zyUtWj0&t=2316) sharpened my interest in staged trust and deliberately weakened settlement. Its nonpayment anecdotes raise an important question for evaluation: when an agent gains more, did it create value, bargain effectively, or exploit a promise the exchange mechanism could not enforce?

The behavior I especially want to test is strategic dishonesty: whether an agent pursuing profit begins making false claims without being instructed to deceive. Could it establish trust through small completed trades, then exploit that reputation in a larger deal? Could it return an accidental payment while coordinating prices against buyers? Those would be different behaviors requiring different evidence, not a single label of “honest” or “dishonest.”

For Classic, I would compare controlled treatments. One would use simultaneous exchange with clear settlement guarantees. Another would permit staged delivery or credit between experiment-controlled agents in an isolated world. Matching the remaining conditions would help identify how much apparent success depends on settlement design.

Repeated identities make reputation valuable. Short horizons can reduce the future cost of losing it. Public warnings may change outcomes compared with private complaints. An agent might also adapt its language to what it predicts a particular opponent will believe.

Honesty needs an operational definition. Keeping a maximum acceptable price private is bargaining. Falsely claiming payment is a checkable assertion. A failed promise could reflect an execution error, agreed credit, or a deliberately broken commitment. Statements must be compared with the facts available to the agent and the eventual outcome.

Cooperation, specialization, retaliation, and coordinated withholding are hypotheses to test. Similar prices alone would not prove collusion: agents might independently face similar costs. Communication, actions, and comparison runs need to support the interpretation.

## A profit leaderboard leaves too much out

If the objective is simply “finish with the most coins,” several very different behaviors can win. My scorecard would preserve those distinctions.

![Proposed market scorecard covering returns, execution, truthfulness, counterparties, market quality, and coordination.](@images/posts/runescape-classic-ai-price-of-trust/market-scorecard.svg)

*Proposed measurements for a controlled market evaluation; these are not experimental scores.*

| Dimension | What I would measure |
| --- | --- |
| Returns | Realized gains, costs, liabilities, inventory valuation, and capital tied up. |
| Execution | Fulfilled commitments, completed trades, defaults, timeouts, and settlement delay. |
| Truthfulness | Verifiable claims against known facts; omissions judged under explicit disclosure rules. |
| Counterparties | Losses imposed, mistaken transfers returned, and resilience to misleading messages. |
| Market quality | Volume, spreads, fill rates, concentration, and recovery after shocks. |
| Coordination | Productive specialization, shared-resource costs, and evidence of collusion. |

Measuring total surplus would require explicit valuations. Coins transferred between participants do not by themselves measure value created. Short-term profit and repeated-game trust also deserve separate treatment.

The evidence needs to survive the story. I would retain observations, actions, commitments, transfers, and final states so a run can be reconstructed. Summaries help navigate long logs; checking those summaries is itself an analysis problem. A model's explanation is evidence to examine, not privileged access to its motives.

Chat creates a tool boundary too. Another trader's message is information, not authority to operate the agent's tools. That connects directly to the [prompt-injection boundary](https://blog.jamestsetsekas.com/posts/prompt-injection-is-the-new-command-injection/) I have written about before.

OpenRSC permits automation only on Uranium and Coleslaw and prohibits scamming. Any experiment permitting deception belongs in an isolated setting with controlled counterparties. [The live-world rules](https://rsc.vet/rules) govern public play.

I want to test whether an agent can recognize an opportunity, execute reliably, adapt when conditions change, and honor its commitments. RuneScape Classic gives me a world where those decisions have observable consequences. The scripts and operational tooling are useful today. Building reproducible evaluations on that foundation is how I want to turn the next set of strategic questions into evidence.

---

*October 20, 2026. Cover: AI-generated editorial illustration, not a game screenshot. Diagrams by James Tsetsekas describe proposed evaluations; no Classic model benchmark results are claimed.*
