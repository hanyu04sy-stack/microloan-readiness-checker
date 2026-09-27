# Step 7 - Class 5 Economics Analysis

Status: complete for the final 50-case experiment and the evidence available. Project-specific production volume, labour inputs, and fixed monthly cost remain unknown and are therefore retained as variables.

## Final RAG update

The selected RAG candidate completed 50 successful structured calls with 47,693 prompt tokens and 83,006 total tokens. Estimated output-plus-thinking tokens were 35,313. Applying the same dated prices gives an attributable direct model cost of USD 0.1681935, or USD 0.003364 per incoming application. Its manual-review rate was 10%.

Using the same course-sourced scenarios, variable plus expected fallback cost becomes approximately USD 0.0534 per incoming application for a USD 0.50 light review and USD 0.6034 for a USD 6.00 heavier escalation, before `F / V`. These are scenario calculations, not measured bank costs. The earlier sections retain the non-RAG run as historical comparison; they must not be mistaken for the final RAG cost profile.

## 1. Method required by the course

The analysis follows the three-layer cost-to-serve method in PE6201 Class 5 C2:

1. Per-task variable cost: fresh input tokens, output and thinking tokens, retrieval, and tool fees.
2. Per-task expected fallback cost: `(1 - automated success rate) x cost of handling one fallback`.
3. Fixed monthly cost: infrastructure, evaluation, monitoring, and maintenance, divided by monthly volume.

The resulting decision unit is:

```text
cost per successful task
  = per-task variable cost
  + expected fallback cost
  + fixed monthly cost / monthly application volume
```

This is intentionally different from quoting only a price per million tokens. The course also requires a break-even calculation and a sensitivity table because the success rate is the most uncertain input.

Course sources: PE6201 Class 5 C2, pages 4, 16, and 21-23; PE6201 Class 3 C3, pages 3-5. The course examples are methodological references and are not treated as facts about this microloan project.

## 2. Dated model-price configuration

Model: `gemini-3.8-flash`

Pricing source checked on 27 September 2026: Google Gemini Developer API pricing, <https://ai.google.dev/gemini-api/docs/pricing>.

Prices applicable through 31 December 2026:

| Meter | Price per 1 million tokens (USD) |
|---|---:|
| Input | 0.75 |
| Output, including thinking tokens | 3.75 |

These prices are configuration data, not permanent constants. Google states that different prices apply from 1 January 2027.

## 3. Final observed usage

Only calls with returned usage metadata are included below. Failed 503 calls and quota-limited 429 attempts returned no token metadata, so no token cost is invented for them.

| Measure | Observed value |
|---|---:|
| Finalized applications | 50 |
| Successful model calls with usage metadata | 44 |
| Semantic failures routed to manual review | 6 |
| Prompt/input tokens | 16,942 |
| Visible output tokens | 3,322 |
| Total tokens reported by the provider | 41,894 |
| Estimated billed non-input tokens (`total - prompt`) | 24,952 |
| Observed manual-review outcomes | 11 of 50 (22%) |

The difference between total and prompt tokens is used as the estimate of billed output plus thinking tokens. The six API-failure fallbacks and five intentionally ambiguous cases account for the 11 manual-review outcomes.

## 4. Direct model cost attributable from observed usage

```text
input cost
  = 16,942 / 1,000,000 x USD 0.75
  = USD 0.0127065

output-and-thinking cost
  = 24,952 / 1,000,000 x USD 3.75
  = USD 0.09357

direct model cost attributable from returned usage metadata
  = USD 0.1062765

average direct model cost per incoming application
  = USD 0.1062765 / 50
  = USD 0.00212553

average direct model cost per successful API response
  = USD 0.1062765 / 44
  = USD 0.002415375

direct model cost per automatically completed case
  = USD 0.1062765 / 39
  = USD 0.00272504
```

These amounts apply the dated paid-tier token prices to returned usage metadata. Failed attempts returned no usage metadata, so the estimate does not assign them an invented token charge. The user's account charge may therefore differ because of unobserved failed-attempt usage and the timing of the switch from free to paid service. This calculation is the consistent economic comparison used by the report, not a reconstruction of the billing statement.

