# Copyright 2021-2023 AIPlan4EU project
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


import importlib
import sys
import os
import inspect
import configparser
import unified_planning as up
from unified_planning.environment import Environment
from unified_planning.exceptions import UPUsageError
from unified_planning.model import ProblemKind
from unified_planning.plans import PlanKind
from unified_planning.engines.mixins.oneshot_planner import OptimalityGuarantee
from unified_planning.engines.mixins.anytime_planner import AnytimeGuarantee
from unified_planning.engines.mixins.anytime_planner import AnytimePlannerMixin
from unified_planning.engines.mixins.compiler import CompilationKind, CompilerMixin
from unified_planning.engines.mixins.oneshot_planner import OneshotPlannerMixin
from unified_planning.engines.mixins.plan_validator import PlanValidatorMixin
from unified_planning.engines.mixins.portfolio import PortfolioSelectorMixin
from unified_planning.engines.mixins.replanner import ReplannerMixin
from unified_planning.engines.mixins.plan_repairer import PlanRepairerMixin
from unified_planning.engines.mixins.sequential_simulator import (
    SequentialSimulatorMixin,
)
from unified_planning.engines.engine import OperationMode
from typing import IO, Any, Dict, Tuple, Optional, List, Union, Type, Sequence, cast
from pathlib import PurePath


DEFAULT_ENGINES = {
    "fast-downward": ("up_fast_downward", "FastDownwardPDDLPlanner"),
    "fast-downward-opt": ("up_fast_downward", "FastDownwardOptimalPDDLPlanner"),
    "symk": ("up_symk", "SymKPDDLPlanner"),
    "symk-opt": ("up_symk", "SymKOptimalPDDLPlanner"),
    "pyperplan": ("up_pyperplan.engine", "EngineImpl"),
    "pyperplan-opt": ("up_pyperplan.engine", "OptEngineImpl"),
    "enhsp": ("up_enhsp.enhsp_planner", "ENHSPSatEngine"),
    "enhsp-opt": ("up_enhsp.enhsp_planner", "ENHSPOptEngine"),
    "enhsp-any": ("up_enhsp.enhsp_planner", "ENHSPAnytimeEngine"),
    "tamer": ("up_tamer.engine", "EngineImpl"),
    "lpg": ("up_lpg.lpg_planner", "LPGEngine"),
    "lpg-anytime": ("up_lpg.lpg_planner", "LPGAnytimeEngine"),
    "lpg-repairer": ("up_lpg.lpg_planner", "LPGPlanRepairer"),
    "fmap": ("up_fmap.fmap_planner", "FMAPsolver"),
    "aries": ("up_aries", "Aries"),
    "aries-val": ("up_aries", "AriesVal"),
    "sequential_plan_validator": (
        "unified_planning.engines.plan_validator",
        "SequentialPlanValidator",
    ),
    "sequential_simulator": (
        "unified_planning.engines.sequential_simulator",
        "UPSequentialSimulator",
    ),
    "up_bounded_types_remover": (
        "unified_planning.engines.compilers.bounded_types_remover",
        "BoundedTypesRemover",
    ),
    "up_conditional_effects_remover": (
        "unified_planning.engines.compilers.conditional_effects_remover",
        "ConditionalEffectsRemover",
    ),
    "up_disjunctive_conditions_remover": (
        "unified_planning.engines.compilers.disjunctive_conditions_remover",
        "DisjunctiveConditionsRemover",
    ),
    "up_state_invariants_remover": (
        "unified_planning.engines.compilers.state_invariants_remover",
        "StateInvariantsRemover",
    ),
    "up_negative_conditions_remover": (
        "unified_planning.engines.compilers.negative_conditions_remover",
        "NegativeConditionsRemover",
    ),
    "up_quantifiers_remover": (
        "unified_planning.engines.compilers.quantifiers_remover",
        "QuantifiersRemover",
    ),
    "up_usertype_fluents_remover": (
        "unified_planning.engines.compilers.usertype_fluents_remover",
        "UsertypeFluentsRemover",
    ),
    "tarski_grounder": (
        "unified_planning.engines.compilers.tarski_grounder",
        "TarskiGrounder",
    ),
    "fast-downward-grounder": ("up_fast_downward", "FastDownwardGrounder"),
    "fast-downward-reachability-grounder": (
        "up_fast_downward",
        "FastDownwardReachabilityGrounder",
    ),
    "up_grounder": ("unified_planning.engines.compilers.grounder", "Grounder"),
    "up_ma_disjunctive_conditions_remover": (
        "unified_planning.engines.compilers.ma_disjunctive_conditions_remover",
        "MA_DisjunctiveConditionsRemover",
    ),
    "up_ma_conditional_effects_remover": (
        "unified_planning.engines.compilers.ma_conditional_effects_remover",
        "MA_ConditionalEffectsRemover",
    ),
}

DEFAULT_META_ENGINES = {
    "oversubscription": (
        "unified_planning.engines.oversubscription_planner",
        "OversubscriptionPlanner",
    ),
    "replanner": (
        "unified_planning.engines.replanner",
        "Replanner",
    ),
}

