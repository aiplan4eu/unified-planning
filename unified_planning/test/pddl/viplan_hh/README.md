The problems in this directory were taken from the [ViPlan-HH benchmark](https://github.com/merlerm/ViPlan/) (licensed under the MIT License). All PDDL files in that problem can be found [here](https://github.com/merlerm/ViPlan/tree/main/data/planning/igibson).

The KS0 compiler tests treat these instances as a catalog of ViPlan-HH cases
declared in `unified_planning/test/viplan_hh_cases.py`. The shared
`domain.pddl` stays in this directory, and each case entry points to a problem
file here while declaring its initial-state uncertainty in a compact,
problem-agnostic format.

State facts are written as atom tuples instead of parsed strings. For example,
`("inside", "bowl_1", "cabinet_1")` represents the fluent
`inside(bowl_1, cabinet_1)`.

Each `ViPlanHHCase` can declare:

- `representative_states`: a small set of initial states used by compile and
  end-to-end smoke tests.
- `base_state`: facts shared by every generated uncertain world.
- `uncertainty_dimensions`: mutually-exclusive choices whose Cartesian product
  defines the full possible-state set for the subset stress test.
- `true_state`: the benchmark's ground-truth initial state, which is always
  included in the stress-test subsets.

To add another ViPlan-HH problem under the same domain:

1. Add the new `*.pddl` problem file to this directory.
2. Add a matching `ViPlanHHCase` entry in
   `unified_planning/test/viplan_hh_cases.py`.
3. Define `representative_states` for the smoke tests.
4. If the new problem should participate in the subset stress test, also
   define `base_state`, `uncertainty_dimensions`, and `true_state`.

The KS0 ViPlan-HH tests iterate over every declared case automatically, so
adding a new case does not require additional bespoke test helpers.
