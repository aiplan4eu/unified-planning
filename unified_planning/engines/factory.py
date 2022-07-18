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


import importlib
import sys
import os
import inspect
import configparser
import unified_planning as up
from unified_planning.environment import Environment
from unified_planning.model import ProblemKind
from unified_planning.plans import PlanKind
from unified_planning.engines.mixins.oneshot_planner import OptimalityGuarantee
from unified_planning.engines.mixins.compiler import CompilationKind, CompilerMixin
from unified_planning.engines.mixins.oneshot_planner import OneshotPlannerMixin
from unified_planning.engines.mixins.plan_validator import PlanValidatorMixin
from unified_planning.engines.mixins.replanner import ReplannerMixin
from unified_planning.engines.mixins.simulator import SimulatorMixin
from typing import IO, Dict, Tuple, Optional, List, Union, Type, cast
from pathlib import PurePath


DEFAULT_ENGINES = {
    "fast-downward": ("up_fast_downward", "FastDownwardPDDLPlanner"),
    "fast-downward-opt": ("up_fast_downward", "FastDownwardOptimalPDDLPlanner"),
    "pyperplan": ("up_pyperplan.engine", "EngineImpl"),
    "enhsp": ("up_enhsp.enhsp_planner", "ENHSPSatEngine"),
    "enhsp-opt": ("up_enhsp.enhsp_planner", "ENHSPOptEngine"),
    "tamer": ("up_tamer.engine", "EngineImpl"),
    "sequential_plan_validator": (
        "unified_planning.engines.plan_validator",
        "SequentialPlanValidator",
    ),
    "sequential_simulator": (
        "unified_planning.engines.sequential_simulator",
        "SequentialSimulator",
    ),
    "up_conditional_effects_remover": (
        "unified_planning.engines.compilers.conditional_effects_remover",
        "ConditionalEffectsRemover",
    ),
    "up_disjunctive_conditions_remover": (
        "unified_planning.engines.compilers.disjunctive_conditions_remover",
        "DisjunctiveConditionsRemover",
    ),
    "up_negative_conditions_remover": (
        "unified_planning.engines.compilers.negative_conditions_remover",
        "NegativeConditionsRemover",
    ),
    "up_quantifiers_remover": (
        "unified_planning.engines.compilers.quantifiers_remover",
        "QuantifiersRemover",
    ),
    "tarski_grounder": (
        "unified_planning.engines.compilers.tarski_grounder",
        "TarskiGrounder",
    ),
    "up_grounder": ("unified_planning.engines.compilers.grounder", "Grounder"),
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
    "pyperplan",
    "enhsp",
    "enhsp-opt",
    "tamer",
    "sequential_plan_validator",
    "sequential_simulator",
    "up_conditional_effects_remover",
    "up_disjunctive_conditions_remover",
    "up_negative_conditions_remover",
    "up_quantifiers_remover",
    "tarski_grounder",
    "up_grounder",
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
    def __init__(self, env: "Environment"):
        self._env = env
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
        return list(self._engines.keys())

    def engine(self, name: str) -> Type["up.engines.engine.Engine"]:
        return self._engines[name]

    @property
    def preference_list(self) -> List[str]:
        return self._preference_list

    @preference_list.setter
    def preference_list(self, preference_list: List[str]):
        """Defines the order in which to pick the engines.
        The list is not required to contain all the engines. It is
        possible to define a subsets of the engines, or even just
        one. The impact of this, is that the engine will never be
        selected automatically. Note, however, that the engine can
        still be selected by calling it by name.
        """
        self._preference_list = preference_list

    def add_engine(self, name: str, module_name: str, class_name: str):
        self._add_engine(name, module_name, class_name)
        self._preference_list.append(name)
        engine = self._engines[name]
        for me_name, me in self._meta_engines.items():
            if me.is_compatible_engine(engine):
                n = f"{me_name}[{name}]"
                self._engines[n] = me[engine]
                self._preference_list.append(n)

    def add_meta_engine(self, name: str, module_name: str, class_name: str):
        for engine_name, engine in self._engines.items():
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

    def _get_engine_class(
        self,
        engine_kind: str,
        name: Optional[str] = None,
        problem_kind: ProblemKind = ProblemKind(),
        optimality_guarantee: Optional["OptimalityGuarantee"] = None,
        compilation_kind: Optional["CompilationKind"] = None,
        plan_kind: Optional["PlanKind"] = None,
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
            if getattr(EngineClass, "is_" + engine_kind)():
                assert (
                    optimality_guarantee is None
                    or issubclass(EngineClass, OneshotPlannerMixin)
                    or issubclass(EngineClass, ReplannerMixin)
                )
                assert compilation_kind is None or issubclass(
                    EngineClass, CompilerMixin
                )
                assert plan_kind is None or issubclass(EngineClass, PlanValidatorMixin)
                if (
                    EngineClass.supports(problem_kind)
                    and (
                        optimality_guarantee is None
                        or EngineClass.satisfies(optimality_guarantee)  # type: ignore
                    )
                    and (
                        compilation_kind is None
                        or cast(CompilerMixin, EngineClass).supports_compilation(
                            compilation_kind
                        )
                    )
                    and (
                        plan_kind is None
                        or cast(PlanValidatorMixin, EngineClass).supports_plan(
                            plan_kind
                        )
                    )
                ):
                    return EngineClass
                elif (
                    compilation_kind is None
                    or cast(CompilerMixin, EngineClass).supports_compilation(
                        compilation_kind
                    )
                ) and (
                    plan_kind is None
                    or cast(PlanValidatorMixin, EngineClass).supports_plan(plan_kind)
                ):
                    x = [name] + [
                        str(EngineClass.supports(ProblemKind({f})))
                        for f in problem_features
                    ]
                    if optimality_guarantee is not None:
                        assert issubclass(
                            EngineClass, OneshotPlannerMixin
                        ) or issubclass(EngineClass, ReplannerMixin)
                        x.append(str(EngineClass.satisfies(optimality_guarantee)))
                    planners_features.append(x)
        if len(planners_features) > 0:
            header = ["Engine"] + problem_features
            if optimality_guarantee is not None:
                header.append("OPTIMALITY_GUARANTEE")
            msg = f"No available engine supports all the problem features:\n{format_table(header, planners_features)}"
        elif compilation_kind is not None:
            msg = f"No available engine supports {compilation_kind}"
        elif plan_kind is not None:
            msg = f"No available engine supports {plan_kind}"
        else:
            msg = f"No available {engine_kind} engine"
        raise up.exceptions.UPNoSuitableEngineAvailableException(msg)

    def _print_credits(self, all_credits: List[Optional["up.engines.Credits"]]):
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
                    f"\033[1mNOTE: To disable printing of planning engine credits, add this line to your code: `up.shortcuts.get_env().credits_stream = None`\n"
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
        engine_kind: str,
        name: Optional[str] = None,
        names: Optional[List[str]] = None,
        params: Union[Dict[str, str], List[Dict[str, str]]] = None,
        problem_kind: ProblemKind = ProblemKind(),
        optimality_guarantee: Optional["OptimalityGuarantee"] = None,
        compilation_kind: Optional["CompilationKind"] = None,
        plan_kind: Optional["PlanKind"] = None,
        problem: Optional["up.model.AbstractProblem"] = None,
    ) -> "up.engines.engine.Engine":
        if names is not None:
            assert name is None
            assert problem is None, "Parallel simulation is not supported"
            if params is None:
                params = [{} for i in range(len(names))]
            assert isinstance(params, List) and len(names) == len(params)
            engines = []
            all_credits = []
            for name, param in zip(names, params):
                EngineClass = self._get_engine_class(engine_kind, name)
                all_credits.append(EngineClass.get_credits(**param))
                engines.append((name, param))
            self._print_credits(all_credits)
            p_engine = up.engines.parallel.Parallel(self, engines)
            return p_engine
        else:
            if params is None:
                params = {}
            assert isinstance(params, Dict)
            EngineClass = self._get_engine_class(
                engine_kind,
                name,
                problem_kind,
                optimality_guarantee,
                compilation_kind,
                plan_kind,
            )
            credits = EngineClass.get_credits(**params)
            self._print_credits([credits])
            if problem is None:
                assert engine_kind not in ["simulator", "replanner"]
                res = EngineClass(**params)
            else:
                assert engine_kind in ["simulator", "replanner"]
                assert issubclass(EngineClass, up.engines.engine.Engine)
                assert issubclass(EngineClass, SimulatorMixin) or issubclass(
                    EngineClass, ReplannerMixin
                )
                res = EngineClass(problem=problem, **params)
            if name is not None:
                res.error_on_failed_checks = False
            return res

    @property
    def environment(self) -> "Environment":
        """Returns the environment in which this factory is created"""
        return self._env

    def OneshotPlanner(
        self,
        *,
        name: Optional[str] = None,
        names: Optional[List[str]] = None,
        params: Union[Dict[str, str], List[Dict[str, str]]] = None,
        problem_kind: ProblemKind = ProblemKind(),
        optimality_guarantee: Optional[Union["OptimalityGuarantee", str]] = None,
    ) -> "up.engines.engine.Engine":
        """
        Returns a oneshot planner. There are three ways to call this method:
        - using 'name' (the name of a specific planner) and 'params' (planner dependent options).
          e.g. OneshotPlanner(name='tamer', params={'heuristic': 'hadd'})
        - using 'names' (list of specific planners name) and 'params' (list of
          planners dependent options) to get a Parallel engine.
          e.g. OneshotPlanner(names=['tamer', 'tamer'],
                              params=[{'heuristic': 'hadd'}, {'heuristic': 'hmax'}])
        - using 'problem_kind' and 'optimality_guarantee'.
          e.g. OneshotPlanner(problem_kind=problem.kind, optimality_guarantee=SOLVED_OPTIMALLY)
        """
        if isinstance(optimality_guarantee, str):
            optimality_guarantee = OptimalityGuarantee[optimality_guarantee]
        return self._get_engine(
            "oneshot_planner", name, names, params, problem_kind, optimality_guarantee
        )

    def PlanValidator(
        self,
        *,
        name: Optional[str] = None,
        names: Optional[List[str]] = None,
        params: Union[Dict[str, str], List[Dict[str, str]]] = None,
        problem_kind: ProblemKind = ProblemKind(),
        plan_kind: Optional[Union["PlanKind", str]] = None,
    ) -> "up.engines.engine.Engine":
        """
        Returns a plan validator. There are three ways to call this method:
        - using 'name' (the name of a specific plan validator) and 'params'
          (plan validator dependent options).
          e.g. PlanValidator(name='tamer', params={'opt': 'val'})
        - using 'names' (list of specific plan validators name) and 'params' (list of
          plan validators dependent options) to get a Parallel engine.
          e.g. PlanValidator(names=['tamer', 'tamer'],
                             params=[{'opt1': 'val1'}, {'opt2': 'val2'}])
        - using 'problem_kind' and 'plan_kind' parameters.
          e.g. PlanValidator(problem_kind=problem.kind, plan_kind=plan.kind)
        """
        if isinstance(plan_kind, str):
            plan_kind = PlanKind[plan_kind]
        return self._get_engine(
            "plan_validator", name, names, params, problem_kind, plan_kind=plan_kind
        )

    def Compiler(
        self,
        *,
        name: Optional[str] = None,
        params: Union[Dict[str, str], List[Dict[str, str]]] = None,
        problem_kind: ProblemKind = ProblemKind(),
        compilation_kind: Optional[Union["CompilationKind", str]] = None,
    ) -> "up.engines.engine.Engine":
        """
        Returns a Compiler. There are two ways to call this method:
        - using 'name' (the name of a specific grounder) and 'params'
          (grounder dependent options).
          e.g. Compiler(name='tamer', params={'opt': 'val'})
        - using 'problem_kind' and 'compilation_kind' parameters.
          e.g. Compiler(problem_kind=problem.kind, compilation_kind=GROUNDER)
        """
        if isinstance(compilation_kind, str):
            compilation_kind = CompilationKind[compilation_kind]
        return self._get_engine(
            "compiler",
            name,
            None,
            params,
            problem_kind,
            compilation_kind=compilation_kind,
        )

    def Simulator(
        self,
        problem: "up.model.AbstractProblem",
        *,
        name: Optional[str] = None,
        params: Union[Dict[str, str], List[Dict[str, str]]] = None,
    ) -> "up.engines.engine.Engine":
        """
        Returns a Simulator. There are two ways to call this method:
        - using 'problem_kind' through the problem field.
          e.g. Simulator(problem)
        - using 'name' (the name of a specific simulator) and eventually some 'params'
          (simulator dependent options).
          e.g. Simulator(problem, name='sequential_simulator')
        """
        return self._get_engine(
            "simulator", name, None, params, problem.kind, problem=problem
        )

    def Replanner(
        self,
        problem: "up.model.AbstractProblem",
        *,
        name: Optional[str] = None,
        params: Union[Dict[str, str], List[Dict[str, str]]] = None,
        optimality_guarantee: Optional[Union["OptimalityGuarantee", str]] = None,
    ) -> "up.engines.engine.Engine":
        """
        Returns a Replanner. There are two ways to call this method:
        - using 'problem' (with its kind) and 'optimality_guarantee' parameters.
          e.g. Replanner(problem, optimality_guarantee=SOLVED_OPTIMALLY)
        - using 'name' (the name of a specific replanner) and 'params'
          (replanner dependent options).
          e.g. Replanner(problem, name='replanner[tamer]')
        """
        if isinstance(optimality_guarantee, str):
            optimality_guarantee = OptimalityGuarantee[optimality_guarantee]
        return self._get_engine(
            "replanner",
            name,
            None,
            params,
            problem.kind,
            optimality_guarantee,
            problem=problem,
        )

    def print_engines_info(
        self, stream: IO[str] = sys.stdout, full_credits: bool = True
    ):
        stream.write("These are the engines currently available:\n")
        for Engine in self._engines.values():
            credits = Engine.get_credits()
            if credits is not None:
                stream.write("---------------------------------------\n")
                credits.write_credits(stream, full_credits)
                stream.write(
                    f"This engine supports the following features:\n{str(Engine.supported_kind())}\n\n"
                )
