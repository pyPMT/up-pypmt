import unified_planning as up
from up_pypmt.SMTPlanner import SMTPlanner

# Register planner to UP framework
env = up.environment.get_environment()
env.factory.add_engine('SMTPlanner', __name__, 'SMTPlanner')
