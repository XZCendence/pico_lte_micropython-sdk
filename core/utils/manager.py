"""
Module for managing processes on modem step by step.
"""

from core.temp import config
from core.utils.status import Status

class Step:
    """Data class for storing step data"""

    is_ok = False
    final_step = False
    def __init__(
        self, name, function, success, fail,
            function_params=None, desired_response=None,
            interval=0, retry=0, final_step=False, cachable=False
        ):
        self.function = function
        self.name = name
        self.success = success
        self.fail = fail
        self.interval = interval
        self.retry = retry
        self.function_params = function_params
        self.final_step = final_step
        self.desired_response = desired_response
        self.cachable = cachable

class StateManager:
    """Class for managing states"""

    NO_WAIT_INTERVAL = 0
    cache_available = False
    retry_counter = 0
    steps = {}
    cache = config["cache"]

    def __init__(self, first_step, function_name=None):
        """Initializes state manager"""
        self.first_step = first_step
        self.function_name = function_name

        if function_name and self.cache.states.get(function_name):
            self.cache_available = True
            self.cache.add_cache(function_name)

        self.organizer_step = Step(
            function=self.organizer,
            name="organizer", success="organizer", fail="organizer",
            function_params=None, interval=0, retry=0
        )

        self.success_step = Step(
            function=self.success,
            name="success", success="success", fail="success",
            function_params=None, interval=0, retry=0, final_step=True
        )

        self.failure_step = Step(
            function=self.failure,
            name="failure", success="failure", fail="failure",
            function_params=None, interval=0, retry=0, final_step=True
        )

        self.current = self.organizer_step

        # Add default steps to steps dictionary
        self.add_step(self.organizer_step)
        self.add_step(self.success_step)
        self.add_step(self.failure_step)

    def add_step(self, step):
        """Adds step to steps dictionary"""
        self.steps[step.name] = step

    def get_step(self, name):
        """Returns step with name"""
        return self.steps[name]

    def clear_counter(self):
        """Clears retry counter"""
        self.retry_counter = 0

    def counter_tick(self):
        """Increments retry counter"""
        self.retry_counter += 1

    def organizer(self):
        """Organizer step function"""
        if self.current.name == "organizer":
            self.current = self.first_step
            print("CACHE AVAILABLE:", self.cache_available)
            print("FUNC:", self.function_name)
            # assign cache step as current if specific cache is exists
            if self.cache_available:
                if self.function_name in self.cache.states:
                    self.current = self.get_step(self.cache.states[self.function_name])
                    print("CURRENT: ", self.current)
        else:
            if self.current.is_ok: # step succieded
                if self.current.cachable: # Assign new cache if step cachable
                    self.cache.set_state(self.function_name, self.current.name)

                self.current.is_ok = False
                self.current = self.get_step(self.current.success)
            else:
                if self.retry_counter >= self.current.retry:
                    # step failed and retry counter is exceeded

                    if self.cache_available:
                        if self.current.name == self.cache.states[self.function_name]:
                            # step failed and current step is cache step
                            # go to first step and clear function spesific cache
                            self.current = self.first_step
                            self.cache.set_state(self.function_name, None)
                    else:
                        self.current = self.get_step(self.current.fail)

                    self.clear_counter()
                    self.current.interval = self.NO_WAIT_INTERVAL
                else:
                    # step failed and retry counter is not exceeded, retrying...
                    self.current = self.get_step(self.current.name)
                    self.counter_tick()
        return {"status" : Status.SUCCESS}

    def success(self):
        """Success step function"""
        return {"status": Status.SUCCESS, "interval": self.NO_WAIT_INTERVAL}

    def failure(self):
        """Fail step function"""
        return {"status": Status.ERROR, "interval": self.NO_WAIT_INTERVAL}

    def execute_organizer_step(self):
        """Executes organizer step"""
        self.organizer()

    def execute_current_step(self):
        """Executes current step"""
        params = self.current.function_params

        if params:
            result = self.current.function(**params)
        else:
            result = self.current.function()

        print(result)

        if self.current.desired_response:
            if result["status"] == Status.SUCCESS and \
                    self.current.desired_response in result["value"]:
                self.current.is_ok = True
            else:
                self.current.is_ok = False
        else:
            if result["status"] == Status.SUCCESS:
                self.current.is_ok = True
            else:
                self.current.is_ok = False

    def run(self, begin=None, end=None):
        """Runs state manager"""
        result={}
        if begin:
            self.current = self.get_step(begin)

        self.execute_organizer_step()
        self.execute_current_step()

        if end:
            if self.current.name == self.get_step(end).name:
                self.current.final_step = True

        if not self.current.final_step:
            result["status"] = Status.ONGOING
            result["interval"] = self.current.interval
            return result
        else:
            if self.current.name == "success":
                result["status"] = Status.SUCCESS
            elif self.current.name == "failure":
                result["status"] = Status.ERROR

            result["interval"] = self.NO_WAIT_INTERVAL
            return result
