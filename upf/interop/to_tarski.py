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


from fractions import Fraction
from numbers import Integral
from typing import Dict, List, Optional, Tuple, Union

import upf
import upf.model
import upf.walkers as walkers

import tarski # type: ignore

class TarskiFormulaConverter(walkers.DagWalker):
    def __init__(self, language: 'tarski.fol.FirstOrderLanguage', env) -> None:
        walkers.DagWalker.__init__(self)
        self.lang = language
        self.env = env

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
        return tarski.syntax.Atom(self.lang.get_predicate(tarski.syntax.BuiltinPredicateSymbol.EQ), args)

    def walk_le(self, expression: 'upf.model.FNode', args: List['tarski.syntax.formulas.Formula']) -> 'tarski.syntax.formulas.Formula':
        assert len(args) == 2
        return tarski.syntax.Atom(self.lang.get_predicate(tarski.syntax.BuiltinPredicateSymbol.LE), args)

    def walk_lt(self, expression: 'upf.model.FNode', args: List['tarski.syntax.formulas.Formula']) -> 'tarski.syntax.formulas.Formula':
        assert len(args) == 2
        return tarski.syntax.Atom(self.lang.get_predicate(tarski.syntax.BuiltinPredicateSymbol.LT), args)

    def walk_fluent_exp(self, expression: 'upf.model.FNode', args: List['tarski.syntax.formulas.Formula']) -> 'tarski.syntax.formulas.Formula':
        tarski_fluent_rep = self.lang.get(expression.fluent().name())
        new_args = []
        for i, x in enumerate(expression.args()):
            if x.is_int_constant():
                type = (expression.fluent().signature())[i]
                typename = _type_name_added_to_language_if_needed(self.lang, type)
                constant = tarski.syntax.Constant(x.int_constant_value(), \
                    self.lang.get_sort(typename))
                new_args.append(constant)
            elif x.is_real_constant():
                raise upf.exceptions.UPFProblemDefinitionError('Fluents can not have reals into their signatures.')
            else:
                new_args.append(args[i])
        return tarski_fluent_rep(*new_args)

    def walk_plus(self, expression: 'upf.model.FNode', args: List['tarski.syntax.formulas.Formula']) -> 'tarski.syntax.formulas.Formula':
        value = args[0]
        for a in args[1:]:
            value = value + a
        return value

    def walk_minus(self, expression: 'upf.model.FNode', args: List['tarski.syntax.formulas.Formula']) -> 'tarski.syntax.formulas.Formula':
        assert len(args) == 2
        return args[0] - args[1]

    def walk_times(self, expression: 'upf.model.FNode', args: List['tarski.syntax.formulas.Formula']) -> 'tarski.syntax.formulas.Formula':
        value = args[0]
        for a in args[1:]:
            value = value * a
        return value

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
        return tarski.syntax.Constant(expression.int_constant_value(), self.lang.Integer) # type: ignore

    def walk_real_constant(self, expression: 'upf.model.FNode', args: List['tarski.syntax.formulas.Formula']) -> 'tarski.syntax.formulas.Formula':
        assert len(args) == 0
        return tarski.syntax.Constant(expression.real_constant_value(), self.lang.Real) # type: ignore

    def walk_param_exp(self, expression: 'upf.model.FNode', args: List['tarski.syntax.formulas.Formula']) -> 'tarski.syntax.formulas.Formula':
        return self.lang.variable(expression.parameter().name(), \
            self.lang.get_sort(_type_name_added_to_language_if_needed(self.lang, expression.parameter().type()))) # type: ignore

    def walk_variable_exp(self, expression: 'upf.model.FNode', args: List['tarski.syntax.formulas.Formula']) -> 'tarski.syntax.formulas.Formula':
        return self.lang.variable(expression.variable().name(), \
            self.lang.get_sort(_type_name_added_to_language_if_needed(self.lang, expression.variable().type()))) # type: ignore

    def walk_object_exp(self, expression: 'upf.model.FNode', args: List['tarski.syntax.formulas.Formula']) -> 'tarski.syntax.formulas.Formula':
        return self.lang.get_constant(expression.object().name())

