import numpy as np
import datetime
from helpers.printhelper import PrintHelper as ph
from sklearn.ensemble import IsolationForest


class DiscriminatoryFilter(object):
    # 0.14 actual
    CUTOFF = [25000, 25000, 40000, 40000, 40000]
    use_select_count = False

    def __init__(self, selection_count = None):
        """
        Constructor

        :param selection_percent: floating point value in [0.0, 1.0]
        the percentage of elements sorted by variance to return.
        """
        self.selection_count = selection_count


    def filter_outliers(self, samples):
        ph.disp('Filtering out outliers')
        clf = IsolationForest(max_samples=5000, n_estimators = 500, n_jobs=-1)
        clf.fit(samples)
        samples_pred = clf.predict(samples)

        for sample, is_outlier in zip(samples, samples_pred):
            if is_outlier == 1:
                yield sample

        ph.disp('Outliers filtered')


    def disp_data_info(self, samples):
        variances = np.var(samples, axis=1)
        means = np.mean(samples, axis=1)

        avg_vars = np.mean(variances)
        std_vars = np.std(variances)
        avg_mean = np.mean(means)

        ph.disp('Avg Var %.6f, Std Var %.6f, Avg Mean: %.6f' % (avg_vars,
            std_vars, avg_mean))


    def get_selected(self, samples, layer_index):
        #self.disp_data_info(samples)
        variances = np.var(samples, axis=1)
        per_sample_avg = np.mean(variances)
        per_sample_std = np.std(variances)
        print('The min variance is ', np.amin(variances))
        print('The max variance is ', np.amax(variances))
        print('per sample std ', per_sample_std)
        print('per sample avg ', per_sample_avg)

        if self.selection_count is None:
            return samples
        return samples[np.random.choice(samples.shape[0], self.selection_count,
            replace=False), :]

    def get_top(self, samples, layer_index):
        if len(samples) > self.selection_count:
            samples = samples[0:self.selection_count]
            ph.disp('-----Selected %i samples' % (self.selection_count))
        else:
            ph.disp('-----Left with %i samples' % (len(samples)))

        variances = np.var(samples, axis=1)
        variances = np.array(variances, np.float32)
        per_sample_avg = np.mean(variances)
        per_sample_std = np.std(variances)
        print('The min variance is ', np.amin(variances))
        print('The max variance is ', np.amax(variances))
        print('per sample std ', per_sample_std)
        print('per sample avg ', per_sample_avg)

        return samples


    def get_sorted(self, samples, layer_index):
        if self.selection_count is None:
            return np.array(samples)
        #self.disp_data_info(samples)

        variances = np.var(samples, axis=1)
        variances = np.array(variances, np.float32)
        per_sample_avg = np.mean(variances)
        per_sample_std = np.std(variances)

        sample_variances = list(zip(samples, variances))

        if layer_index == 0:
            thresh_var = per_sample_avg
        elif layer_index == 1:
            thresh_var = per_sample_avg
        else:
            thresh_var = per_sample_avg

        ph.disp('-----Filtering out values lower than %.5f to make sorting easier' % (thresh_var))
        before_len = len(sample_variances)
        sample_variances = [(sample, variance) for sample, variance in
                sample_variances if variance > (thresh_var)]
        ph.disp('-----Filtered out %i values to make sorting easier' %
                (before_len - len(sample_variances)))

        ph.disp('-----Beginning sort')
        sample_variances = sorted(sample_variances, key = lambda x: -x[1])
        ph.disp('-----Sort finished')
        samples = [sample_variance[0] for sample_variance in sample_variances]

        #if self.selection_count is not None:
        #    samples = np.array(samples)
        #    return samples[np.random.choice(samples.shape[0],
        #        self.selection_count, replace=False), :]

        return np.array(samples)


    #def custom_filter(self, samples):
    #    """
    #    Filter the samples based off of the selection percentage,
    #    an optional min_variance, and an optional CUTOFF to determine
    #    the max number of values that are selected.

    #    :param samples: The list of samples to be filtered.
    #    :return the selected samples
    #    """

    #    ph.disp('Getting sample variances')

    #    variances = np.var(samples, axis=1)
    #    print('max var %.2f' % np.amax(variances))
    #    sample_variances = list(zip(samples, variances))

    #    #overall_var = np.var(samples)
    #    #overall_avg = np.mean(samples)
    #    per_sample_std = np.std(variances)
    #    per_sample_avg = np.mean(variances)

    #    #thresh_fact = 0.0
    #    #min_variance = per_sample_avg + (thresh_fact * per_sample_var)
    #    min_variance = self.CUTOFF[self.cur_layer]

    #    #ph.disp('STD: %.5f, Avg: %.5f' % (overall_var, overall_avg), ph.OKGREEN)
    #    #ph.disp('Per Sample STD: STD: %.5f, Avg: %.5f' % (per_sample_var, per_sample_avg), ph.OKGREEN)

    #    if self.selection_percent is None:
    #        ph.disp('Skipping discriminatory filter', ph.FAIL)
    #        return samples

    #    ph.disp(('-' * 5) + 'Filtering input.')

    #    if not self.use_select_count:
    #        ph.disp('-----Min variance: %.5f, Select: %.5f%%' % (min_variance, (self.selection_percent * 100.)))

    #    ph.disp('-----Starting with %i samples' % len(samples))

    #    prev_len = len(variances)

    #    if min_variance != 0.0:
    #        # Discard due to minimum variance.
    #        sample_variances = [(sample, variance) for sample, variance in sample_variances
    #                if variance > min_variance]

    #        ph.disp('-----%i samples discarded from min variance' % (prev_len - len(sample_variances)))
    #        ph.disp('-----%i samples remain' % len(sample_variances))

    #    if not self.use_select_count:
    #        selection_count = int(len(sample_variances) * self.selection_percent)
    #    else:
    #        selection_count = int(self.selection_percent)

    #    #ph.disp('-----Trying to select %i samples' % selection_count)

    #    # Order by variance.
    #    # Sort with the highest values first.
    #    #ph.disp('-----Starting sort')
    #    #start = datetime.datetime.now()

    #    #toss_thresh = per_sample_avg
    #    #sample_variances = [(sample, variance) for sample, variance in sample_variances if variance > toss_thresh]
    #    #ph.disp('-----Filtered out values to make sorting easier')
    #    #sample_variances = sorted(sample_variances, key = lambda x: -x[1])

    #    #delta = datetime.datetime.now() - start
    #    #seconds = delta.seconds
    #    #microseconds = delta.microseconds % 100
    #    #ph.disp('-----Sort ended (%s s : %s ms)' % (str(seconds), str(microseconds)))

    #    #print('Min variance threshold is %.2f' % (sample_variances[selection_count][1]))

    #    samples = [sample_variance[0] for sample_variance in sample_variances]
    #    #samples = samples[0:selection_count]
    #    #self.selection_percent = int(self.selection_percent)
    #    #samples = samples[0:self.selection_percent]

    #    # An optional cutoff parameter to only select CUTOFF values.
    #    # For slower computers with not as much RAM and processing power.
    #    #ph.disp('The current cutoff is ' + str(self.CUTOFF[self.cur_layer]))
    #    #if (self.CUTOFF is not None) and (self.CUTOFF[self.cur_layer] is not None) and selection_count > self.CUTOFF[self.cur_layer]:
    #    #    ph.disp('-----Greater than the cutoff randomly sampling')
    #    #    selected_samples = []
    #    #    cur_cutoff = self.CUTOFF[self.cur_layer]

    #    #    for i in np.arange(cur_cutoff):
    #    #        select_index = np.random.randint(len(samples))
    #    #        selected_samples.append(samples[select_index])
    #    #        del samples[select_index]
    #    #    samples = selected_samples

    #    self.cur_layer += 1

    #    return samples


    def filter_samples(self, samples):
        """
        Wrapper for the custom_filter that outputs debug information
        """

        before_len = len(samples)

        samples = self.custom_filter(samples)

        after_len = len(samples)
        ph.disp(('-' * 5) + '%i reduced to %i' % (before_len, after_len))

        return samples

