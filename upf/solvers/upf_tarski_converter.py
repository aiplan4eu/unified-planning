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


from typing import List, Tuple

import upf
import upf.model
import upf.walkers as walkers

import tarski # type: ignore

class TarskiFormulaConverter(walkers.DagWalker):
    def __init__(self, language: 'tarski.fol.FirstOrderLanguage') -> None:
        walkers.DagWalker.__init__(self) #NOTE: invalidate_memoization is False, but we might want it True
        self.lang = language

    def convert_formula(self, expression: 'upf.model.FNode') -> 'tarski.syntax.formulas.Formula':
        self.walk(expression)

    def walk_and(self, expression: 'upf.model.FNode', args: List['tarski.syntax.formulas.Formula']) -> 'tarski.syntax.formulas.Formula':
        return tarski.syntax.land(*args, flat=True)

    def walk_or(self, expression: 'upf.model.FNode', args: List['tarski.syntax.formulas.Formula']) -> 'tarski.syntax.formulas.Formula':
        return tarski.syntax.lor(*args, flat=True)

    def walk_not(self, expression: 'upf.model.FNode', args: List['tarski.syntax.formulas.Formula']) -> 'tarski.syntax.formulas.Formula':
        assert len(args) == 1
        return tarski.syntax.neg(args[0])

    def walk_iff(self, expression: 'upf.model.FNode', args: List['tarski.syntax.formulas.Formula']) -> 'tarski.syntax.formulas.Formula':
        assert len(args) == 2
        return tarski.syntax.equiv(args[0], args[1])

    def walk_implies(self, expression: 'upf.model.FNode', args: List['tarski.syntax.formulas.Formula']) -> 'tarski.syntax.formulas.Formula':
        assert len(args) == 2
        return tarski.syntax.implies(args[0], args[1])

    def walk_exists(self, expression: 'upf.model.FNode', args: List['tarski.syntax.formulas.Formula']) -> 'tarski.syntax.formulas.Formula':
        assert len(args) == 1
        variables = [self.lang.variable(v.name(), self.lang.sort(v.type().name())) for v in expression.variables()] # type: ignore
        return tarski.syntax.exists(*variables, args[0])

    def walk_forall(self, expression: 'upf.model.FNode', args: List['tarski.syntax.formulas.Formula']) -> 'tarski.syntax.formulas.Formula':
        assert len(args) == 1
        variables = [self.lang.variable(v.name(), self.lang.sort(v.type().name())) for v in expression.variables()] # type: ignore
        return tarski.syntax.forall(*variables, args[0])

    def walk_equals(self, expression: 'upf.model.FNode', args: List['tarski.syntax.formulas.Formula']) -> 'tarski.syntax.formulas.Formula':
        assert len(args) == 2
        return tarski.syntax.Atom(self.lang.get_predicate('='), args[0], args[1]) #NOTE: might also be CompoundTerm instead of Atom, but the first does not extend "Formula"

    def walk_le(self, expression: 'upf.model.FNode', args: List['tarski.syntax.formulas.Formula']) -> 'tarski.syntax.formulas.Formula':
        assert len(args) == 2
        return tarski.syntax.Atom(self.lang.get_predicate('<='), args[0], args[1])

    def walk_lt(self, expression: 'upf.model.FNode', args: List['tarski.syntax.formulas.Formula']) -> 'tarski.syntax.formulas.Formula':
        assert len(args) == 2
        return tarski.syntax.Atom(self.lang.get_predicate('<'), args[0], args[1])

    def walk_fluent_exp(self, expression: 'upf.model.FNode', args: List['tarski.syntax.formulas.Formula']) -> 'tarski.syntax.formulas.Formula':
        tarski_fluent_rep = self.lang.get(expression.fluent().name())
        return tarski_fluent_rep(*args)

    def walk_plus(self, expression: 'upf.model.FNode', args: List['tarski.syntax.formulas.Formula']) -> 'tarski.syntax.formulas.Formula':
        return tarski.syntax.Atom(self.lang.get_predicate('+'), *args) #TODO: to test if + (and *) is binary or n-ary for tarski

    def walk_minus(self, expression: 'upf.model.FNode', args: List['tarski.syntax.formulas.Formula']) -> 'tarski.syntax.formulas.Formula':
        assert len(args) == 2
        return tarski.syntax.Atom(self.lang.get_predicate('-'), args[0], args[1])

    def walk_times(self, expression: 'upf.model.FNode', args: List['tarski.syntax.formulas.Formula']) -> 'tarski.syntax.formulas.Formula':
        return tarski.syntax.Atom(self.lang.get_predicate('*'), *args)

    def walk_div(self, expression: 'upf.model.FNode', args: List['tarski.syntax.formulas.Formula']) -> 'tarski.syntax.formulas.Formula':
        assert len(args) == 2
        return tarski.syntax.Atom(self.lang.get_predicate('/'), args[0], args[1])

    def walk_bool_constant(self, expression: 'upf.model.FNode', args: List['tarski.syntax.formulas.Formula']) -> 'tarski.syntax.formulas.Formula':
        assert len(args) == 0
        if expression.bool_constant_value():
            return tarski.syntax.top
        return tarski.syntax.bot

    def walk_int_constant(self, expression: 'upf.model.FNode', args: List['tarski.syntax.formulas.Formula']) -> 'tarski.syntax.formulas.Formula':
        #NOTE: TODO
        pass

    def walk_real_constant(self, expression: 'upf.model.FNode', args: List['tarski.syntax.formulas.Formula']) -> 'tarski.syntax.formulas.Formula':
        #NOTE: TODO
        pass

    def walk_param_exp(self, expression: 'upf.model.FNode', args: List['tarski.syntax.formulas.Formula']) -> 'tarski.syntax.formulas.Formula':
        tarski_param_rep = self.lang.variable(expression.parameter().name(), self.lang.get_sort(expression.parameter().type().name())) # type: ignore
        return tarski_param_rep #NOTE :not sure

    def walk_variable_exp(self, expression: 'upf.model.FNode', args: List['tarski.syntax.formulas.Formula']) -> 'tarski.syntax.formulas.Formula':
        tarski_variable_rep = self.lang.variable(expression.variable().name(), self.lang.get_sort(expression.variable().type().name())) # type: ignore
        return tarski_variable_rep #NOTE :not sure

    def walk_object_exp(self, expression: 'upf.model.FNode', args: List['tarski.syntax.formulas.Formula']) -> 'tarski.syntax.formulas.Formula':
        tarski_object_rep = self.lang.get_constant(expression.object().name())
        return tarski_object_rep #NOTE :not sure

