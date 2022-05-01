import re
from fractions import Fraction
import sys

from decimal import Decimal, localcontext
from warnings import warn

import unified_planning as up
import unified_planning.environment
import unified_planning.walkers as walkers
from unified_planning.model import DurativeAction
from unified_planning.exceptions import UPTypeError, UPProblemDefinitionError
from typing import IO, List, Optional
from io import StringIO
from functools import reduce
from .pddl_writer import ConverterToPDDLString
from .pddl_writer import PDDLWriter
import re

functions_dict = {}

class ConverterToPDDLString_MA(ConverterToPDDLString):
    '''Represents a planning MultiAgentProblem.'''
    def __init__(self, *args, **kwargs):
        super(ConverterToPDDLString_MA, self).__init__(*args, **kwargs)


class PDDLWriter_MA(PDDLWriter):
    '''Represents a planning MultiAgentProblem.'''
    def __init__(self, ag, *args, **kwargs):
        super(PDDLWriter_MA, self).__init__(*args, **kwargs)
        self._ag =ag
        self.agent_list = []
        self.shared_data = {}

    def remove_underscore(self, name):
        regex = r"_[a-zA-Z]+"
        subst = ""
        new_name = re.sub(regex, subst, name, 0, re.MULTILINE)
        return new_name

    def _write_agents_txt(self, out: IO[str]):
        for ag in self.problem.agents_list:
            out.write(f'{ag._ID} 127.0.0.3\n')


    def write_agents_txt(self, filename: str):
        '''Dumps to file the agents_txt.'''
        with open(filename, 'w') as f:
            self._write_agents_txt(f)


    def _write_CL_FMAP(self, out: IO[str]):
        out.write(f'java -jar FMAP.jar ')
        for ag in self.problem.agents_list:
            out.write(f'{ag._ID} ')

    def write_ma_problem(self, problems, ag_list_problems):
        wrt_domain = False
        for problem in problems:
            for ag in ag_list_problems:
                if wrt_domain == False:
                    self.write_domain(f' domain_{problem._name}')
                    wrt_domain = True
                self.write_problem(f' problem_{problem._name}_{ag}')
                self.write_agents_txt('agent-list.txt')


    def _write_domain(self, out: IO[str]):
        #for agent in self.problem.agents_list:

        problem_kind = self.problem.kind()
        if problem_kind.has_intermediate_conditions_and_effects(): # type: ignore
            raise UPProblemDefinitionError('PDDL2.1 does not support ICE.\nICE are Intermediate Conditions and Effects therefore when an Effect (or Condition) are not at StartTIming(0) or EndTIming(0).')
        if problem_kind.has_timed_effect() or problem_kind.has_timed_goals(): # type: ignore
            raise UPProblemDefinitionError('PDDL2.1 does not support timed effects or timed goals.')
        out.write('(define ')
        if self.problem.name is None:
            name = 'pddl'
        else:
            name = f'{self.problem.name}'
        #out.write(f'(domain {name}-domain)\n')
        out.write(f'(domain pddl-domain)\n')

        if self.needs_requirements:
            out.write('(:requirements :strips')
            if problem_kind.has_flat_typing(): # type: ignore
                out.write(' :typing')
            if problem_kind.has_negative_conditions(): # type: ignore
                out.write(' :negative-preconditions')
            if problem_kind.has_disjunctive_conditions(): # type: ignore
                out.write(' :disjunctive-preconditions')
            if problem_kind.has_equality(): # type: ignore
                out.write(' :equality')
            if (problem_kind.has_continuous_numbers() or # type: ignore
                problem_kind.has_discrete_numbers()): # type: ignore
                out.write(' :numeric-fluents')
            if problem_kind.has_conditional_effects(): # type: ignore
                out.write(' :conditional-effects')
            if problem_kind.has_existential_conditions(): # type: ignore
                out.write(' :existential-preconditions')
            if problem_kind.has_universal_conditions(): # type: ignore
                out.write(' :universal-preconditions')
            if (problem_kind.has_continuous_time() or # type: ignore
                problem_kind.has_discrete_time()): # type: ignore
                out.write(' :durative-actions')
            if problem_kind.has_duration_inequalities(): # type: ignore
                out.write(' :duration-inequalities')
            if self.problem.kind().has_actions_cost(): # type: ignore
                out.write(' :action-costs')
            out.write(')\n')


        if problem_kind.has_hierarchical_typing(): # type: ignore
            while self.problem.has_type(self.object_freshname):
                self.object_freshname = self.object_freshname + '_'
            user_types_hierarchy = self.problem.user_types_hierarchy()
            out.write(f'(:types')
            stack: List['unified_planning.model.Type'] = user_types_hierarchy[None] if None in user_types_hierarchy else []


            out.write(f' {" ".join(self._type_name_or_object_freshname(t) for t in stack)} - object\n')
            while stack:
                current_type = stack.pop()
                direct_sons: List['unified_planning.model.Type'] = user_types_hierarchy[current_type]
                if direct_sons:
                    #verifico se il tipo è un agente o meno, nel caso in cui è un agente, aggiungo (either ... - agent9
                    for agent in self.problem.agents_list:
                        type = self.problem.object(agent._ID)
                        if type.type() in direct_sons:
                            out.write(f'        {" ".join([self._type_name_or_object_freshname(t) for t in direct_sons])} - (either {self._type_name_or_object_freshname(current_type)} agent)\n')
                            break
                        else:
                            out.write(f'        {" ".join([self._type_name_or_object_freshname(t) for t in direct_sons])} - {self._type_name_or_object_freshname(current_type)}\n')
                            break
            out.write(')\n')
        else:

            out.write(f' (:types {" ".join([t.name() for t in self.problem.user_types()])})\n' if len(self.problem.user_types()) > 0 else '') # type: ignore

        predicates = []
        functions = []

        dict = {}
        #raggruppo i fluenti "flu_" e aggiungo either
        for f in self.problem.fluents():
            if f.type().is_bool_type():
                if f not in self.problem.get_flu_functions():
                    import re
                    p = re.compile(r"[a-z]+_")
                    query = re.search(p, f.name())
                    if query:
                        if query[0] not in dict:
                            dict[query[0]] = []
                        for p in f.signature():
                            if p.is_user_type():
                                if self._type_name_or_object_freshname(p) not in dict[query[0]]:
                                    type = self._type_name_or_object_freshname(p)
                                    dict[query[0]].append(type)
        #for f in self.problem.fluents():
        #    if f.type().is_bool_type():
        #        if f not in self.problem.get_flu_functions():
        #            params = []
        #            i = 0
        #            for p in f.signature():
        #                if p.is_user_type():
        #                    params.append(f' ?p{str(i)} - {self._type_name_or_object_freshname(p)}')
        #                    i += 1
        #                else:
        #                    raise UPTypeError('PDDL supports only user type parameters')
        #            predicates.append(f'({f.name()}{"".join(params)})\n')

            elif f.type().is_int_type() or f.type().is_real_type():
                params = []
                i = 0
                for p in f.signature():
                    if p.is_user_type():
                        params.append(f' ?p{str(i)} - {self._type_name_or_object_freshname(p)}')
                        i += 1
                    else:
                        raise UPTypeError('PDDL supports only user type parameters')
                functions.append(f'({f.name()}{"".join(params)})')
            else:
                raise UPTypeError('PDDL supports only boolean and numerical fluents')
        if self.problem.kind().has_actions_cost(): # type: ignore
            functions.append('(total-cost)')

        #type = self.problem.get_obj_type_father(self.problem.agents_list[0]._ID)
        #type = self.problem.get_obj_type_father(self._ag)

        #print(type, self._ag, ok.type().name())
        #breakpoint()

        type = self.problem.object(self._ag).type()
        if type._father.name() == 'agent':
            type = type.name()
        else:
            type = type._father


        #out.write(f'(:predicates \n  (myAgent ?a - {type})\n  {"  ".join(predicates)})\n' if len(predicates) > 0 else '')

        out.write(f'(:predicates \n  (myAgent ?a - {type})')
        for i, k in dict.items():
            if len(k) > 1:
                out.write(f'\n  ({i[:-1]} ?x - (either {" ".join([t for t in k])}))')
            else:
                out.write(f'\n  ({i[:-1]} ?x - {k[0]})')

        out.write(f')\n')
        if self.problem.get_flu_functions():
            out.write(f'(:functions\n')
            for f in self.problem.get_flu_functions():
                if f.type().is_bool_type():
                    user_type_name = f.name()
                    import re
                    p = re.compile(r"[a-z]+_")
                    query = re.search(p, user_type_name)
                    if query:
                        if query[0] not in functions_dict:
                            functions_dict[query[0]] = []
                        for p in f.signature():
                            if p.is_user_type():
                                if self._type_name_or_object_freshname(p) not in functions_dict[query[0]]:
                                    type = self._type_name_or_object_freshname(p)
                                    functions_dict[query[0]].append(type)
                    else:
                        if user_type_name not in dict:
                            functions_dict[user_type_name] = []
                        for p in f.signature():
                            if p.is_user_type():
                                if self._type_name_or_object_freshname(p) not in functions_dict[user_type_name]:
                                    type = self._type_name_or_object_freshname(p)
                                    functions_dict[user_type_name].append(type)
            for i, k in functions_dict.items():
                if len(k) > 2:
                    i = i.replace("_", "")
                    out.write(f'  ({i} ?{k[0][0]} - {k[0]}) - (either {" ".join([t for t in k[1:]])})\n')
                else:
                    i = i.replace("_", "")
                    out.write(f'  ({i} ?{k[0][0]} - {k[0]}) - {k[1]}\n')


                    #out.write(f'\n  ({user_type_name} ?{(f.signature()[0].name())[0]} - {") - ".join([str(o.name()) for o in f.signature()])}')
                    #params = []
                    #i = 0
                    #for p in f.signature():
                    #    if p.is_user_type():
                    #        params.append(f' ?p{str(i)} - {self._type_name_or_object_freshname(p)}')
                    #        i += 1
                    #    else:
                    #        raise UPTypeError('PDDL supports only user type parameters')
                    #functions.append(f'({f.name()}{"".join(params)})\n')
            out.write(f')\n')

        converter = ConverterToPDDLString(self.problem.env)
        for a in self.problem.actions():
            if isinstance(a, up.model.InstantaneousAction):
                out.write(f'(:action {a.name}')
                out.write(f'\n :parameters (')
                for ap in a.parameters():
                    if ap.type().is_user_type():
                        out.write(f' ?{ap.name()} - {self._type_name_or_object_freshname(ap.type())}')
                    else:
                        raise UPTypeError('PDDL supports only user type parameters')
                out.write(')')

                #preconditions
                if len(a.preconditions()) > 0:
                    type = self.problem.get_obj_type_father(self._ag)
                    for ap in a.parameters():
                        if type == ap.type() :
                            parameter_name = ap.name()
                        elif ap.type()._father == type:
                            parameter_name = ap.name()
                        elif type.name() == 'agent':
                            parameter_name = str(self.problem.object(self._ag).type().name())[0]

                    out.write(f'\n :precondition (and')
                    out.write(f' (myAgent ?{parameter_name})')
                    for p in a.preconditions():
                        # print(p, "(", p.fluent().name(), "?", p._content.args[0], ")", converter.convert(p))

                        if len(p._content.args) > 1 and p.is_fluent_exp() and p.fluent() in self.problem.get_flu_functions():
                            flu_name = p.fluent().name()
                            #out.write(f'\n :precondition (and {" ".join([converter.convert(p)])})')
                            flu_name = self.remove_underscore(flu_name)
                            out.write(f' (= ({flu_name} ?{")".join([str(p.arg(0))])}) ?{p.arg(1)})')
                        else:
                            p = converter.convert(p)
                            p = self.remove_underscore(p)
                            out.write(f' {" ".join([p])}')
                out.write(')')
                if len(a.effects()) > 0:
                    out.write('\n :effect (and')
                    for e in a.effects():
                        if e.is_conditional():
                            if len(e._content.args) > 1 and e.fluent() in self.problem.get_flu_functions():
                                flu_name = e.fluent().name()
                                # out.write(f'\n :precondition (and {" ".join([converter.convert(p)])})')
                                flu_name = self.remove_underscore(flu_name)
                                out.write(f' (when (= ({flu_name} ?{")".join([str(e.arg(0))])}) ?{e.arg(1)})')
                            else:
                                new_e = converter.convert(e.condition())
                                new_e = self.remove_underscore(new_e)
                                out.write(f' (when {new_e}')
                        if e.value().is_true():
                            if len(e.fluent()._content.args) > 1 and e.fluent().fluent() in self.problem.get_flu_functions():
                                flu_name = e.fluent().fluent().name()
                                # out.write(f'\n :precondition (and {" ".join([converter.convert(p)])})')
                                flu_name = self.remove_underscore(flu_name)
                                out.write(f' (assign ({flu_name} ?{")".join([str(e.fluent().arg(0))])}) ?{e.fluent().arg(1)})')
                            else:
                                new_e = converter.convert(e.fluent())
                                new_e = self.remove_underscore(new_e)
                                out.write(f' {new_e}')


                        elif e.value().is_false():
                            if len(e.fluent()._content.args) > 1 and e.fluent().fluent() in self.problem.get_flu_functions():
                                flu_name = e.fluent().fluent().name()
                                # out.write(f'\n :precondition (and {" ".join([converter.convert(p)])})')
                                flu_name = self.remove_underscore(flu_name)
                                out.write(f' (not (= ({flu_name} ?{")".join([str(e.fluent().arg(0))])}) ?{e.fluent().arg(1)})')
                            else:
                                new_e = converter.convert(e.fluent())
                                new_e= self.remove_underscore(new_e)
                                out.write(f' (not {new_e})')

                        elif e.is_increase():
                            if len(e.fluent()._content.args) > 1 and e.fluent().fluent() in self.problem.get_flu_functions():
                                flu_name = e.fluent().fluent().name()
                                # out.write(f'\n :precondition (and {" ".join([converter.convert(p)])})')
                                flu_name = self.remove_underscore(flu_name)
                                out.write(f' (increase (= ({flu_name} ?{")".join([str(e.fluent().arg(0))])}) ?{e.fluent().arg(1)} {converter.convert(e.value())})')
                            else:
                                new_e = converter.convert(e.fluent())
                                new_e = self.remove_underscore(new_e)
                                out.write(f' (increase {new_e} {converter.convert(e.value())})')

                        elif e.is_decrease():
                            if len(e.fluent()._content.args) > 1 and e.fluent().fluent() in self.problem.get_flu_functions():
                                flu_name = e.fluent().fluent().name()
                                # out.write(f'\n :precondition (and {" ".join([converter.convert(p)])})')
                                flu_name = self.remove_underscore(flu_name)
                                out.write(f' (decrease (= ({flu_name} ?{")".join([str(e.fluent().arg(0))])}) ?{e.fluent().arg(1)} {converter.convert(e.value())})')
                            else:
                                new_e = converter.convert(e.fluent())
                                new_e = self.remove_underscore(new_e)
                                out.write(f' (decrease {new_e} {converter.convert(e.value())})')

                        else:
                            new_e = converter.convert(e.fluent())
                            new_e = self.remove_underscore(new_e)
                            out.write(f' (assign {new_e} {converter.convert(e.value())})')
                        if e.is_conditional():
                            out.write(f')')

                    if a.cost() is not None:
                        out.write(f' (increase total-cost {converter.convert(a.cost())})')
                    out.write(')')
                out.write(')\n')
            elif isinstance(a, DurativeAction):
                out.write(f' (:durative-action {a.name}')
                out.write(f'\n  :parameters (')
                for ap in a.parameters():
                    if ap.type().is_user_type():
                        out.write(f' ?{ap.name()} - {self._type_name_or_object_freshname(ap.type())}')
                    else:
                        raise UPTypeError('PDDL supports only user type parameters')
                out.write(')')
                l, r = a.duration().lower(), a.duration().upper()
                if l == r:
                    out.write(f'\n  :duration (= ?duration {str(l)})')
                else:
                    out.write(f'\n  :duration (and ')
                    if a.duration().is_left_open():
                        out.write(f'(> ?duration {str(l)})')
                    else:
                        out.write(f'(>= ?duration {str(l)})')
                    if a.duration().is_right_open():
                        out.write(f'(< ?duration {str(r)})')
                    else:
                        out.write(f'(<= ?duration {str(r)})')
                    out.write(')')
                if len(a.conditions()) > 0:
                    out.write(f'\n  :condition (and ')
                    for interval, cl in a.conditions().items():
                        for c in cl:
                            if interval.lower() == interval.upper():
                                if interval.lower().is_from_start():
                                    out.write(f'(at start {converter.convert(c)})')
                                else:
                                    out.write(f'(at end {converter.convert(c)})')
                            else:
                                if not interval.is_left_open():
                                    out.write(f'(at start {converter.convert(c)})')
                                out.write(f'(over all {converter.convert(c)})')
                                if not interval.is_right_open():
                                    out.write(f'(at end {converter.convert(c)})')
                    out.write(')')
                if len(a.effects()) > 0:
                    out.write('\n  :effect (and')
                    for t, el in a.effects().items():
                        for e in el:
                            if t.is_from_start():
                                out.write(f' (at start')
                            else:
                                out.write(f' (at end')
                            if e.is_conditional():
                                out.write(f' (when {converter.convert(e.condition())}')
                            if e.value().is_true():
                                out.write(f' {converter.convert(e.fluent())}')
                            elif e.value().is_false():
                                out.write(f' (not {converter.convert(e.fluent())})')
                            elif e.is_increase():
                                out.write(f' (increase {converter.convert(e.fluent())} {converter.convert(e.value())})')
                            elif e.is_decrease():
                                out.write(f' (decrease {converter.convert(e.fluent())} {converter.convert(e.value())})')
                            else:
                                out.write(f' (assign {converter.convert(e.fluent())} {converter.convert(e.value())})')
                            if e.is_conditional():
                                out.write(f')')
                            out.write(')')
                    if a.cost() is not None:
                        out.write(f' (at end (increase total-cost {converter.convert(a.cost())}))')
                    out.write(')')
                out.write(')\n')
            else:
                raise NotImplementedError
        out.write(')\n')

    def _write_problem(self, out: IO[str]):
        #super()._write_problem(out)
        if self.problem.name is None:
            name = 'pddl'
        else:
            name = f'{self.problem.name}'
        #out.write(f'(define (problem {name}-problem)\n')
        out.write(f'(define (problem pddl-problem)\n')
        #out.write(f'(:domain {name}-domain)\n')
        out.write(f'(:domain pddl-domain)\n')
        if len(self.problem.user_types()) > 0:
            out.write('(:objects ')
            for t in self.problem.user_types():
                objects: List['unified_planning.model.Object'] = list(self.problem.objects(t))
                if len(objects) > 0:
                    out.write(
                        f'\n {" ".join([o.name() for o in objects])} - {self._type_name_or_object_freshname(t)}')
            out.write('\n)\n')
        shared = []
        dict = {}
        out.write('(:shared-data')
        if self.problem.get_shared_data():
            for f in self.problem.get_shared_data():
                if f.type().is_bool_type():
                    data_name = f.name()
                    p = re.compile(r"[a-z]+_")
                    query = re.search(p, data_name)
                    if query:
                        if query[0] not in dict:
                            dict[query[0]] = []
                        for p in f.signature():
                            if p.is_user_type():
                                if self._type_name_or_object_freshname(p) not in dict[query[0]]:
                                    type = self._type_name_or_object_freshname(p)
                                    dict[query[0]].append(type)
                    else:
                        if data_name not in dict:
                            dict[data_name] = []
                        for p in f.signature():
                            if p.is_user_type():
                                if self._type_name_or_object_freshname(p) not in dict[data_name]:
                                    type = self._type_name_or_object_freshname(p)
                                    dict[data_name].append(type)
                else:
                    raise UPTypeError('Not boolean')
            ok = {}
            for i, k in dict.items():
                if len(k) > 2:
                    #k.pop(0)
                    i = i.replace("_", "")
                    out.write(f'\n  (({i} ?{k[0][0]} - {k[0]}) - (either {" ".join([t for t in k[1:]])}))')
                else:
                    if i not in functions_dict:
                        i = i.replace("_", "")
                        out.write(f'\n  ({i} ?x - (either {k[0]} {k[1]}))')
                    else:
                        i = i.replace("_", "")
                        out.write(f'\n  (({i} ?{k[0][0]} - {k[0]}) - {k[1]})')


                    #params = []
                    #i = 0

                    #user_type_name = f.name()
                    #if len(f.signature()) > 1:
                    #    out.write(f'\n (({user_type_name} ?{(f.signature()[0].name())[0]} - {") - ".join([str(o.name())  for o in f.signature()])})')
                    #else:
                    #    out.write(
                    #        f'\n ({user_type_name} ?{(f.signature()[0].name())[0]} - {") - ".join([str(o.name()) for o in f.signature()])})')

                    #for p in f.signature():
                    #    if p.is_user_type():
                    #        params.append(f'?{(str(p.name()))[0]}{str(i)} - {self._type_name_or_object_freshname(p)}')
                    #        i += 1
                    #    else:
                    #        raise UPTypeError('PDDL supports only user type parameters')
                    #shared.append(f'\n  ({f.name()}{"".join(params)})')

                    #Verificare se è possibile fare: ((pos ?c - crate) - (either place truck)) "aggiungere either"
                    #print(f, f.signature()[0].father(), f.signature()[0].name(), "ooooooooooooooooooo")
                    #print(self._type_name_or_object_freshname(f))

                #else:
                #    raise UPTypeError('Not boolean')
            #out.write('(:shared-data ')
            #out.write(f'{" ".join(shared)})' if len(shared) > 0 else '')
        shared_agents = []
        for agent in self.problem.get_agents():
            if agent._ID == self._ag:
                pass
            else:
                shared_agents.append(agent._ID)
        out.write(f' - \n(either {" ".join([str(o) for o in shared_agents])})')
        out.write('\n)')
        converter = ConverterToPDDLString(self.problem.env)

        out.write('\n(:init\n')
        type = self.problem.object(self._ag)
        out.write(f' (myAgent {type})')
        for f, v in self.problem.initial_values().items():
            if v.is_true():
                if f.is_fluent_exp() and f.fluent() in self.problem.get_flu_functions():
                    fluent = f.fluent().name()
                    regex = r"_[a-zA-Z]+"
                    subst = ""
                    fluent = re.sub(regex, subst, fluent, 0, re.MULTILINE)
                    out.write(f'\n (= ({fluent} {") ".join([converter.convert(o) for o in f._content.args])})')

                    #print(f.fluent().name())
                else:
                    #fluent = f._content.args[0].fluent().name()
                    f = converter.convert(f)

                    regex = r"_[a-zA-Z]+"
                    subst = ""
                    f = re.sub(regex, subst, f, 0, re.MULTILINE)
                    out.write(f'\n {f}')

            elif v.is_false():
                pass
            else:
                f = converter.convert(f)
                v = converter.convert(v)
                regex = r"_[a-zA-Z]+"
                subst = ""
                f = re.sub(regex, subst, f, 0, re.MULTILINE)
                v = re.sub(regex, subst, v, 0, re.MULTILINE)
                out.write(f'\n (= {f} {v})')
        if self.problem.kind().has_actions_cost():  # type: ignore
            out.write(f' (= total-cost 0)')
        out.write('\n)\n')
        out.write(f'(:global-goal (and')
        nl = '\n '
        for p in self.problem.goals():
            if p.fluent() in self.problem.get_flu_functions():
                fluent = p.fluent().name()
                regex = r"_[a-zA-Z]+"
                subst = ""
                fluent = re.sub(regex, subst, fluent, 0, re.MULTILINE)
                out.write(f'\n (= ({fluent} {") ".join([converter.convert(o) for o in p._content.args])})')
            #out.write(f'(:global-goal (and\n {nl.join([converter.convert(p) for p in self.problem.goals()])}\n))\n')
            else:
                p = converter.convert(p)
                regex = r"_[a-zA-Z]+"
                subst = ""
                p = re.sub(regex, subst, p, 0, re.MULTILINE)
                out.write(f'\n {" ".join([p])}')
        out.write(f'\n))\n')

        metrics = self.problem.quality_metrics()
        if len(metrics) == 1:
            metric = metrics[0]
            out.write(' (:metric ')
            if isinstance(metric, up.model.metrics.MinimizeExpressionOnFinalState):
                out.write(f'minimize {metric.expression}')
            elif isinstance(metric, up.model.metrics.MaximizeExpressionOnFinalState):
                out.write(f'maximize {metric.expression}')
            elif isinstance(metric, up.model.metrics.MinimizeActionCosts):
                out.write(f'minimize total-cost')
            else:
                raise
            out.write(')\n')
        elif len(metrics) > 1:
            raise
        out.write(')\n')