import matplotlib.pyplot as plt
from tensorflow.contrib.opt import ScipyOptimizerInterface

import solver.charts as charts

from equations.poisson_pde.create_model_graph import *
from equations.solution import Solution

DATA_DIR = './data-l-BFGS-b'
MODEL_NAME = 'model'
MODEL_PATH = '{}/{}'.format(DATA_DIR, MODEL_NAME)

if not ckeck_if_model_graph_exists(DATA_DIR, MODEL_NAME):
    create_model_graph(DATA_DIR, MODEL_NAME, True)

with tf.Session() as s:
    saver = tf.train.import_meta_graph(MODEL_PATH + '.meta')
    saver.restore(s, tf.train.latest_checkpoint(DATA_DIR))

    solution = Solution.load()

    feed_dict = {EQUATION_CONSTRAIN: ps.uniform_points_2d(0, 1, 11, 0, 1, 11),
                 BC1_CONSTRAIN: ps.uniform_points_2d(0, 1, 10, 0, 0, 1) + \
                                ps.uniform_points_2d(0, 1, 10, 1, 1, 1) + \
                                ps.uniform_points_2d(0, 0, 1, 0, 1, 10) + \
                                ps.uniform_points_2d(1, 1, 1, 0, 1, 10)}

    fig = plt.figure()
    plt.ion()
    plt.draw()

    # see examples here https://bitbucket.org/andrewpeterson/amp/pull-requests/5/master/diff
    external_optimizer = ScipyOptimizerInterface(solution.loss,
                                                 var_list=[solution.weights, solution.centers, solution.parameters],
                                                 method='l-BFGS-b',
                                                 options={'maxiter': 10, 'ftol': 1.e-10, 'gtol': 1.e-10, 'factr': 1.e4})

    error_plot = charts.Error(fig, 121)
    nn_surface = charts.Surface(fig, 122,
                                x0=0, x1=1, x_count=25,
                                y0=0, y1=1, y_count=25,
                                function=lambda x: solution.y(x))

    # todo: what is the reason of it?
    # some hack for now
    prev_error = None

    def step_callback(x):
        """
        :param x: the current values of parameters
        """
        pass

    def loss_callback(x):
        """
        :param x: the current values of parameters
        """
        global prev_error
        if prev_error is None or prev_error > x:
            error_plot.add_error(x)
            print(x)
        prev_error = x

    i = 1
    while True:
        external_optimizer.minimize(session=s,
                                    feed_dict=solution.constrain_feed_dict(feed_dict),
                                    fetches=[solution.loss],
                                    step_callback=step_callback,
                                    loss_callback=loss_callback)
        error_plot.update()

        nn_surface.update()

        plt.draw()
        plt.pause(0.005)

        saver.save(s, MODEL_PATH, global_step=i, write_meta_graph=False)
        i += 1