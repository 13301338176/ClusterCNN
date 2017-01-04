import numpy as np
import matplotlib.pyplot as plt
import scipy.interpolate
from helpers.printhelper import PrintHelper as ph

class HyperParamSearch:
    def __init__(self, model = None, eval_func_name = None, hyper_params_range = None, points = []):
       self.model = model
       self.eval_func_name = eval_func_name
       self.hyper_params_range = hyper_params_range
       self.points = points
       self.max_point = None
       if len(self.points) != 0:
           self.__calc_max_point()


    def search(self):
        ph.DISP = False
        all_param_names = list(self.hyper_params_range.keys())
        accuracies = self.__recur_search(0, all_param_names)

        self.__calc_max_point()
        ph.DISP = True

        return self.points


    def get_max_point(self):
        return self.max_point


    def show_graph(self):
        self.__draw_contour_plot()


    def __calc_max_point(self):
        max_acc = 0.0
        for point in self.points:
            if point['accuracy'] > max_acc:
                self.max_point = point
                max_acc = point['accuracy']


    def __print_percentage(self):
        total = 1
        for key in self.hyper_params_range:
            total *= len(self.hyper_params_range[key])

        fraction = float(len(self.points)) / float(total)
        print '%.2f%%' % (fraction * 100.)


    def __recur_search(self, cur_index, all_param_names, assigned={}):
        param_name = all_param_names[cur_index]

        accuracies = []

        for param_value in self.hyper_params_range[param_name]:
            self.model.set_hyperparam(param_name, param_value)
            assigned[param_name] = param_value

            if cur_index == (len(all_param_names) - 1):
                eval_func = self.__get_eval_func()
                try:
                    accuracy = eval_func()
                except ValueError:
                    accuracy = 0.0
                    ph.linebreak()
                    ph.disp('Could not evaluate model!', ph.FAIL)
                    ph.linebreak()

                self.__print_percentage()

                assigned['accuracy'] = accuracy
                self.points.append(assigned.copy())
                accuracies.append(accuracy)
            else:
                accuracies.append(self.__recur_search(cur_index + 1, all_param_names, assigned))

        return accuracies


    def __draw_contour_plot(self):
        if len(self.hyper_params_range) != 2:
            raise ValueError('Can only draw contour plot for 2 dimensions')

        param_names = self.hyper_params_range.keys()
        x_name = param_names[0]
        y_name = param_names[1]

        X = [point[x_name] for point in self.points]
        Y = [point[y_name] for point in self.points]
        Z = [point['accuracy'] for point in self.points]

        X = np.array(X)
        Y = np.array(Y)
        Z = np.array(Z)

        factor = 1.0
        if X.max() < 1.0:
            factor = 10.0

        X *= factor
        Y *= factor
        Z *= factor

        xi, yi = np.linspace(X.min(), X.max(), 100), np.linspace(Y.min(), Y.max(), 1)

        xi, yi = np.meshgrid(xi, yi)
        rbf = scipy.interpolate.Rbf(X, Y, Z, function='linear')
        zi = rbf(xi, yi)
        plt.imshow(zi, vmin=Z.min(), vmax=Z.max(), origin='lower', extent=[X.min(), X.max(), Y.min(), Y.max()])
        plt.scatter(X, Y, c=Z)
        plt.colorbar()
        plt.savefig("data/paramcontour.png")
        plt.show()


    def __get_eval_func(self):
        try:
            return getattr(self.model, self.eval_func_name)
        except AttributeError:
            print 'Could not find evaluation function'
            return None