class TarskiConverter:
    def __init__(self) -> None:
        pass

    def upf_to_tarski(self, problem: 'upf.model.Problem') -> 'tarski.fstrips.problem.Problem':
        #creating tarski language
        lang = tarski.fol.FirstOrderLanguage(f'{problem.name}_lang', ['equality', 'arithmetic'])
        for ut in problem.user_types(): #adding user_types to the language
            lang.sort(ut.name()) # type: ignore
        for f in problem.fluents(): #adding fluents to the language
            signature = [lang.get_sort(t.name()) for t in f.signature()] # type: ignore
            if f.type().is_bool_type():
                lang.predicate(f.name(), *signature)
            else:
                #NOTE: Might not be bool_type or real_type
                lang.function(f.name(), *signature, lang.get_sort(f.type().name())) # type: ignore #NOTE: NOT SURE ABOUT THIS
        for o in problem.all_objects(): #adding objects to the language
            lang.constant(o.name(), lang.get_sort(o.type().name())) # type: ignore
        #creating tarski problem
        em = problem.env.expression_manager
        tfc = TarskiFormulaConverter(language=lang)
        new_problem = tarski.fstrips.problem.create_fstrips_problem(lang, problem.name, f'{problem.name}_domain')
        for action in problem.actions():
            if not isinstance(action, upf.model.InstantaneousAction):
                raise #TODO: Insert exception to raise
            parameters = [lang.variable(p.name(), lang.get_sort(p.type().name())) for p in action.parameters()] # type: ignore
            #add action to the problem
            new_problem.action(action.name,
                                parameters,
                                precondition=em.And(action.preconditions()),
                                effects=[_convert_effect(e, tfc, em) for e in action.effects()]
            )
        #TODO: init with new_problem.init.add(predicate, eventually some parameters)
        # new_problem.init.set(function, eventually some parameters)
        new_problem.goal = tfc.convert_formula(em.And(problem.goals()))

        return new_problem


def _convert_effect(effect: 'upf.model.Effect', tfc: TarskiFormulaConverter, em: 'upf.model.ExpressionManager') -> 'tarski.fstrips.SingleEffect':
    condition = tfc.convert_formula(effect.condition())
    predicate = tfc.convert_formula(effect.fluent())
    if effect.value().is_bool_constant():
        if effect.value().constant_value():
            return tarski.fstrips.AddEffect(predicate, condition)
        else:
            return tarski.fstrips.DelEffect(predicate, condition)
    else:
        if effect.kind() == upf.model.effect.ASSIGN:
            value = tfc.convert_formula(effect.value())
        elif effect.kind() == upf.model.effect.INCREASE:
            value = tfc.convert_formula(em.Plus(effect.fluent(), effect.value()))
        else:
            value = tfc.convert_formula(em.Minus(effect.fluent(), effect.value()))
        return tarski.fstrips.FunctionalEffect(predicate, value, condition)