DEFAULT_ENGINES_PREFERENCE_LIST = [
    "fast-downward",
    "fast-downward-opt",
    "symk",
    "symk-opt",
    "pyperplan",
    "pyperplan-opt",
    "enhsp",
    "enhsp-opt",
    "enhsp-any",
    "tamer",
    "sequential_plan_validator",
    "sequential_simulator",
    "up_bounded_types_remover",
    "up_conditional_effects_remover",
    "up_disjunctive_conditions_remover",
    "up_ma_disjunctive_conditions_remover",
    "up_ma_conditional_effects_remover",
    "up_negative_conditions_remover",
    "up_quantifiers_remover",
    "up_state_invariants_remover",
    "up_usertype_fluents_remover",
    "tarski_grounder",
    "fast-downward-reachability-grounder",
    "fast-downward-grounder",
    "up_grounder",
    "lpg",
    "lpg-anytime",
    "lpg-repairer",
    "fmap",
    "aries",
    "aries-val",
]

DEFAULT_META_ENGINES_PREFERENCE_LIST = ["oversubscription"]


def format_table(header: List[str], rows: List[List[str]]) -> str:
    row_template = "|"
    for i in range(len(header)):
        l = max(len(r[i]) for r in [header] + rows)
        row_template += f" {{:<{str(l)}}} |"
    header_str = row_template.format(*header)
    row_len = len(header_str)
    rows_str = [f'{"-"*row_len}', f"{header_str}", f'{"="*row_len}']
    for row in rows:
        rows_str.append(f"{row_template.format(*row)}")
        rows_str.append(f'{"-"*row_len}')
    return "\n".join(rows_str)


def get_possible_config_locations() -> List[str]:
    """Returns all the possible location of the configuration file."""
    home = os.path.expanduser("~")
    files = []
    stack = inspect.stack()
    for p in PurePath(os.path.abspath(stack[-1].filename)).parents:
        files.append(os.path.join(p, "up.ini"))
        files.append(os.path.join(p, ".up.ini"))
    files.append(os.path.join(home, "up.ini"))
    files.append(os.path.join(home, ".up.ini"))
    files.append(os.path.join(home, ".uprc"))
    return files


