class Task:
    def __init__(self, time, stream_number):
        self.time = time  # Текущее время
        self.time_left = None  # Оставшееся время обработки задачи
        self.runtime = 0  # Время обработки задачи
        self.stream_number = stream_number  # Номер потока, в который поступила задача
        self.wait_time = 0  # Время ожидания задачи

    # Метод запускает выполнение задачи
    def start(self, time, runtime):
        if self.runtime > 0:
            self.wait_time += time - self.time
        self.time_left = runtime
        self.time = time

    # Метод приостанавливает выполнение задачи
    def pause(self, time):
        self.runtime = time - self.time
        self.time_left -= self.runtime
        self.time = time

    # Метод завершает выполнение задачи
    def stop(self, time):
        self.time = time
        self.runtime += self.time_left
        self.time_left = 0


class Stream:
    def __init__(self, priority):
        self.priority = priority  # Приоритет потока
        self.queue = []  # Очередь задач
        self.time = 0  # Время добавления последнего потока
        self.input_task_counter = 0  # Количество поступивших задач
        self.sum_task_runtime = 0  # Сумма времен обработки задач
        self.completed_task_counter = 0  # Количество обработанных задач

    # Метод добавляет задачу в очередь потока
    def add_task(self, task):
        self.queue.append(task)
        self.input_task_counter += 1
        self.time = task.time

    # Метод возвращает первую задачу из очереди потока
    def get_task(self):
        return self.queue.pop(0) if len(self.queue) > 0 else None

    # Обновление приоритета потока
    def update_priority(self, task_runtime):
        self.sum_task_runtime += task_runtime
        self.completed_task_counter += 1
        if self.completed_task_counter > 10:
            self.priority = self.sum_task_runtime / self.completed_task_counter


class Server:
    def __init__(self, server_generators, server_generator_params, stream_config):
        self.time = 0  # Текущее время
        self.busy = False  # True - сервер занят, иначе свободен
        self.task = None  # Задача обрабатываемая сервером
        self.output_task = []  # Обработанные задачи
        self.streams = {}  # Потоки
        self.server_generators = server_generators  # Генераторы обработки задач
        self.server_generator_params = server_generator_params  # Параметры для генераторов
        # self.input_task_list = []
        for number, priority in stream_config.items():
            self.streams[number] = Stream(priority)

    # Метод добавляет задачу в указанный поток
    def add_task(self, task, stream_number):
        self.streams[stream_number].add_task(task)
        if self.task and self.streams[stream_number].priority > self.streams[self.task.stream_number].priority:
            self.next_task()

    # Метод возвращяет номер не пустого потока с наивысшим приоритетом
    def get_high_priority_stream_number(self, stream_numbers=None):
        high_priority = None
        h_stream_number = None
        if stream_numbers is None:
            stream_numbers = self.streams.keys()

        for number in stream_numbers:
            stream = self.streams[number]
            queue_len = len(stream.queue)
            if queue_len > 0:
                priority = stream.priority
                if (high_priority is None or priority > high_priority
                   or priority == high_priority and queue_len > len(self.streams[h_stream_number].queue)):
                    high_priority = stream.priority
                    h_stream_number = number
        return h_stream_number

    # Метод возвращает номера потоков, время поступления заданий в которые равно time
    def get_stream_numbers_by_time(self, time):
        stream_numbers = []
        for number, stream in self.streams.items():
            if stream.time == time:
                stream_numbers.append(number)
        return stream_numbers

    # Метод возвращает ближайшее время поступления задачи в поток
    def get_nearest_stream_time(self):
        min_stream_time = None
        for stream in self.streams.values():
            if len(stream.queue) == 1 and (min_stream_time is None or min_stream_time > stream.time):
                min_stream_time = stream.time
        return min_stream_time

    # Метод выполняет переход сервера с текущей задачи на следующую
    def next_task(self):
        nearest_stream_time = self.get_nearest_stream_time()
        h_stream_number = self.get_high_priority_stream_number()
        if self.busy:
            if nearest_stream_time\
                and self.streams[h_stream_number].priority > self.streams[self.task.stream_number].priority:
                # Приостановка текущей задачи, если поступила задача с более высоким приоритетом
                self.task.pause(nearest_stream_time)
                self.streams[self.task.stream_number].queue.append(self.task)
            else:
                # Завершение текущей задачи
                self.busy = False
                self.task.stop(self.time)
                self.streams[self.task.stream_number].update_priority(self.task.runtime)
                self.output_task.append(self.task)
                self.task = None
        if h_stream_number:
            # Запуск новой задачи
            self.task = self.streams[h_stream_number].get_task()
            self.time = self.task.time
            runtime = self.server_generators[h_stream_number](*self.server_generator_params[h_stream_number])
            self.task.start(self.time, runtime)
            self.time += runtime
            self.busy = True


class Model:
    def __init__(self, runtime,
                 task_generators, task_generator_params,
                 server_generators, server_generator_params,
                 stream_config):
        self.runtime = runtime
        self.server = Server(server_generators, server_generator_params, stream_config)
        self.task_times = {}  # Времена следующих задач для потоков
        self.task_time = 0
        self.stream_numbers = None
        self.task_generators = task_generators  # Генератор времени поступления задачи в поток
        self.task_generator_params = task_generator_params  # Параметры для генератора времен поступающих задач
        self.task_counter = 0  # Количество задач поступивших на потоки сервера

    # Метод возвращает потоки, время следующей задачи для которых равно time
    def _get_stream_numbers_by_time(self, time):
        stream_numbers = []
        for number, value in self.task_times.items():
            if value == time:
                stream_numbers.append(number)
        return stream_numbers

    # Метод возвращает время поступления ближайшей задачи
    def _get_nearest_task_time(self):
        min_time =  None
        for value in self.task_times.values():
            if min_time is None or value < min_time:
                min_time = value
        return min_time

    # Запуск процесса моделирования
    def start(self):
        # инициализация первых задач в потоках
        for number in self.server.streams.keys():
            task_time = self.task_generators[number](*self.task_generator_params[number])
            self.task_times[number] = task_time
            if task_time < self.task_time or self.task_time == 0:
                self.task_time = task_time
        self.stream_numbers = self._get_stream_numbers_by_time(self.task_time)
        for number in self.stream_numbers:
            self.task_counter += 1
            self.server.add_task(Task(self.task_time, number), number)
            self.task_times[number] += self.task_generators[number](*self.task_generator_params[number])
        self.server.next_task()
        # запуск цикла работы сервера
        while self.server.time <= self.runtime:
            self.task_time = self._get_nearest_task_time()
            if self.server.time >= self.task_time:
                # добавление задачи в поток с указанным временем
                self.stream_numbers = self._get_stream_numbers_by_time(self.task_time)
                for number in self.stream_numbers:
                    self.task_counter += 1
                    self.server.add_task(Task(self.task_time, number), number)
                    self.task_times[number] += self.task_generators[number](*self.task_generator_params[number])
            else:
                if not self.server.busy:
                    self.task_counter += 1
                    # добавление задачи в поток с указанным временем
                    self.stream_numbers = self._get_stream_numbers_by_time(self.task_time)
                    for number in self.stream_numbers:
                        self.server.add_task(Task(self.task_time, number), number)
                        self.task_times[number] += self.task_generators[number](*self.task_generator_params[number])
                self.server.next_task()
        print('total tasks:',self.task_counter)
        for key, sv in self.server.streams.items():
            print(key, ':', sv.priority, sv.input_task_counter, sv.completed_task_counter)
