# ADR-0011: Project is named `cyberkinetic`

**Status:** Accepted
**Deciders:** August

## Context
The project needed a name before the repository was created. Two forces:

1. The harness is scoped to **cyber-physical systems** — products whose compromise has
   real-world, physical consequence. The design's novel contribution is the model of
   that consequence (see ADR-0001, ADR-0006), not the pipeline mechanics.
2. The architecture is inspired by `obra/superpowers` (composable skills, cascading
   intermediary artifacts, hard gates). An early candidate name, `cyber-physical-powers`,
   made that lineage explicit.

## Decision
Name the project **`cyberkinetic`**. Credit the `superpowers` lineage in the design
document's Inspirations section, **not** in the project name.

## Options Considered

### `cyber-physical-powers` (and variants: `cpspowers`, `physicalpowers`)
| Dimension | Assessment |
|---|---|
| Scope clarity | High |
| Distinctiveness | Low — borrows equity |
| Ergonomics | Poor — hyphenated triple, bad URL, bad aloud |

**Cons:** Permanently frames the project as derivative of its inspiration, inviting
comparison to a project in a different domain, and undersells the novel contribution
(the consequence model). Rejected.

### `kinetic`
Understated; "kinetic" is already the term of art for *has physical effect*. But
ambiguous outside context (physics? animation? a JS library?).

### `assay`, `transducer`, `cyphy`, `corpus`
Considered. `transducer` (a device converting energy across domains — literally the
cyber↔physical boundary) was the strongest alternative. `cyphy` is the researchers'
contraction but carries a SyFy homophone.

### `cyberkinetic` (chosen)
| Dimension | Assessment |
|---|---|
| Scope clarity | High — scopes to security + physical effect with zero explanation |
| Distinctiveness | Good — stands alone, borrows nothing |
| Ergonomics | Good — one word, typeable, pronounceable |

**Pros:** Names the boundary the harness actually models. Self-scoping in a repo listing.
**Cons:** The `cyber-` prefix carries mild marketing-tell risk with practitioners.
Accepted as a worthwhile trade for unambiguity.

## Consequences
- Repo: `cyberkinetic` (personal GitHub). Optional CLI alias: `ck`.
- Skills keep plain verb-noun names (`extract-claims`, `challenge-claim`); they are not
  themed to the project name. Legibility over cleverness.
- The assessment database stays `assessment.db` (one per assessment), not branded.
- **Prior-use note:** at least one prior company has operated under a similar name.
  Trademark risk was considered and accepted by the author; this is a naming record,
  not a legal clearance. Revisit if the project is adopted commercially or by an
  organization, where the risk profile differs.
- If a rename is ever proposed, this ADR is the record of what was already weighed.
