from typing import Callable, IO, Optional
import unified_planning as up
from unified_planning.engines.results import CompilerResult
from unified_planning.engines import PlanGenerationResultStatus, PlanGenerationResult

from pypmt.apis import valid_configs, generate_schedule_for, compile, initialize_fluents

# We have to args: linear, upper_bound
class SMTPlanner(up.engines.Engine, up.engines.mixins.OneshotPlannerMixin):
    def __init__(self, **options):
        # Read known user-options and store them for using in the `solve` method
        up.engines.Engine.__init__(self)
        up.engines.mixins.OneshotPlannerMixin.__init__(self)

        # Get the planner configuration.
        self.configuration = options.get('configuration', None)
        if self.configuration is None:
            # This means that we need to check the validity of the configuration.
            self.encoder  = eval(options.get('encoder', 'None'))
            self.search_strategy = eval(options.get('search-strategy', 'None'))

            assert self.encoder is not None, "Encoder is not defined."
            assert self.search_strategy is not None, "Search strategy is not defined."

            # Check if this is a valid configuration.
            for (_encoder, _search, _compilationlist) in valid_configs.values():
                if _encoder == self.encoder and _search == self.search_strategy:
                    self.configuration = (_encoder, _search, _compilationlist)
                    break
        else:
            self.configuration = valid_configs[self.configuration]
        
        assert self.configuration is not None, "Invalid configuration pass."

        # override the compilationlist if it is passed in the options
        compilationlist = options.get('compilationlist', None)
        if compilationlist is not None:
            self.configuration = (self.configuration[0], self.configuration[1], compilationlist)

        # Construct the shcedule.
        self.upper_bound = options.get('upper-bound', None)
        assert self.upper_bound is not None, "Upper bound is not defined."
        
        self.schedule = generate_schedule_for(self.configuration[0], self.upper_bound)
        self.run_validation = options.get('run-validation', False)

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
    
        # 1. initialise the fluents
        initialize_fluents(problem)
        # 2. compile the problem
        compiled_tasks = compile(problem, self.configuration[2])
        arg_task = compiled_tasks[-1].problem if isinstance(compiled_tasks[-1], CompilerResult) else compiled_tasks[-1]
        # 3. create the encoder instance
        encoder_instance = self.configuration[0](arg_task)
        search_strategy  = self.configuration[1]
        # 4. search for the plan
        plan = search_strategy(encoder_instance, self.schedule, run_validation=self.run_validation).search()
        # 5. return the result
        if not plan.validate():
            return PlanGenerationResult(PlanGenerationResultStatus.UNSOLVABLE_INCOMPLETELY, None, self.name, log_messages=[f'failure reason {plan.validation_fail_reason}'])
        # 6. lift the plan
        up_seq_plan = plan.plan
        for compilation_r in reversed(compiled_tasks[1:]):
            up_seq_plan = up_seq_plan.replace_action_instances(compilation_r.map_back_action_instance)
        plan.plan = up_seq_plan
        return PlanGenerationResult(PlanGenerationResultStatus.SOLVED_SATISFICING, plan.plan, self.name)

    def destroy(self):
        pass