class Factory:
    """
    Class that manages all the different :class:`Engines <unified_planning.engines.Engine>` classes
    and handles the operation modes available in the library.
    """

    def __init__(self, environment: "Environment"):
        self._env = environment
        self._engines: Dict[str, Type["up.engines.engine.Engine"]] = {}
        self._engines_info: List[Tuple[str, str, str]] = []
        self._meta_engines: Dict[str, Type["up.engines.meta_engine.MetaEngine"]] = {}
        self._meta_engines_info: List[Tuple[str, str, str]] = []
        self._credit_disclaimer_printed = False
        for name, (module_name, class_name) in DEFAULT_ENGINES.items():
            try:
                self._add_engine(name, module_name, class_name)
            except ImportError:
                pass
        engines = dict(self._engines)
        for name, (module_name, class_name) in DEFAULT_META_ENGINES.items():
            try:
                for engine_name, engine in engines.items():
                    self._add_meta_engine(
                        name, module_name, class_name, engine_name, engine
                    )
            except ImportError:
                pass
        self._preference_list = []
        for name in DEFAULT_ENGINES_PREFERENCE_LIST:
            if name in self._engines:
                self._preference_list.append(name)
        for name in DEFAULT_META_ENGINES_PREFERENCE_LIST:
            for e in self._engines.keys():
                if e.startswith(f"{name}["):
                    self._preference_list.append(e)
        self.configure_from_file()

    # The getstate and setstate method are needed in the Parallel engine.
    # The Parallel engine creates a deep copy of the Factory instance
    # in another process by pickling it.
    # Since local classes are not picklable and engines instantiated from
    # a meta engine are local classes, we need to remove them from the
    # state and then re-create them in the new process.
    def __getstate__(self):
        state = self.__dict__.copy()
        del state["_engines"]
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._engines = {}
        engines_info = list(self._engines_info)
        self._engines_info = []
        for name, module_name, class_name in engines_info:
            self._add_engine(name, module_name, class_name)
        engines = dict(self._engines)
        meta_engines_info = list(self._meta_engines_info)
        self._meta_engines_info = []
        for name, module_name, class_name in meta_engines_info:
            for engine_name, engine in engines.items():
                self._add_meta_engine(
                    name, module_name, class_name, engine_name, engine
                )

    @property
    def engines(self) -> List[str]:
        """Returns the list of the available :class:`Engines <unified_planning.engines.Engine>` names."""
        return list(self._engines.keys())

    def engine(self, name: str) -> Type["up.engines.engine.Engine"]:
        """
        Returns a specific `Engine` class.

        :param name: The name of the `engine` in the factory.
        :return: The `engine` Class.
        """
        return self._engines[name]

    @property
    def preference_list(self) -> List[str]:
        """Returns the current list of preferences."""
        return self._preference_list

    @preference_list.setter
    def preference_list(self, preference_list: List[str]):
        """
        Defines the order in which to pick the :class:`Engines <unified_planning.engines.Engine>`.
        The list is not required to contain all the `Engines`. It is
        possible to define a subsets of the `Engines`, or even just
        one.

        The impact of not including an `Engine`, is that it will never be
        selected automatically. Note, however, that it can
        still be selected by using it's name in the Operation modes.
        """
        self._preference_list = preference_list

    def add_engine(self, name: str, module_name: str, class_name: str):
        """
        Adds an :class:`Engine <unified_planning.engines.Engine>` Class to the factory, given the module and the class names.

        :param name: The `name` of the added `engine Class` in the factory.
        :param module_name: The `name` of the module in which the `engine Class` is defined.
        :param class_name: The `name` of the `engine Class`.
        """
        self._add_engine(name, module_name, class_name)
        self._preference_list.append(name)
        engine = self._engines[name]
        for me_name, me in self._meta_engines.items():
            if me.is_compatible_engine(engine):
                n = f"{me_name}[{name}]"
                self._engines[n] = me[engine]
                self._preference_list.append(n)

    def add_meta_engine(self, name: str, module_name: str, class_name: str):
        """
        Adds a :class:`MetaEngine <unified_planning.engines.MetaEngine>` Class to the `Factory`, given the module and the class names.

        :param name: The `name` of the added `meta engine Class` in the factory.
        :param module_name: The `name` of the module in which the `meta engine Class` is defined.
        :param class_name: The name of the `meta engine Class`.
        """
        engines = dict(self._engines)
        for engine_name, engine in engines.items():
            self._add_meta_engine(name, module_name, class_name, engine_name, engine)
            n = f"{name}[{engine_name}]"
            if n in self.engines:
                self._preference_list.append(n)

    def configure_from_file(self, config_filename: Optional[str] = None):
        """
        Reads a configuration file and configures the factory.

        The following is an example of configuration file:


        [global]
        engine_preference_list: fast-downward fast-downward-opt enhsp enhsp-opt tamer

        [engine <engine-name>]
        module_name: <module-name>
        class_name: <class-name>


        If not given, the configuration is read from the first `up.ini` or `.up.ini` file
        located in any of the parent directories from which this code was called  or,
        otherwise, from one of the following files: `~/up.ini`, `~/.up.ini`, `~/.uprc`.

        :param config_filename: The path of the file containing the wanted configuration.
        """
        config = configparser.ConfigParser()
        if config_filename is None:
            files = get_possible_config_locations()
            config.read(files)
        else:
            config.read([config_filename])

        new_engine_sections = [
            s for s in config.sections() if s.lower().startswith("engine ")
        ]

        for s in new_engine_sections:
            name = s[len("engine ") :]

            module_name = config.get(s, "module_name")
            assert module_name is not None, (
                "Missing 'module_name' value in definition" "of '%s' engine" % name
            )

            class_name = config.get(s, "class_name")
            assert class_name is not None, (
                "Missing 'class_name' value in definition" "of '%s' engine" % name
            )

            self.add_engine(name, module_name, class_name)

        new_meta_engine_sections = [
            s for s in config.sections() if s.lower().startswith("meta-engine ")
        ]

        for s in new_meta_engine_sections:
            name = s[len("meta-engine ") :]

            module_name = config.get(s, "module_name")
            assert module_name is not None, (
                "Missing 'module_name' value in definition of '%s' meta-engine" % name
            )

            class_name = config.get(s, "class_name")
            assert class_name is not None, (
                "Missing 'class_name' value in definition of '%s' meta-engine" % name
            )

            self.add_meta_engine(name, module_name, class_name)

        if "global" in config.sections():
            pref_list = config.get("global", "engine_preference_list")

            if pref_list is not None:
                prefs = [x.strip() for x in pref_list.split() if len(x.strip()) > 0]
                self.preference_list = [e for e in prefs if e in self.engines]

    def _add_engine(self, name: str, module_name: str, class_name: str):
        module = importlib.import_module(module_name)
        EngineImpl = getattr(module, class_name)
        self._engines[name] = EngineImpl
        self._engines_info.append((name, module_name, class_name))

    def _add_meta_engine(
        self,
        name: str,
        module_name: str,
        class_name: str,
        engine_name: str,
        engine: Type["up.engines.engine.Engine"],
    ):
        if name in self._meta_engines:
            EngineImpl = self._meta_engines[name]
        else:
            module = importlib.import_module(module_name)
            EngineImpl = getattr(module, class_name)
            self._meta_engines[name] = EngineImpl
            self._meta_engines_info.append((name, module_name, class_name))
        if EngineImpl.is_compatible_engine(engine):
            self._engines[f"{name}[{engine_name}]"] = EngineImpl[engine]

    def _engine_satisfies_conditions(
        self,
        EngineClass: Type["up.engines.engine.Engine"],
        operation_mode: "OperationMode",
        problem_kind: ProblemKind,
        optimality_guarantee: Optional["OptimalityGuarantee"],
        compilation_kind: Optional["CompilationKind"],
        plan_kind: Optional["PlanKind"],
        anytime_guarantee: Optional["AnytimeGuarantee"],
    ) -> bool:
        if not getattr(EngineClass, "is_" + operation_mode.value)():
            return False
        if (
            operation_mode == OperationMode.ONESHOT_PLANNER
            or operation_mode == OperationMode.REPLANNER
            or operation_mode == OperationMode.PORTFOLIO_SELECTOR
        ):
            assert (
                issubclass(EngineClass, OneshotPlannerMixin)
                or issubclass(EngineClass, ReplannerMixin)
                or issubclass(EngineClass, PortfolioSelectorMixin)
            )
            assert anytime_guarantee is None
            assert compilation_kind is None
            assert plan_kind is None
            if optimality_guarantee is not None and not EngineClass.satisfies(
                optimality_guarantee
            ):
                return False
        elif operation_mode == OperationMode.PLAN_VALIDATOR:
            assert issubclass(EngineClass, PlanValidatorMixin)
            assert optimality_guarantee is None
            assert anytime_guarantee is None
            assert compilation_kind is None
            if plan_kind is not None and not EngineClass.supports_plan(plan_kind):
                return False
        elif operation_mode == OperationMode.COMPILER:
            assert issubclass(EngineClass, CompilerMixin)
            assert optimality_guarantee is None
            assert anytime_guarantee is None
            assert plan_kind is None
            if compilation_kind is not None and not EngineClass.supports_compilation(
                compilation_kind
            ):
                return False
        elif operation_mode == OperationMode.ANYTIME_PLANNER:
            assert issubclass(EngineClass, AnytimePlannerMixin)
            assert optimality_guarantee is None
            assert compilation_kind is None
            assert plan_kind is None
            if anytime_guarantee is not None and not EngineClass.ensures(
                anytime_guarantee
            ):
                return False
        elif operation_mode == OperationMode.PLAN_REPAIRER:
            assert issubclass(EngineClass, PlanRepairerMixin)
            assert anytime_guarantee is None
            assert compilation_kind is None
            if plan_kind is not None and not EngineClass.supports_plan(plan_kind):
                return False
            if optimality_guarantee is not None and not EngineClass.satisfies(
                optimality_guarantee
            ):
                return False
        else:
            assert optimality_guarantee is None
            assert anytime_guarantee is None
            assert compilation_kind is None
            assert plan_kind is None
        return EngineClass.supports(problem_kind)

    def _get_engine_class(
        self,
        operation_mode: "OperationMode",
        name: Optional[str] = None,
        problem_kind: ProblemKind = ProblemKind(),
        optimality_guarantee: Optional["OptimalityGuarantee"] = None,
        compilation_kind: Optional["CompilationKind"] = None,
        plan_kind: Optional["PlanKind"] = None,
        anytime_guarantee: Optional["AnytimeGuarantee"] = None,
    ) -> Type["up.engines.engine.Engine"]:
        if name is not None:
            if name in self._engines:
                return self._engines[name]
            else:
                raise up.exceptions.UPNoRequestedEngineAvailableException
        problem_features = list(problem_kind.features)
        planners_features = []
        # Make sure that optimality guarantees and compilation kind are mutually exclusive
        assert optimality_guarantee is None or compilation_kind is None
        for name in self._preference_list:
            EngineClass = self._engines[name]
            if self._engine_satisfies_conditions(
                EngineClass,
                operation_mode,
                problem_kind,
                optimality_guarantee,
                compilation_kind,
                plan_kind,
                anytime_guarantee,
            ):
                return EngineClass
            elif getattr(EngineClass, "is_" + operation_mode.value)():
                # The EngineClass satisfies the given OperationMode but does not
                # satisfy some other features; add it to the error report features if
                # no NoSuitableEngineAvailable are found.
                x = [name] + [
                    str(EngineClass.supports(ProblemKind({f})))
                    for f in problem_features
                ]
                planners_features.append(x)
        if len(planners_features) > 0:
            header = ["Engine"] + problem_features
            msg = f"No available engine supports all the problem features:\n{format_table(header, planners_features)}"
        elif compilation_kind is not None:
            msg = f"No available engine supports {compilation_kind}"
        elif plan_kind is not None:
            msg = f"No available engine supports {plan_kind}"
        elif optimality_guarantee is not None:
            msg = f"No available engine supports {optimality_guarantee}"
        elif anytime_guarantee is not None:
            msg = f"No available engine supports {anytime_guarantee}"
        else:
            msg = f"No available {operation_mode} engine"
        raise up.exceptions.UPNoSuitableEngineAvailableException(msg)

    def _print_credits(self, all_credits: Sequence[Optional["up.engines.Credits"]]):
        """
        This function prints the credits of the engine(s) used by an operation mode
        """
        credits: List["up.engines.Credits"] = [c for c in all_credits if c is not None]
        if len(credits) == 0:
            return

        stack = inspect.stack()
        fname = stack[3].filename
        if "unified_planning/shortcuts.py" in fname:
            fname = stack[4].filename
            operation_mode_name = stack[3].function
            line = stack[4].lineno
        else:
            operation_mode_name = stack[2].function
            line = stack[3].lineno

        class PaleWriter(up.AnyBaseClass):
            def __init__(self, stream: IO[str]):
                self._stream = stream

            def write(self, txt: str):
                self._stream.write("\033[96m")
                self._stream.write(txt)
                self._stream.write("\033[0m")

        if self.environment.credits_stream is not None:
            w = PaleWriter(self.environment.credits_stream)

            if not self._credit_disclaimer_printed:
                self._credit_disclaimer_printed = True
                w.write(
                    f"\033[1mNOTE: To disable printing of planning engine credits, add this line to your code: `up.shortcuts.get_environment().credits_stream = None`\n"
                )
            w.write("  *** Credits ***\n")
            w.write(
                f"  * In operation mode `{operation_mode_name}` at line {line} of `{fname}`, "
            )
            if len(credits) > 1:
                w.write(
                    "you are using a parallel planning engine with the following components:\n"
                )
            else:
                w.write("you are using the following planning engine:\n")
            for c in credits:
                c.write_credits(w)
            w.write("\n")

    def _get_engine(
        self,
        operation_mode: "OperationMode",
        name: Optional[str] = None,
        names: Optional[Sequence[str]] = None,
        params: Optional[Union[Dict[str, str], Sequence[Dict[str, str]]]] = None,
        problem_kind: ProblemKind = ProblemKind(),
        optimality_guarantee: Optional["OptimalityGuarantee"] = None,
        compilation_kind: Optional["CompilationKind"] = None,
        compilation_kinds: Optional[Sequence["CompilationKind"]] = None,
        plan_kind: Optional["PlanKind"] = None,
        anytime_guarantee: Optional["AnytimeGuarantee"] = None,
        problem: Optional["up.model.AbstractProblem"] = None,
    ) -> "up.engines.engine.Engine":
        if names is not None and operation_mode != OperationMode.COMPILER:
            assert name is None
            assert problem is None, "Parallel simulation is not supported"
            if params is None:
                params = [{} for _ in names]
            assert isinstance(params, List) and len(names) == len(params)
            engines = []
            all_credits = []
            for name, param in zip(names, params):
                EngineClass = self._get_engine_class(operation_mode, name)
                all_credits.append(EngineClass.get_credits(**param))
                engines.append((name, param))
            self._print_credits(all_credits)
            p_engine = up.engines.parallel.Parallel(self, engines)
            return p_engine
        elif operation_mode == OperationMode.COMPILER and compilation_kinds is not None:
            assert name is None
            assert names is not None or problem_kind is not None
            if names is None:
                names = [None for _ in compilation_kinds]  # type: ignore
            if params is None:
                params = [{} for _ in compilation_kinds]
            assert isinstance(params, List) and len(names) == len(params)
            compilers: List["up.engines.engine.Engine"] = []
            all_credits = []
            for name, param, compilation_kind in zip(names, params, compilation_kinds):
                EngineClass = self._get_engine_class(
                    operation_mode,
                    name,
                    problem_kind,
                    compilation_kind=compilation_kind,
                )
                assert issubclass(EngineClass, CompilerMixin)
                problem_kind = EngineClass.resulting_problem_kind(
                    problem_kind, compilation_kind
                )
                all_credits.append(EngineClass.get_credits(**param))
                compiler = EngineClass(**param)
                compiler.default = compilation_kind
                compilers.append(compiler)
            self._print_credits(all_credits)
            return up.engines.compilers.compilers_pipeline.CompilersPipeline(compilers)
        else:
            assert names is None
            error_failed_checks = name is None
            if params is None:
                params = {}
            assert isinstance(params, Dict)
            EngineClass = self._get_engine_class(
                operation_mode,
                name,
                problem_kind,
                optimality_guarantee,
                compilation_kind,
                plan_kind,
                anytime_guarantee,
            )
            credits = EngineClass.get_credits(**params)
            self._print_credits([credits])
            if operation_mode == OperationMode.REPLANNER:
                assert problem is not None
                if (
                    problem.kind.has_quality_metrics()
                    and optimality_guarantee == OptimalityGuarantee.SOLVED_OPTIMALLY
                ):
                    msg = f"The problem has no quality metrics but the engine is required to be optimal!"
                    raise up.exceptions.UPUsageError(msg)
                res = EngineClass(problem=problem, **params)
            elif operation_mode == OperationMode.SEQUENTIAL_SIMULATOR:
                assert problem is not None
                res = EngineClass(
                    problem=problem,
                    error_on_failed_checks=error_failed_checks,
                    **params,
                )
                assert isinstance(res, SequentialSimulatorMixin)
            elif operation_mode == OperationMode.COMPILER:
                res = EngineClass(**params)
                assert isinstance(res, CompilerMixin)
                if compilation_kind is not None:
                    res.default = compilation_kind
            elif (
                operation_mode == OperationMode.ONESHOT_PLANNER
                or operation_mode == OperationMode.PLAN_REPAIRER
                or operation_mode == OperationMode.PORTFOLIO_SELECTOR
            ):
                res = EngineClass(**params)
                assert (
                    isinstance(res, OneshotPlannerMixin)
                    or isinstance(res, PortfolioSelectorMixin)
                    or isinstance(res, PlanRepairerMixin)
                )
                if optimality_guarantee == OptimalityGuarantee.SOLVED_OPTIMALLY:
                    res.optimality_metric_required = True
            elif operation_mode == OperationMode.ANYTIME_PLANNER:
                res = EngineClass(**params)
                assert isinstance(res, AnytimePlannerMixin)
                if (
                    anytime_guarantee == AnytimeGuarantee.INCREASING_QUALITY
                    or anytime_guarantee == AnytimeGuarantee.OPTIMAL_PLANS
                ):
                    res.optimality_metric_required = True
            else:
                res = EngineClass(**params)
            res.error_on_failed_checks = error_failed_checks
            return res

    @property
    def environment(self) -> "Environment":
        """Returns the environment in which this factory is created"""
        return self._env

    def OneshotPlanner(
        self,
        *,
        name: Optional[str] = None,
        names: Optional[Sequence[str]] = None,
        params: Optional[Union[Dict[str, Any], Sequence[Dict[str, Any]]]] = None,
        problem_kind: ProblemKind = ProblemKind(),
        optimality_guarantee: Optional[Union["OptimalityGuarantee", str]] = None,
    ) -> "up.engines.engine.Engine":
        """
        Returns a oneshot planner. There are three ways to call this method:

        *   | using ``name`` (the name of a specific planner) and ``params`` (planner dependent options).
            | e.g. ``OneshotPlanner(name='tamer', params={'heuristic': 'hadd'})``
        *   | using ``names`` (list of specific planners name) and ``params`` (list of planner dependent options) to get a ``Parallel`` engine.
            | e.g. ``OneshotPlanner(names=['tamer', 'tamer'], params=[{'heuristic': 'hadd'}, {'heuristic': 'hmax'}])``
        *   | using ``problem_kind`` and ``optimality_guarantee``.
            | e.g. ``OneshotPlanner(problem_kind=problem.kind, optimality_guarantee=SOLVED_OPTIMALLY)``
        """
        if isinstance(optimality_guarantee, str):
            try:
                optimality_guarantee = OptimalityGuarantee[optimality_guarantee.upper()]
            except KeyError:
                raise UPUsageError(
                    f"{optimality_guarantee} is not a valid OptimalityGuarantee."
                )
        return self._get_engine(
            OperationMode.ONESHOT_PLANNER,
            name,
            names,
            params,
            problem_kind,
            optimality_guarantee,
        )

    def AnytimePlanner(
        self,
        *,
        name: Optional[str] = None,
        params: Optional[Dict[str, str]] = None,
        problem_kind: ProblemKind = ProblemKind(),
        anytime_guarantee: Optional[Union["AnytimeGuarantee", str]] = None,
    ) -> "up.engines.engine.Engine":
        """
        Returns a anytime planner. There are two ways to call this method:

        *   | using ``name`` (the name of a specific planner) and ``params`` (planner dependent options).
            | e.g. ``AnytimePlanner(name='tamer', params={'heuristic': 'hadd'})``
        *   | using ``problem_kind`` and ``anytime_guarantee``.
            | e.g. ``AnytimePlanner(problem_kind=problem.kind, anytime_guarantee=INCREASING_QUALITY)``

        An ``AnytimePlanner`` is a planner that returns an ``Iterator`` of solutions.
        Depending on the given ``anytime_guarantee`` parameter, every plan being generated is:

        * strictly better in terms of quality than the previous one (``INCREASING_QUALITY``);
        * optimal (``OPTIMAL_PLANS``);
        * just a different plan, with no specific guarantee (``None``).

        It raises an exception if the problem has no optimality metrics and anytime_guarantee
        is equal to ``INCREASING_QUALITY`` or ``OPTIMAL_PLAN``.
        """
        if isinstance(anytime_guarantee, str):
            try:
                anytime_guarantee = AnytimeGuarantee[anytime_guarantee.upper()]
            except KeyError:
                raise UPUsageError(
                    f"{anytime_guarantee} is not a valid AnytimeGuarantee."
                )
        return self._get_engine(
            OperationMode.ANYTIME_PLANNER,
            name,
            None,
            params,
            problem_kind,
            anytime_guarantee=anytime_guarantee,
        )

    def PlanValidator(
        self,
        *,
        name: Optional[str] = None,
        names: Optional[Sequence[str]] = None,
        params: Optional[Union[Dict[str, str], Sequence[Dict[str, str]]]] = None,
        problem_kind: ProblemKind = ProblemKind(),
        plan_kind: Optional[Union["PlanKind", str]] = None,
    ) -> "up.engines.engine.Engine":
        """
        Returns a plan validator. There are three ways to call this method:

        *   | using ``name`` (the name of a specific plan validator) and ``params`` (plan validator dependent options).
            | e.g. ``PlanValidator(name='tamer', params={'opt': 'val'})``
        *   | using ``names`` (list of specific plan validators name) and ``params`` (list of plan validators dependent options) to get a ``Parallel`` engine.
            | e.g. ``PlanValidator(names=['tamer', 'tamer'], params=[{'opt1': 'val1'}, {'opt2': 'val2'}])``
        *   | using ``problem_kind`` and ``plan_kind`` parameters.
            | e.g. ``PlanValidator(problem_kind=problem.kind, plan_kind=plan.kind)``
        """
        if isinstance(plan_kind, str):
            plan_kind = PlanKind[plan_kind]
        return self._get_engine(
            OperationMode.PLAN_VALIDATOR,
            name,
            names,
            params,
            problem_kind,
            plan_kind=plan_kind,
        )

    def Compiler(
        self,
        *,
        name: Optional[str] = None,
        names: Optional[Sequence[str]] = None,
        params: Optional[Union[Dict[str, str], Sequence[Dict[str, str]]]] = None,
        problem_kind: ProblemKind = ProblemKind(),
        compilation_kind: Optional[Union["CompilationKind", str]] = None,
        compilation_kinds: Optional[Sequence[Union["CompilationKind", str]]] = None,
    ) -> "up.engines.engine.Engine":
        """
        Returns a compiler or a pipeline of compilers.

        To get a compiler there are two ways to call this method:

        *   | using ``name`` (the name of a specific compiler) and ``params`` (compiler dependent options).
            | e.g. ``Compiler(name='tamer', params={'opt': 'val'})``
        *   | using ``problem_kind`` and ``compilation_kind`` parameters.
            | e.g. ``Compiler(problem_kind=problem.kind, compilation_kind=GROUNDING)``

        To get a pipeline of compilers there are two ways to call this method:

        *   | using ``names`` (the names of the specific compilers), ``params`` (compilers dependent options) and ``compilation_kinds``.
            | e.g. ``Compiler(names=['up_quantifiers_remover', 'up_grounder'], params=[{'opt1': 'val1'}, {'opt2': 'val2'}], compilation_kinds=[QUANTIFIERS_REMOVING, GROUNDING])``
        *   | using ``problem_kind`` and ``compilation_kinds`` parameters.
            | e.g. ``Compiler(problem_kind=problem.kind, compilation_kinds=[QUANTIFIERS_REMOVING, GROUNDING])``
        """
        if isinstance(compilation_kind, str):
            try:
                compilation_kind = CompilationKind[compilation_kind.upper()]
            except KeyError:
                raise UPUsageError(
                    f"{compilation_kind} is not a valid CompilationKind."
                )
        kinds: Optional[List[CompilationKind]] = None
        if compilation_kinds is not None:
            kinds = []
            for kind in compilation_kinds:
                if isinstance(kind, str):
                    try:
                        kinds.append(CompilationKind[kind.upper()])
                    except KeyError:
                        raise UPUsageError(f"{kind} is not a valid CompilationKind.")
                else:
                    assert isinstance(kind, CompilationKind), "Typing not respected"
                    kinds.append(kind)
        return self._get_engine(
            OperationMode.COMPILER,
            name,
            names,
            params,
            problem_kind,
            compilation_kind=compilation_kind,
            compilation_kinds=kinds,
        )

    def SequentialSimulator(
        self,
        problem: "up.model.AbstractProblem",
        *,
        name: Optional[str] = None,
        params: Optional[Dict[str, str]] = None,
    ) -> "up.engines.engine.Engine":
        """
        Returns a sequential simulator. There are two ways to call this method:

        *   | using ``problem_kind`` through the problem field.
            | e.g. ``SequentialSimulator(problem)``
        *   | using ``name`` (the name of a specific simulator) and eventually some ``params`` (simulator dependent options).
            | e.g. ``SequentialSimulator(problem, name='sequential_simulator')``
        """
        return self._get_engine(
            OperationMode.SEQUENTIAL_SIMULATOR,
            name,
            None,
            params,
            problem.kind,
            problem=problem,
        )

    def Replanner(
        self,
        problem: "up.model.AbstractProblem",
        *,
        name: Optional[str] = None,
        params: Optional[Dict[str, str]] = None,
        optimality_guarantee: Optional[Union["OptimalityGuarantee", str]] = None,
    ) -> "up.engines.engine.Engine":
        """
        Returns a Replanner. There are two ways to call this method:

        *   | using ``problem`` (with its kind) and ``optimality_guarantee`` parameters.
            | e.g. ``Replanner(problem, optimality_guarantee=SOLVED_OPTIMALLY)``
        *   | using ``name`` (the name of a specific replanner) and ``params`` (replanner dependent options).
            | e.g. ``Replanner(problem, name='replanner[tamer]')``
        """
        if isinstance(optimality_guarantee, str):
            try:
                optimality_guarantee = OptimalityGuarantee[optimality_guarantee.upper()]
            except KeyError:
                raise UPUsageError(
                    f"{optimality_guarantee} is not a valid OptimalityGuarantee."
                )
        return self._get_engine(
            OperationMode.REPLANNER,
            name,
            None,
            params,
            problem.kind,
            optimality_guarantee,
            problem=problem,
        )

    def PlanRepairer(
        self,
        *,
        name: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        problem_kind: ProblemKind = ProblemKind(),
        plan_kind: Optional[Union["PlanKind", str]] = None,
        optimality_guarantee: Optional[Union["OptimalityGuarantee", str]] = None,
    ) -> "up.engines.engine.Engine":
        """
        Returns a plan repairer. There are two ways to call this method:

        *   | using ``name`` (the name of a plan repairer) and eventually ``params``.
            | e.g. ``PlanRepairer(name='xxx')``
        *   | using ``problem_kind``, ``plan_kind`` and ``optimality_guarantee``.
            | e.g. ``PlanRepairer(problem_kind=problem.kind, plan_kind=plan.kind, optimality_guarantee=SOLVED_OPTIMALLY)``
        """
        if isinstance(plan_kind, str):
            try:
                plan_kind = PlanKind[plan_kind.upper()]
            except KeyError:
                raise UPUsageError(f"{plan_kind} is not a valid PlanKind.")
        if isinstance(optimality_guarantee, str):
            try:
                optimality_guarantee = OptimalityGuarantee[optimality_guarantee.upper()]
            except KeyError:
                raise UPUsageError(
                    f"{optimality_guarantee} is not a valid OptimalityGuarantee."
                )
        return self._get_engine(
            OperationMode.PLAN_REPAIRER,
            name=name,
            params=params,
            problem_kind=problem_kind,
            plan_kind=plan_kind,
            optimality_guarantee=optimality_guarantee,
        )

    def PortfolioSelector(
        self,
        *,
        name: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        problem_kind: ProblemKind = ProblemKind(),
        optimality_guarantee: Optional[Union["OptimalityGuarantee", str]] = None,
    ) -> "up.engines.engine.Engine":
        """
        Returns a portfolio selector. There are two ways to call this method:

        *   | using ``name`` (the name of a specific portfolio) and eventually ``params`` (portfolio dependent options).
            | e.g. ``PortfolioSelector(name='ibacop')``
        *   | using ``problem_kind`` and ``optimality_guarantee``.
            | e.g. ``PortfolioSelector(problem_kind=problem.kind, optimality_guarantee=SOLVED_OPTIMALLY)``
        """
        if isinstance(optimality_guarantee, str):
            try:
                optimality_guarantee = OptimalityGuarantee[optimality_guarantee.upper()]
            except KeyError:
                raise UPUsageError(
                    f"{optimality_guarantee} is not a valid OptimalityGuarantee."
                )
        return self._get_engine(
            OperationMode.PORTFOLIO_SELECTOR,
            name=name,
            params=params,
            problem_kind=problem_kind,
            optimality_guarantee=optimality_guarantee,
        )

    def print_engines_info(
        self,
        stream: IO[str] = sys.stdout,
        *,
        operation_mode: Optional[Union[OperationMode, str]] = None,
        show_supported_kind: bool = True,
        show_credits: bool = False,
        full_credits: bool = True,
    ):
        """
        Writes the info of all the installed engines in the given stream; the
        default stream is the stdout.

        :param stream: The ``IO[str]`` where all the engine's info are written;
            defaults to sys.stdout.
        :param operation_mode: If specified, writes info about the engines that support
            that OperationMode.
        :param show_supported_kind: If ``True`` writes the supported_kind of the engines.
            defaults to ``True``.
        :param show_credits: If ``True`` writes the credits of the engines.
            defaults to ``False``.
        :param full_credits: If ``True`` writes a longer version of the credits; ignored
            if ``show_credits`` is ``False``; defaults to ``True``.
        """
        stream.write("These are the engines currently available:\n")
        if isinstance(operation_mode, str):
            try:
                operation_mode = OperationMode[operation_mode.upper()]
            except KeyError:
                raise UPUsageError(f"{operation_mode} is not a valid OperationMode.")
        for engine_name, Engine in self._engines.items():
            if (
                operation_mode is not None
                and not getattr(Engine, "is_" + operation_mode.value)()
            ):
                continue
            credits = Engine.get_credits() if show_credits else None
            engine_name_str = f"Engine's factory name: {engine_name}\n\n"
            stream.write("-" * (len(engine_name_str) - 2))
            stream.write("\n")
            stream.write(engine_name_str)
            if credits is not None:
                credits.write_credits(stream, full_credits)
            supported_operation_modes = [
                om.value for om in OperationMode if getattr(Engine, "is_" + om.value)()
            ]
            stream.write("Supported operation modes:\n    - ")
            stream.write("\n    - ".join(supported_operation_modes))
            stream.write("\n")
            if show_supported_kind:
                stream.write(
                    f"\nThis engine supports the following features:\n{str(Engine.supported_kind())}\n"
                )
            stream.write("\n")

    def get_all_applicable_engines(
        self,
        problem_kind: ProblemKind,
        operation_mode: OperationMode = OperationMode.ONESHOT_PLANNER,
        *,
        optimality_guarantee: Optional[Union["OptimalityGuarantee", str]] = None,
        anytime_guarantee: Optional[Union["AnytimeGuarantee", str]] = None,
        plan_kind: Optional[Union["PlanKind", str]] = None,
        compilation_kind: Optional[Union["CompilationKind", str]] = None,
    ) -> List[str]:
        """
        | Returns all the engine names installed that are able to handle all the given
          requirements.

        | Since the semantic of the parameters given to this function depends on the chosen ``OperationMode``,
          an user must have clear their meaning in the Operation Mode context.

        :param problem_kind: An engine is returned only if it supports this ``problem_kind``.
        :param operation_mode: An engine is returned only if it implements this ``operation_mode``; defaults to ``ONESHOT_PLANNER``.
        :param optimality_guarantee: An engine is returned only if it satisfies this ``optimality_guarantee``. This parameter
            can be specified only if the ``operation_mode`` is ``ONESHOT_PLANNER``, ``REPLANNER``, ``PLAN_REPAIRER``
            or ``PORTFOLIO_SELECTOR``.
        :param anytime_guarantee: An engine is returned only if it satisfies this ``anytime_guarantee``. This parameter
            can be specified only if the ``operation_mode`` is ``ANYTIME_PLANNER``.
        :param plan_kind: An engine is returned only if it is able to handle this ``plan_kind``. This parameter
            can be specified only if the ``operation_mode`` is ``PLAN_VALIDATOR`` or ``PLAN_REPAIRER``.
        :param compilation_kind: An engine is returned only if it is able to handle this ``compilation_kind``. This
            parameter can be specified only if the ``operation_mode`` is ``COMPILER``.
        :return: The list of engines names that satisfy all the given requirements.
        """
        if isinstance(optimality_guarantee, str):
            try:
                optimality_guarantee = OptimalityGuarantee[optimality_guarantee.upper()]
            except KeyError:
                raise UPUsageError(
                    f"{optimality_guarantee} is not a valid OptimalityGuarantee."
                )
        if isinstance(anytime_guarantee, str):
            try:
                anytime_guarantee = AnytimeGuarantee[anytime_guarantee.upper()]
            except KeyError:
                raise UPUsageError(
                    f"{anytime_guarantee} is not a valid AnytimeGuarantee."
                )
        if isinstance(compilation_kind, str):
            try:
                compilation_kind = CompilationKind[compilation_kind.upper()]
            except KeyError:
                raise UPUsageError(
                    f"{compilation_kind} is not a valid CompilationKind."
                )
        if isinstance(plan_kind, str):
            try:
                plan_kind = PlanKind[plan_kind.upper()]
            except KeyError:
                raise UPUsageError(f"{plan_kind} is not a valid PlanKind.")
        names: List[str] = []
        for name in self._preference_list:
            EngineClass = self._engines[name]
            if self._engine_satisfies_conditions(
                EngineClass,
                operation_mode,
                problem_kind,
                cast(Optional[OptimalityGuarantee], optimality_guarantee),
                cast(Optional[CompilationKind], compilation_kind),
                plan_kind,
                cast(Optional[AnytimeGuarantee], anytime_guarantee),
            ):
                names.append(name)
        return names
