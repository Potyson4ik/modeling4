import model
import matplotlib.pyplot as plt
from numpy.random import logistic, standard_t, rayleigh, beta, weibull, gamma

def logistic_plus(mu, s):
    result = logistic(mu, s)
    while result < 0:
        result = logistic(mu, s)
    return result

def student_abs(nu):
    return abs(standard_t(nu))

if __name__ == "__main__":
    stream_config = {1: 0.0001, 2: 0.0001, 3: 0.0001}
    task_generators = {1: logistic_plus,  # Положительные результаты функции логистического распределения
                       2: rayleigh,       # Распределение Рэлея
                       3: gamma           # Распределение Эрланга (вычисляется из гамма распределения)
                       }
    task_generator_params = {1: (0, 1), 2: [1], 3: [2]}
    server_generators = {1: student_abs,  # Распределение Стьюдента (результат взят по модулю)
                         2: beta,         # Бета-распределение
                         3: weibull       # Распределение Вейбулла
                         }
    server_generator_params = {1: [1], 2: (1, 2), 3: [1]}  # Параметры для распределений

    model1 = model.Model(10000,
                         task_generators,
                         task_generator_params,
                         server_generators,
                         server_generator_params,
                         stream_config)
    model1.start()
    model1.print_info()

    stream_priority_M_hist = {1:[], 2:[], 3:[]}
    for i in range(1000, 200000, 1000):
        model1 = model.Model(10000,
                             task_generators,
                             task_generator_params,
                             server_generators,
                             server_generator_params,
                             stream_config)
        model1.start()
        for number, stream in model1.server.streams.items():
            stream_priority_M_hist[number].append(stream.get_M())
    for number, hist in stream_priority_M_hist.items():
        plt.figure("Зависимость мат.ожидания приоритета потока "+str(number)+" от времени")
        plt.plot(range(1000, 200000, 1000), hist)
        plt.title("Зависимость мат.ожидания приоритета потока "+str(number)+" от времени")
        plt.xlabel('Время работы модели')
        plt.ylabel('Мат.ожидание приоритета')
        plt.grid(True)
        plt.show()