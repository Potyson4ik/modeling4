class Task:
    def __init__(self, time, stream_number):
        self.time = time
        self.time_left = None
        self.runtime = 0
        self.stream_number = stream_number
        self.wait_time = 0

    def start(self, time, runtime):
        if self.runtime > 0:
            self.wait_time += time - self.time
        self.time_left = runtime
        self.time = time

    def pause(self, time):
        dif_time = time - self.time
        self.runtime = dif_time
        self.time_left -= dif_time
        self.time = time

    def stop(self, time):
        self.time = time
        self.runtime += self.time_left
        self.time_left = 0


class Stream:
    def __init__(self, priority):
        self.priority = priority
        self.queue = []
        self.time = 0
        self.input_task_counter = 0
        self.sum_task_runtime = 0
        self.completed_task_counter = 0


    def add_task(self, task):
        self.queue.append(task)
        self.time = task.time
        if task.time_left is None:
            self.input_task_counter += 1

    def get_task(self):
        return self.queue.pop(0) if len(self.queue) > 0 else None

    def update_priority(self, task_runtime):
        self.sum_task_runtime += task_runtime
        self.completed_task_counter += 1
        if self.completed_task_counter > 10:
            self.priority = self.sum_task_runtime / self.completed_task_counter


class Server:
    def __init__(self, server_generators, server_generator_params, stream_config):
        self.time = 0
        self.busy = False
        self.task = None
        self.output_task = []
        self.streams = {}
        self.server_generators = server_generators
        self.server_generator_params = server_generator_params
        self.input_task_list = []
        for number, priority in stream_config.items():
            self.streams[number] = Stream(priority)

    def add_task(self, task, stream_number):
        self.input_task_list.append()
        if len(self.streams[stream_number].queue) == 0:
            if self.busy and self.streams[stream_number].priority > self.streams[self.task.stream_number].priority:
                self.task.pause(task.time)
                self.time = task.time
                self.streams[task.stream_number].add_task(self.task)
                self.task = None
                self.busy = False
            elif not self.busy:
                task.start(self.time, self.server_generators[stream_number](*self.server_generator_params[stream_number]))
                self.task = task
                self.time += task.time_left
                self.busy = True
                self.streams[task.stream_number].time = task.time
            else:
                self.streams[stream_number].add_task(task)
        else:
            self.streams[stream_number].add_task(task)

    def get_stream_number_with_high_priority(self, stream_numbers=None):
        high_priority = None
        number_stream_with_high_priority = None
        if stream_numbers is None:
            stream_numbers = self.streams.keys()

        for number in stream_numbers:
            stream = self.streams[number]
            if high_priority is None or stream.priority > high_priority:
                high_priority = stream.priority
                number_stream_with_high_priority = number
        return number_stream_with_high_priority


    def get_stream_numbers_by_time(self, time):
        stream_numbers = []
        for number, stream in self.streams.items():
            if stream.time == time:
                stream_numbers.append(number)
        return stream_numbers

    def get_nearest_stream_time(self):
        min_stream_time = None
        for stream in self.streams.values():
            if (min_stream_time is None or min_stream_time > stream.time):
                min_stream_time = stream.time
        return min_stream_time

    def get_nearest_stream_with_task_time(self):
        min_stream_time = None
        for stream in self.streams.values():
            if len(stream.queue) > 0 and (min_stream_time is None or min_stream_time > stream.time):
                min_stream_time = stream.time
        return min_stream_time

    def next_task(self):
        if self.busy:
            self.busy = False
            self.task.stop(self.time)
            self.streams[self.task.stream_number].update_priority(self.task.runtime)
            self.output_task.append(self.task)
            self.task = None
        nearest_stream_time = self.get_nearest_stream_with_task_time()
        self.time = nearest_stream_time
        if nearest_stream_time is not None:
            stream_numbers = self.get_stream_numbers_by_time(nearest_stream_time)
            stream_number = self.get_stream_number_with_high_priority(stream_numbers)
            task = self.streams[stream_number].get_task()
            task.start(self.time, self.server_generators[stream_number](*self.server_generator_params[stream_number]))
            self.task = task
            self.time += self.task.time_left
            self.busy = True


class Model:
    def __init__(self, runtime,
                 task_generators, task_generator_params,
                 server_generators, server_generator_params,
                 stream_config):
        self.runtime = runtime
        self.server = Server(server_generators, server_generator_params, stream_config)
        self.system_time = 0
        self.task_time = 0
        self.task_generators = task_generators
        self.task_generator_params = task_generator_params
        self.task_counter = 0

    def start(self):
        self.system_time = 0
        for number, stream in self.server.streams.items():
            self.task_counter += 1
            task_time = self.task_generators[number](*self.task_generator_params[number])
            task = Task(task_time, number)
            stream.add_task(task)
            stream.time = task_time
            if task_time < self.task_time or self.task_time == 0:
                self.task_time = task_time
        while self.system_time <= self.runtime:
            if self.system_time >= self.task_time:
                self.task_counter += 1
                stream_numbers = self.server.get_stream_numbers_by_time(self.task_time)
                for stream_number in stream_numbers:
                    task = Task(self.task_time + self.task_generators[stream_number](
                                                                         *self.task_generator_params[stream_number]),
                                stream_number)
                    self.server.add_task(task, stream_number)
            else:
                self.server.next_task()
            self.task_time = self.server.get_nearest_stream_time()
            self.system_time = self.server.time
        print("enter", self.task_counter, '; completed', len(self.server.output_task))
