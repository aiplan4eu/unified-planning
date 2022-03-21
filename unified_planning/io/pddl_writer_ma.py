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


class ConverterToPDDLString_MA(ConverterToPDDLString):
    '''Represents a planning MultiAgentProblem.'''
    def __init__(self, *args, **kwargs):
        super(ConverterToPDDLString_MA, self).__init__(*args, **kwargs)


class PDDLWriter_MA(PDDLWriter):
    '''Represents a planning MultiAgentProblem.'''
    def __init__(self, *args, **kwargs):
        super(PDDLWriter_MA, self).__init__(*args, **kwargs)


    def _write_problem(self, out: IO[str]):
        #super()._write_problem(out)
        if self.problem.name is None:
            name = 'pddl'
        else:
            name = f'{self.problem.name}'
        out.write(f'(define (problem {name}-problem)\n')
        out.write(f' (:domain {name}-domain)\n')
        if len(self.problem.user_types()) > 0:
            out.write(' (:objects ')
            for t in self.problem.user_types():
                objects: List['unified_planning.model.Object'] = list(self.problem.objects(t))
                if len(objects) > 0:
                    out.write(
                        f'\n   {" ".join([o.name() for o in objects])} - {self._type_name_or_object_freshname(t)}')
            out.write('\n )\n')
        shared = []
        if self.problem.get_shared_data():
            for f in self.problem.get_shared_data():
                if f.type().is_bool_type():
                    params = []
                    i = 0
                    for p in f.signature():
                        if p.is_user_type():
                            params.append(f'?p{str(i)} - {self._type_name_or_object_freshname(p)}')
                            i += 1
                        else:
                            raise UPTypeError('PDDL supports only user type parameters')
                    shared.append(f'\n   ({f.name()}{"".join(params)})')
                else:
                    raise UPTypeError('Not boolean')
            out.write('(:shared-data ')
            out.write(f'{" ".join(shared)})' if len(shared) > 0 else '')
        converter = ConverterToPDDLString(self.problem.env)
        out.write('\n(:init')
        for f, v in self.problem.initial_values().items():
            if v.is_true():
                out.write(f'\n   {converter.convert(f)}')
            elif v.is_false():
                pass
            else:
                out.write(f' (= {converter.convert(f)} {converter.convert(v)})')
        if self.problem.kind().has_actions_cost():  # type: ignore
            out.write(f' (= total-cost 0)')
        out.write(')\n')
        out.write(f'(:global-goal (and\n   {" ".join([converter.convert(p) for p in self.problem.goals()])}\n))\n')
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