def convert_problem_to_tarski(problem: 'upf.model.Problem') -> 'tarski.fstrips.problem.Problem':
    '''Converts a problem in the upf.model.Problem representation in the equivalent
    tarski.fstrips.Problem representation.'''
    features: List[str] = []
    kind = problem.kind()
    if kind.has_equality(): # type: ignore
        features.append('equality')
    if kind.has_continuous_numbers() or kind.has_discrete_numbers() or kind.has_numeric_fluents(): # type: ignore
        features.append('arithmetic')
    #creating tarski language
    lang = tarski.fstrips.language(f'{problem.name}_lang', features)
    for ut in problem.user_types(): #adding user_types to the language
        lang.sort(ut.name()) # type: ignore
    for fluent in problem.fluents(): #adding fluents to the language
        signature = []
        for type in fluent.signature():
            if type.is_user_type():
                signature.append(lang.get_sort(type.name())) # type: ignore
            else:
                #typename will be the name that this type has in the tarski language
                typename = _type_name_added_to_language_if_needed(lang, type)
                signature.append(lang.get_sort(typename))
        if fluent.type().is_bool_type():
            lang.predicate(fluent.name(), *signature)
        else:
            typename = _type_name_added_to_language_if_needed(lang, fluent.type())
            lang.function(fluent.name(), *signature, lang.get_sort(typename)) # type: ignore
    for o in problem.all_objects(): #adding objects to the language
        lang.constant(o.name(), lang.get_sort(o.type().name())) # type: ignore
    #creating tarski problem
    em = problem.env.expression_manager
    tfc = TarskiFormulaConverter(language=lang, env=problem.env)
    new_problem = tarski.fstrips.problem.create_fstrips_problem(lang, problem.name, f'{problem.name}_domain')
    for action in problem.actions():
        if not isinstance(action, upf.model.InstantaneousAction):
            raise upf.exceptions.UPFProblemDefinitionError('Tarski supports only Instantaneous Actions.')
        parameters = [lang.variable(p.name(), lang.get_sort(_type_name_added_to_language_if_needed(lang, p.type()))) for p in action.parameters()] # type: ignore
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
                    parameters.append(tfc.convert_formula(a))
                new_problem.init.add(lang.get_predicate(fluent_exp.fluent().name()), *parameters)
        else:
            value: Optional[Union[Fraction, int, 'tarski.syntax.formulas.Formula']] = None
            if value_exp.is_int_constant():
                value = value_exp.int_constant_value()
            elif value_exp.is_real_constant():
                value = value_exp.real_constant_value()
            else:
                value = tfc.convert_formula(value_exp)
            new_problem.init.set(tfc.convert_formula(fluent_exp), value)
    new_problem.goal = tfc.convert_formula(em.And(problem.goals()))
    return new_problem

def _type_name_added_to_language_if_needed(lang: 'tarski.FirstOrderLanguage', type: 'upf.model.Type') -> str:
    typename = str(type).replace(' ','')
    if type.is_int_type() and (type.lower_bound() is None or type.upper_bound() is None): # type: ignore
        if type.lower_bound() is None and type.upper_bound() is None: # type: ignore
            typename = 'Integer'
        elif type.lower_bound() == 0: # type: ignore
            assert type.upper_bound() is None # type: ignore #must be true, otherwise branch would be skipped
            typename = 'Natural'
        else:
            raise upf.exceptions.UPFProblemDefinitionError('Int type with just one bound is not accepted by tarski')
    elif type.is_real_type() and (type.lower_bound() is None or type.upper_bound() is None): # type: ignore
        if type.lower_bound() is None and type.upper_bound() is None: # type: ignore
            typename = 'Real'
        else:
            raise upf.exceptions.UPFProblemDefinitionError('Real type with just one bound is not accepted by tarski')
    if not lang.has_sort(typename):
        # the type is not in the language, therefore it must be added
        if type.is_int_type():
            lang.interval(typename, lang.Integer, type.lower_bound(), type.upper_bound()) # type: ignore
        elif type.is_real_type():
            lang.interval(typename, lang.Real, type.lower_bound(), type.upper_bound()) # type: ignore
        else:
            raise NotImplementedError
    return typename

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
