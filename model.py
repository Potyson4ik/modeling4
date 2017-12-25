import random


class Task:
    def __init__(self, current_time, stream_number):
        self.stream_number = stream_number
        self.is_used = False
        self.runtime = 0  # Время обработки задачи
        self.wait_time = 0  # Время ожидания задачи в очереди
        self.time = current_time  # Системное время
        self.is_run = False  # True - задача в данный момент обрабатывается севером

    # Метод возвращает время обработки задачи на сервере
    def get_total_time(self):
        return self.runtime + self.wait_time

    # Метод запускает выполнение задачи
    def run_task(self, time):
        self.is_used = True
        self.wait_time += time - self.time
        self.time = time
        self.is_run = True
        return self.runtime

    # Метод останавливает выполнение задачи
    def stop_task(self, time):
        self.runtime += time - self.time
        self.time = time
        self.task_run = False


class Stream:
    def __init__(self, priority, generator, generator_param):
        self.priority = priority  # Приоритет потока
        self.server_generator = generator  # Генератор времени обработки задачи сервером
        self.server_generator_param = generator_param # Входные параметры для генератора
        self.queue = []  # Очередь задач в потоке
        self.time = 0  # Время работы потока
        self.wait_time = 0  # Время бездействия потока
        self.added_task = 0  # Количество принтых потоком задач

    def add_task(self, task):
        pass




class Server:
    def __init__(self, generators_param, generators, stream_config):
        self.streams = {}  # Потоки
        self.generators = generators  # Генераторы времён обработки ресурсов
        self.generators_param = generators_param  # Входные параметры для генераторов
        self.time = 0  # Время работы сервера
        self.output_tasks = []  # Список завершенных задач
        # Инициализация потоков по заданной конфигурации
        for key, priority in stream_config.items():
            self.streams[key] = Stream(priority, generators[key], generators_param[key])

    # Метод добавляет задачу на сервер
    def add_task(self, task):
        self.streams[task.stream_number].add_task(task)

    # Метод возвращает индекс модуля, вида - (<тип ресурса>, <номер модуля в списке>)
    def _get_module_index_by_nearest_event(self):
        min_module_time = None
        module_index = None
        for key, module_list in self.modules.items():
            for i in range(len(module_list)):
                module = module_list[i]
                if (min_module_time is None or module.time < min_module_time) and module.time > 0 and module.busy:
                    min_module_time = module.time
                    module_index = (key, i)
        return module_index

    # Метод возвращает время ближайшего события на сервере
    def get_nearest_event_time(self):
        min_module_time = None
        for module_list in self.modules.values():
            for module in module_list:
                if (min_module_time is None or module.time < min_module_time) and module.time > 0 and module.busy:
                    min_module_time = module.time
        return min_module_time

    # Метод выполняет следующее событие
    def next_event(self):
        key, index = self._get_module_index_by_nearest_event()
        task = self.modules[key][index].next_task()
        if task is not None:
            if task.get_next_resource() is not None:
                module_index = None
                min_queue_size = None
                next_resource = task.get_next_resource()
                for i in range(len(self.modules[next_resource])):
                    module = self.modules[next_resource][i]
                    if not module.busy:
                        module_index = i
                        break
                    if min_queue_size is None or min_queue_size > len(module.queue):
                        module_index = i
                        min_queue_size = len(module.queue)
                self.modules[next_resource][module_index].add_task(task)
            else:
                self.output_tasks.append(task)


class Model:
    def __init__(self, runtime, task_package, module_gen, module_gen_params, task_gen, task_gen_params, module_config):
        self.server = Server(module_gen_params, module_gen, module_config)
        self.task_generator = task_gen
        self.task_generator_params = task_gen_params
        self.task_package = task_package
        self.runtime = runtime

    def start(self):
        system_time = 0
        task_time = self.task_generator(*self.task_generator_params)
        system_time = task_time
        task = Task(self.task_package[:], task_time, task_time)
        task_counter = 1
        while system_time is None or system_time < self.runtime:
            if system_time is None or system_time >= task_time:
                self.server.add_task(task)
                g_time = self.task_generator(*self.task_generator_params)
                task_time += g_time
                task = Task(self.task_package[:], task_time, g_time)
                task_counter += 1
            else:
                self.server.next_event()
            system_time = self.server.get_nearest_event_time()

        print('Задачи принятые сервером - ', task_counter)
        print('Обработано задач - ', len(self.server.output_tasks))
        info = """
    Модуль: тип ресурса - {}, номер - {};
        Выполнено задач: {};
        Задачи оставшиеся в очереди: {};
        Общее время обработки ресурсов: {:.3f};
        Среднее время обработки ресурса: {:.3f};
        Время ожидания новых ресурсов: {:.3f};
        Среднее время ожидания ресурса: {:.3f};
        Максимальное время ожидания ресурса: {:.3f};
        Среднее время поступления ресурсов: {:.3f}
        Загруженность модуля: {:.5f}"""
        for resource, modules in self.server.modules.items():
            for number, module in enumerate(modules):
                print(info.format(resource, number,
                                  module.completed_task_counter,
                                  len(module.queue),
                                  sum(module.module_time_list),
                                  module.get_avg_module_time(),
                                  module.wait_time,
                                  module.wait_time / len(module.wait_time_list),
                                  max(module.wait_time_list),
                                  module.get_avg_task_time(),
                                  module.get_load()))
            print()