import model
from numpy.random import logistic, standard_t, rayleigh, beta, weibull, gamma


def logistic_plus(mu, s):
    result = logistic(mu, s)
    while result < 0:
        result = logistic(mu, s)
    return result


def student_abs(nu):
    return abs(standard_t(nu))


stream_config = {1: 1, 2: 1, 3: 1}
task_generators = {1: logistic_plus, 2: rayleigh, 3: gamma}
task_generator_params = {1: (0, 1), 2: [1], 3: [2]}
server_generators = {1: student_abs, 2: beta, 3: weibull}
server_generator_params = {1: [1], 2: (0, 1), 3: [1]}

model1 = model.Model(1000, task_generators, task_generator_params, server_generators, server_generator_params, stream_config)
model1.start()