## 5. Rules baseline versus hybrid

The rule-only baseline has effectively zero model-inference cost. Its completed evaluation achieved precision 1.00 but recall 0.333, missing 20 flag-worthy cases. Therefore, low inference cost alone is not a sufficient business result.

The hybrid system achieved precision 0.857, recall 1.000, and F1 0.923. It eliminated the baseline's 20 false negatives while adding five false positives. Its manual-review rate was 22%, including five correctly escalated ambiguous cases and six API-failure fallbacks.

The baseline's missed semantic problems are silent failures rather than observed human fallbacks. No downstream monetary loss is assigned to them because the project has no evidence for such a value. They remain visible in the quality metrics and Class 6 risk analysis.

## 6. Course-sourced fallback scenarios

The project has no confirmed operational volume, reviewer wage, review duration, or fixed monthly cost. Rather than inventing bank data, the analysis uses two explicitly illustrative fallback-cost scenarios taken from PE6201 Class 5 C2:

| Scenario | Course example | Fallback cost used |
|---|---|---:|
| Light review | 45 seconds of a clerk at USD 40 per hour | USD 0.50 |
| Heavier escalation | 8 minutes at a loaded USD 45 per hour | USD 6.00 |

These are sensitivity bounds from the course, not claims about a real microloan operation.

Using the attributable direct model cost estimate of USD 0.002126 per incoming application:

```text
variable plus fallback cost per application
  = USD 0.002126 + manual-review rate x fallback cost
```

| Manual-review rate | Light review: USD 0.50 | Heavier escalation: USD 6.00 |
|---:|---:|---:|
| 12% | 0.062126 | 0.722126 |
| **22% observed** | **0.112126** | **1.322126** |
| 32% | 0.162126 | 1.922126 |

The sensitivity range is the observed review rate plus or minus 10 percentage points, following the course method. It demonstrates that human fallback dominates direct model cost in both course-sourced scenarios.

## 7. Break-even interpretation

At the attributable model-cost estimate, the hybrid system pays for that measured inference cost if it avoids at least:

```text
light-review scenario:
  0.002126 / 0.50 = 0.004252, or about 0.425 percentage points

heavier-escalation scenario:
  0.002126 / 6.00 = 0.000354, or about 0.035 percentage points
```

Equivalently, avoiding one USD 0.50 review offsets about 235 model-processed applications, while avoiding one USD 6.00 escalation offsets about 2,823 applications at the observed token profile. This does not establish that the hybrid system avoids a real institution's reviews because no real workflow baseline was supplied.

## 8. Inputs that remain unquantified

The following values have not been supplied by the student, instructor, or project data and remain explicitly unquantified:

| Input | Symbol | Status |
|---|---|---|
| Expected applications per month | `V` | Not confirmed |
| Average minutes for one manual review | `M` | Not confirmed |
| Fully loaded reviewer cost per hour in USD | `W` | Not confirmed |
| Fixed monthly infrastructure and maintenance cost in USD | `F` | Not confirmed |

If project-specific values later become available:

```text
human fallback cost = M / 60 x W

hybrid cost per successful task
  = observed model cost per application
  + manual-review rate x human fallback cost
  + F / V
```

Because `F` and `V` are unknown, this analysis reports variable plus fallback cost and retains `F / V` symbolically. It does not claim a complete production lifecycle cost.

## 9. Current defensible conclusion

Under both course-sourced scenarios, the direct model charge is much smaller than expected human fallback cost. At the observed 22% manual-review rate, variable plus fallback cost is approximately USD 0.112 per incoming application in the light-review scenario and USD 1.322 in the heavier-escalation scenario, before `F / V`. The economic decision therefore depends primarily on human fallback and operational assumptions, not token price. This is a scenario conclusion, not a claim about the actual staffing cost of a real lender.

The detailed calculations in Sections 3-9 describe the earlier non-RAG hybrid
run and are retained as historical comparison. The final RAG candidate has now
completed its separate frozen run; its current economics are summarized in the
Final RAG update at the beginning of this document and in
`RAG_EVALUATION_REPORT.md`.
