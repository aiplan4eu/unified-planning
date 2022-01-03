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


from typing import Dict, List, Tuple

import upf
import upf.model
import upf.walkers as walkers

import tarski # type: ignore

class TarskiFormulaConverter(walkers.DagWalker):
    def __init__(self, language: 'tarski.fol.FirstOrderLanguage') -> None:
        walkers.DagWalker.__init__(self) #NOTE: invalidate_memoization is False, but we might want it True
        self.lang = language

    def convert_formula(self, expression: 'upf.model.FNode') -> 'tarski.syntax.formulas.Formula':
        return self.walk(expression)

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
        variables = [self.lang.variable(v.name(), self.lang.get_sort(v.type().name())) for v in expression.variables()] # type: ignore
        return tarski.syntax.exists(*variables, args[0])

    def walk_forall(self, expression: 'upf.model.FNode', args: List['tarski.syntax.formulas.Formula']) -> 'tarski.syntax.formulas.Formula':
        assert len(args) == 1
        variables = [self.lang.variable(v.name(), self.lang.get_sort(v.type().name())) for v in expression.variables()] # type: ignore
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
        return tarski.syntax.Atom(self.lang.get_predicate('+'), *args)#TODO : write this correcly #TODO: to test if + (and *) is binary or n-ary for tarski

    def walk_minus(self, expression: 'upf.model.FNode', args: List['tarski.syntax.formulas.Formula']) -> 'tarski.syntax.formulas.Formula':
        assert len(args) == 2
        return args[0] - args[1]

    def walk_times(self, expression: 'upf.model.FNode', args: List['tarski.syntax.formulas.Formula']) -> 'tarski.syntax.formulas.Formula':
        return tarski.syntax.Atom(self.lang.get_predicate('*'), *args) #TODO : write this correcly

    def walk_div(self, expression: 'upf.model.FNode', args: List['tarski.syntax.formulas.Formula']) -> 'tarski.syntax.formulas.Formula':
        assert len(args) == 2
        return args[0] / args[1]

    def walk_bool_constant(self, expression: 'upf.model.FNode', args: List['tarski.syntax.formulas.Formula']) -> 'tarski.syntax.formulas.Formula':
        assert len(args) == 0
        if expression.bool_constant_value():
            return tarski.syntax.top
        return tarski.syntax.bot

    def walk_int_constant(self, expression: 'upf.model.FNode', args: List['tarski.syntax.formulas.Formula']) -> 'tarski.syntax.formulas.Formula':
        assert len(args) == 0
        # NOTE expression.int_constant_value() might need to be changed to str(expression.int_constant_value())
        return tarski.syntax.Constant(expression.int_constant_value(), self.lang.Real) # type: ignore

    def walk_real_constant(self, expression: 'upf.model.FNode', args: List['tarski.syntax.formulas.Formula']) -> 'tarski.syntax.formulas.Formula':
        assert len(args) == 0
        # NOTE expression.int_constant_value() might need to be changed to str(expression.int_constant_value())
        return tarski.syntax.Constant(expression.real_constant_value(), self.lang.Real) # type: ignore

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
        lang = tarski.fstrips.language(f'{problem.name}_lang', ['equality', 'arithmetic'])
        for ut in problem.user_types(): #adding user_types to the language
            lang.sort(ut.name()) # type: ignore
        for fluent in problem.fluents(): #adding fluents to the language
            signature = []
            for type in fluent.signature():
                if type.is_user_type():
                    signature.append(lang.get_sort(type.name())) # type: ignore
                else:
                    #typename will be the name that this type has in the tarski language
                    typename = str(type).replace(' ','')
                    if not lang.has_sort(typename):
                        # the type is not in the language, therefore it must be added
                        if type.is_int_type() or type.is_real_type():
                            lang.interval(typename, lang.Real, type.lower_bound(), type.upper_bound()) # type: ignore
                        else:
                            raise NotImplementedError
                    signature.append(lang.get_sort(typename))
            if fluent.type().is_bool_type():
                lang.predicate(fluent.name(), *signature)
            else:
                typename = str(fluent.type()).replace(' ','')
                if not lang.has_sort(typename):
                    # the type is not in the language, therefore it must be added
                    if fluent.type().is_int_type() or fluent.type().is_real_type():
                        lang.interval(typename, lang.Real, fluent.type().lower_bound(), fluent.type().upper_bound()) # type: ignore
                    else:
                        raise NotImplementedError
                lang.function(fluent.name(), *signature, lang.get_sort(typename)) # type: ignore
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
                                precondition=tfc.convert_formula(em.And(action.preconditions())),
                                effects=[_convert_effect(e, tfc, em) for e in action.effects()])
        for fluent_exp, value_exp in problem.initial_values().items():
            if value_exp.is_bool_constant():
                if value_exp.constant_value():
                    parameters = []
                    for a in fluent_exp.args():
                        if not a.is_object_exp():
                            raise #TODO: insert exception to raise
                        parameters.append(lang.get_constant(a.object().name()))
                    new_problem.init.add(lang.get_predicate(fluent_exp.fluent().name()), *parameters)
            else:
                new_problem.init.set(tfc.convert_formula(fluent_exp), tfc.convert_formula(value_exp))
        new_problem.goal = tfc.convert_formula(em.And(problem.goals()))
        print(tfc.convert_formula(em.And(problem.goals())))

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
