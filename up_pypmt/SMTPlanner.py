from typing import Callable, IO, Optional
import unified_planning as up
from unified_planning.engines.results import CompilerResult
from unified_planning.engines import PlanGenerationResultStatus, PlanGenerationResult
from pypmt.config import Config
from pypmt.pypmtcli import process_arguments
import argparse
from pypmt.apis import solveUP



# We have to args: linear, upper_bound
class SMTPlanner(up.engines.Engine, up.engines.mixins.OneshotPlannerMixin):
    def __init__(self, **options):
        # Read known user-options and store them for using in the `solve` method
        up.engines.Engine.__init__(self)
        up.engines.mixins.OneshotPlannerMixin.__init__(self)
        assert "configuration" in options, "Configuration is not defined."
        self.conf = Config(options["configuration"])

    @property
    def name(self) -> str:
        return "SMTPlanner"

    # TODO: We need to revist this.
    @staticmethod
    def supported_kind():
        # For this demo we limit ourselves to numeric planning.
        # Other kinds of problems can be modeled in the UP library,
        # see unified_planning.model.problem_kind.
        supported_kind = up.model.ProblemKind()
        supported_kind.set_problem_class("ACTION_BASED")
        supported_kind.set_problem_type("GENERAL_NUMERIC_PLANNING")
        supported_kind.set_typing('FLAT_TYPING')
        supported_kind.set_typing('HIERARCHICAL_TYPING')
        supported_kind.set_numbers('CONTINUOUS_NUMBERS')
        supported_kind.set_numbers('DISCRETE_NUMBERS')
        supported_kind.set_fluents_type('NUMERIC_FLUENTS')
        supported_kind.set_numbers('BOUNDED_TYPES')
        supported_kind.set_fluents_type('OBJECT_FLUENTS')
        supported_kind.set_conditions_kind('NEGATIVE_CONDITIONS')
        supported_kind.set_conditions_kind('DISJUNCTIVE_CONDITIONS')
        supported_kind.set_conditions_kind('EQUALITIES')
        supported_kind.set_conditions_kind('EXISTENTIAL_CONDITIONS')
        supported_kind.set_conditions_kind('UNIVERSAL_CONDITIONS')
        supported_kind.set_effects_kind('CONDITIONAL_EFFECTS')
        supported_kind.set_effects_kind('INCREASE_EFFECTS')
        supported_kind.set_effects_kind('DECREASE_EFFECTS')
        supported_kind.set_effects_kind('FLUENTS_IN_NUMERIC_ASSIGNMENTS')

        return supported_kind

    @staticmethod
    def supports(problem_kind):
        return problem_kind <= SMTPlanner.supported_kind()

    def _solve(self, problem: 'up.model.Problem',
              callback: Optional[Callable[['up.engines.PlanGenerationResult'], None]] = None,
              timeout: Optional[float] = None,
              output_stream: Optional[IO[str]] = None) -> 'up.engines.PlanGenerationResult':
        plan = solveUP(problem, self.conf)
        if plan is None or not plan.validate():
            return PlanGenerationResult(PlanGenerationResultStatus.UNSOLVABLE_INCOMPLETELY, None, self.name, log_messages=[f'failure reason {plan.validation_fail_reason}'])
        return PlanGenerationResult(PlanGenerationResultStatus.SOLVED_SATISFICING, plan.plan, self.name)

    def destroy(self):
        pass