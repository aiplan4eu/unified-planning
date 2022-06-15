# Copyright 2021 AIPlan4EU project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


import networkx as nx # type: ignore
import unified_planning as up
import unified_planning.plans as plans
from unified_planning.environment import Environment
from unified_planning.exceptions import UPUsageError
from unified_planning.model import FNode, InstantaneousAction, Expression
from unified_planning.walkers import Substituter, Simplifier, FreeVarsExtractor, ExpressionQuantifiersRemover
from typing import Callable, Dict, Optional, Set, List, cast


class SequentialPlan(plans.plan.Plan):
    '''Represents a sequential plan.'''
    def __init__(self, actions: List['plans.plan.ActionInstance'], environment: Optional['Environment'] = None):
        # if we have a specific env or we don't have any actions
        if environment is not None or not actions:
            plans.plan.Plan.__init__(self, plans.plan.PlanKind.SEQUENTIAL_PLAN, environment)
        # If we don't have a specific env and have at least 1 action, use the env of the first action
        else:
            assert len(actions) > 0
            plans.plan.Plan.__init__(self, plans.plan.PlanKind.SEQUENTIAL_PLAN, actions[0].action.env)
        for ai in actions: # check that given env and the env in the actions is the same
            if ai.action.env != self._environment:
                raise UPUsageError('The environment given to the plan is not the same of the actions in the plan.')
        self._actions = actions

    def __repr__(self) -> str:
        return str(self._actions)

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, SequentialPlan) and len(self._actions) == len(oth._actions):
            for ai, oth_ai in zip(self._actions, oth._actions):
                if not ai.is_semantically_equivalent(oth_ai):
                    return False
            return True
        else:
            return False

    def __hash__(self) -> int:
        count: int = 0
        for i, ai in enumerate(self._actions):
            count += i + hash(ai.action) + hash(ai.actual_parameters)
        return count

    def __contains__(self, item: object) -> bool:
        if isinstance(item, plans.plan.ActionInstance):
            return any(item.is_semantically_equivalent(a) for a in self._actions)
        else:
            return False

    @property
    def actions(self) -> List['plans.plan.ActionInstance']:
        '''Returns the sequence of action instances.'''
        return self._actions

    def replace_action_instances(self, replace_function: Callable[['plans.plan.ActionInstance'], 'plans.plan.ActionInstance']) -> 'up.plans.plan.Plan':
        new_ai = [replace_function(ai) for ai in self._actions]
        new_env = self._environment
        if len(new_ai) > 0:
            new_env = new_ai[0].action.env
        return SequentialPlan(new_ai, new_env)

    def to_partial_order_plan(self, problem: 'up.model.objects_set.ObjectsSetMixin') -> 'up.plans.partial_order_plan.PartialOrderPlan':
        '''Returns the PartialOrderPlan version of this SequentialPlan.

        This is done by keeping the ordering constraints, given by the SequentialPlan, between 2 ActionInstances
        that satisfy one of these conditions:
        + at least one of the 2 ActionInstances writes on a grounded fluent (writes means that one of his effects
                assign a value to said fluent)
            - AND the other ActionInstance reads or writes on the same grounded fluent (reads means that one of his preconditions
                or one of his condition in a conditional effect depends on said fluent).'''
        subs = Substituter(self._environment)
        simp = Simplifier(self._environment)
        eqr = ExpressionQuantifiersRemover(self._environment)
        fve = FreeVarsExtractor()
        # last_modifier is the mapping from a grounded fluent to the last action instance that assigned a value to
        # that fluent
        last_modifier: Dict[FNode, 'plans.plan.ActionInstance'] = {}
        # all_required is the mapping from a grounded fluent to all the action instances that read the value of that
        # fluent in their preconditions (or in the condition of their conditional effects)
        all_required: Dict[FNode, List['plans.plan.ActionInstance']] = {}
        # graph stores the information gathered through the process
        graph = nx.DiGraph()
        for action_instance in self.actions:
            graph.add_node(action_instance)
            assert isinstance(action_instance.action, InstantaneousAction)
            inst_action = cast(InstantaneousAction, action_instance.action)

            # required_fluents contains all the grounded fluents that this action_instance "reads"
            required_fluents: Set[FNode] = set()
            # same of required_fluents, but the fluents are lifted
            lifted_required_fluents: Set[FNode] = set()
            # add free vars of preconditions
            for prec in inst_action.preconditions:
                lifted_required_fluents |= fve.get(eqr.remove_quantifiers(prec, problem))
            # add in the required_fluents all the free fluents this action instance deals with
            for eff in inst_action.effects:
                lifted_required_fluents |= fve.get(eqr.remove_quantifiers(eff.condition, problem))
                lifted_required_fluents |= fve.get(eqr.remove_quantifiers(eff.fluent, problem))
                lifted_required_fluents |= fve.get(eqr.remove_quantifiers(eff.value, problem))

            assignments: Dict[Expression, Expression] = dict(zip(inst_action.parameters, action_instance.actual_parameters))
            for lifted_fluent in lifted_required_fluents:
                assert lifted_fluent.is_fluent_exp()
                for arg in lifted_fluent.args: # check that we don't have "nested" fluents
                    if len(fve.get(eqr.remove_quantifiers(arg, problem))) != 0:
                        raise UPUsageError(f'The partial deordering of a Sequential Plan does not allow the use of fluents inside the parameter of fluents!\nThe fluent: {lifted_fluent} does violates this contraint.')
                required_fluents.add(simp.simplify(subs.substitute(lifted_fluent, assignments)))

            # for every required fluent, add this action instance to the list of action instances that requires this fluent
            # and order the current action instance after the last modifier of the fluent
            for required_fluent in required_fluents:
                action_instance_list = all_required.setdefault(required_fluent, [])
                action_instance_list.append(action_instance)
                required_fluent_last_modifier = last_modifier.get(required_fluent, None)
                if required_fluent_last_modifier is not None:
                    assert required_fluent_last_modifier != action_instance # sanity check
                    graph.add_edge(required_fluent_last_modifier, action_instance)

            # for every effect, set current action instance as the last modifier and the current action instance is ordered
            # after every action instance that requires a fluent the current action instance modifies
            for eff in inst_action.effects:
                assert eff.fluent.is_fluent_exp()
                grounded_fluent = simp.simplify(subs.substitute(eff.fluent, assignments))
                last_modifier[grounded_fluent] = action_instance
                dependent_action_instance_list = all_required.setdefault(grounded_fluent, [])
                for dependent_action_instance in dependent_action_instance_list:
                    if dependent_action_instance != action_instance:
                        graph.add_edge(dependent_action_instance, action_instance)

        assert nx.is_directed_acyclic_graph(graph)
        # remove redundant edges and return the up.plans.partial_order_plan.PartialOrderPlan structure.
        return up.plans.partial_order_plan.PartialOrderPlan({}, self._environment, nx.transitive_reduction(graph))
