The problems in this directory were taken from the [ViPlan-HH benchmark](https://github.com/merlerm/ViPlan/), distributed under the [MIT License](https://github.com/merlerm/ViPlan/blob/main/LICENSE). All PDDL files in that benchmark can be found [here](https://github.com/merlerm/ViPlan/tree/main/data/planning/igibson).

The KS0 compiler tests treat these instances as a catalog of ViPlan-HH cases
declared in `unified_planning/test/pddl/viplan_hh/viplan_hh_cases.py`. The shared
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
- `single_state_plan` / `conformant_plan`: known-good plans for the KS0
  compilation of the case (sequences of grounded compiled-action names),
  for the compilation with the first representative state and with all
  representative states respectively.

The known-good plans keep the tests planner-independent: instead of solving
the (large) compiled problems with whatever planner is installed — which can
be extremely slow — the tests replay the stored plans with the sequential
simulator on both the compiled and the original problem. The plans were
generated once by solving each compilation with a classical planner
(fast-downward). If the KS0 translation or its naming scheme changes, the
fixtures must be regenerated the same way: compile the case's problem with
`Ks0Compiler`, solve the compiled problem with any classical planner
supporting conditional effects, and store the resulting grounded action
names.

To add another ViPlan-HH problem under the same domain:

1. Add the new `*.pddl` problem file to this directory.
2. Add a matching `ViPlanHHCase` entry in
   `unified_planning/test/pddl/viplan_hh/viplan_hh_cases.py`.
3. Define `representative_states` for the smoke tests.
4. Generate `single_state_plan` and `conformant_plan` as described above.
5. If the new problem should participate in the subset stress test, also
   define `base_state`, `uncertainty_dimensions`, and `true_state`.

The KS0 ViPlan-HH tests iterate over every declared case automatically, so
adding a new case does not require additional bespoke test helpers.
