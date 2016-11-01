from keras.models import Sequential
from keras.layers.convolutional import Convolution2D
from keras.layers.convolutional import MaxPooling2D
from keras.layers.core import Activation
from keras.layers.core import Flatten
from keras.layers.core import Dense
from keras import backend as K
from keras.models import load_model

from clustering import load_or_create_centroids
from clustering import build_patch_vecs
from model_wrapper import ModelWrapper

from sklearn.cross_validation import train_test_split
from sklearn import datasets
from keras.optimizers import SGD
from keras.utils import np_utils
import numpy as np
import pickle
import plotly.plotly as py
from plotly.tools import FigureFactory as FF
import plotly.tools as tls
from helpers.mathhelper import *
from load_runner import LoadRunner
from anchor_normalizer import AnchorVecNormalizer

def add_convlayer(model, nkern, subsample, filter_size, input_shape=None, weights=None):
    if input_shape is not None:
        convLayer = Convolution2D(nkern, filter_size[0], filter_size[1], border_mode='same', subsample=subsample, input_shape=input_shape)
    else:
        convLayer = Convolution2D(nkern, filter_size[0], filter_size[1], border_mode='same', subsample=subsample)

    model.add(convLayer)

    if not weights is None:
        params = convLayer.get_weights()
        bias = params[1]

        convLayer.set_weights([weights, bias])

    model.add(Activation('relu'))
    maxPoolingOut = MaxPooling2D(pool_size=(2,2), strides=(2,2))
    model.add(maxPoolingOut)
    convout_f = K.function([model.layers[0].input], [maxPoolingOut.output])
    return convout_f


def add_fclayer(model, output_dim, weights=None):
    dense_layer = Dense(output_dim)

    model.add(dense_layer)

    if not weights is None:
        bias = dense_layer.get_weights()[1]
        dense_layer.set_weights([weights, bias])

    fcOutLayer = Activation('relu')
    model.add(fcOutLayer)
    fcOut_f = K.function([model.layers[0].input], [fcOutLayer.output])
    return fcOut_f


def fetch_data(test_size):
    dataset = datasets.fetch_mldata('MNIST Original')
    data = dataset.data.reshape((dataset.data.shape[0], 28, 28))
    data = data[:, np.newaxis, :, :]

    return train_test_split(data / 255.0, dataset.target.astype('int'), test_size=test_size)


def create_model(train_percentage, should_set_weights, target_stds=[None] * 5):
    # Break the data up into test and training set.
    # This will be set at 0.3 is test and 0.7 is training.
    (train_data, test_data, train_labels, test_labels) = fetch_data(0.3)

    remaining = int(len(train_data) * train_percentage)

    train_labels = np_utils.to_categorical(train_labels, 10)
    test_labels = np_utils.to_categorical(test_labels, 10)

    # Only use a given amount of the training data.
    scaled_train_data = train_data[0:remaining]
    train_labels = train_labels[0:remaining]

    print 'Running for %.2f%% test size' % (train_percentage * 100.)
    print 'The training data has a length of %i' % (len(train_data))

    input_shape = (1, 28, 28)
    subsample=(1,1)
    filter_size=(5,5)
    batch_size = 5
    nkerns = (6, 16)
    force_create = True

    input_centroids = [None] * 5
    layer_out = [None] * 4

    model = Sequential()

    if should_set_weights[0]:
        print 'Setting conv layer 0 weights'
        input_centroids[0] = load_or_create_centroids(force_create, 'data/centroids/centroids0.h5',
                                batch_size, train_data, input_shape, subsample,
                                filter_size, nkerns[0], target_stds[0])

    convout0_f = add_convlayer(model, nkerns[0], subsample, filter_size, input_shape=input_shape, weights=input_centroids[0])

    if should_set_weights[1]:
        print 'Setting conv layer 1 weights'
        layer_out[0] = convout0_f([train_data])[0]
        input_shape = (nkerns[0], 14, 14)
        input_centroids[1] = load_or_create_centroids(force_create, 'data/centroids/centroids1.h5',
                                batch_size, layer_out[0], input_shape, subsample, filter_size, nkerns[1], target_stds[1])

    convout1_f = add_convlayer(model, nkerns[1], subsample, filter_size, input_shape=input_shape, weights=input_centroids[1])


    model.add(Flatten())

    if should_set_weights[2]:
        print 'Setting fc layer 0 weights'
        layer_out[1] = convout1_f([train_data])[0]
        input_shape = (nkerns[1], 7, 7)
        input_centroids[2] = load_or_create_centroids(force_create, 'data/centroids/centroids2.h5',
                                batch_size, layer_out[1], input_shape, subsample,
                                filter_size, 120, target_stds[2], convolute=False)
        sp = input_centroids[2].shape
        input_centroids[2] = input_centroids[2].reshape(sp[1], sp[0])

    fc0_f = add_fclayer(model, 120, weights=input_centroids[2])

    if should_set_weights[3]:
        print 'Setting fc layer 1 weights'
        layer_out[2] = fc0_f([train_data])[0]
        input_shape = (120,)
        input_centroids[3] = load_or_create_centroids(force_create, 'data/centroids/centroids3.h5',
                                    batch_size, layer_out[2], input_shape, subsample,
                                    filter_size, 84, target_stds[3], convolute=False)
        sp = input_centroids[3].shape
        input_centroids[3] = input_centroids[3].reshape(sp[1], sp[0])

    fc1_f = add_fclayer(model, 84, weights=input_centroids[3])

    if should_set_weights[4]:
        print 'Setting classifier weights'
        layer_out[3] = fc1_f([train_data])[0]
        input_shape=(84,)
        input_centroids[4] = load_or_create_centroids(force_create, 'data/centroids/centroids4.h5',
                                    batch_size, layer_out[3], input_shape, subsample,
                                    filter_size, 10, target_stds[4], convolute=False)
        sp = input_centroids[4].shape
        input_centroids[4] = input_centroids[4].reshape(sp[1], sp[0])

    classification_layer = Dense(10)
    model.add(classification_layer)

    if should_set_weights[4]:
        bias = classification_layer.get_weights()[1]
        classification_layer.set_weights([input_centroids[4], bias])

    model.add(Activation('softmax'))

    print 'Compiling model'
    opt = SGD(lr = 0.01)
    model.compile(loss='categorical_crossentropy', optimizer=opt, metrics=['accuracy'])

    if len(scaled_train_data) > 0:
        # Normalize the anchor vectors as the model weights are updated.
        anchor_vec_normalizer = AnchorVecNormalizer(filter_size, nkerns)
        model.fit(scaled_train_data, train_labels, batch_size=batch_size, nb_epoch=20, verbose=1, callbacks=[anchor_vec_normalizer])

    (loss, accuracy) = model.evaluate(test_data, test_labels, batch_size=batch_size, verbose=1)
    print ''
    print 'Accuracy %.9f%%' % (accuracy * 100.)

    # print 'Saving'
    # model.save_weights(save_model_filename)
    return ModelWrapper(accuracy, input_centroids, model)

def get_all_mags(anchor_vecs):
    mags = []
    for anchor_vec in anchor_vecs:
        # There are sub anchor vectors.
        sub_mags = []
        for sub_anchor_vec in anchor_vec:
            sub_mags.append(np.linalg.norm(sub_anchor_vec))

        mags.append(sub_mags)

    return mags


def get_all_angles(anchor_vecs):
    angles = []
    for anchor_vec in anchor_vecs:
        sub_mags = []
        # Create a unit vector in the the first dimension.]:
        dim = np.array(anchor_vec).shape[1]
        compare_vec = np.zeros(dim)
        compare_vec[0] = 1.

        sub_angles = []
        for sub_anchor_vec in anchor_vec:
            # Normalize
            sub_anchor_vec = sub_anchor_vec / np.linalg.norm(sub_anchor_vec)
            sub_angles.append(angle_between(compare_vec, sub_anchor_vec))

        angles.append(sub_angles)

    return angles


def print_scalar_data(data):
    for model_data in data:
        print '%s: %.5f%%' % (model_data[0], model_data[1])

        for sub_data in model_data[2]:
            std = np.std(sub_data)
            avg = np.average(sub_data)
            min_val = np.amin(sub_data)
            max_val = np.amax(sub_data)
            print 'STD: %.9f' % (std)
            print 'AVG: %.9f' % (avg)
            print 'MIN: %.9f' % (min_val)
            print 'MAX: %.9f' % (max_val)
            print '--------------'

        print ''
        print ''



def create_compare_models_mags():
    base_model = create_model(0, [False] * 5)
    base_anchor_vecs = get_anchor_vectors(base_model)

    kmeans_model = create_model(0, [True] * 5)
    kmeans_anchor_vecs = get_anchor_vectors(kmeans_model)

    base_mags = get_all_mags(base_anchor_vecs)
    kmeans_mags = get_all_mags(kmeans_anchor_vecs)

    return [['Base Magnitudes', base_model.accuracy, base_mags], ['K-means Magnitudes', kmeans_model.accuracy, kmeans_mags]]

def create_compare_models_angles():
    base_model = create_model(0.4, [False] * 5)
    base_anchor_vecs = get_anchor_vectors(base_model)

    kmeans_model = create_model(0.4, [True] * 5)
    kmeans_anchor_vecs = get_anchor_vectors(kmeans_model)

    base_angles = get_all_angles(base_anchor_vecs)
    kmeans_angles = get_all_angles(kmeans_anchor_vecs)

    return [['Base Angles', base_model.accuracy, base_angles], ['K-means Angles', kmeans_model.accuracy, kmeans_angles]]


def test_train_data(const_fact):
    train_sizes = np.arange(0, 1.1, 0.1)

    train_size_models = []
    for train_size in reversed(train_sizes):
        reg_model = create_model(train_size, [False] * 5, const_fact)
        kmeans_model = create_model(train_size, [True] * 5, const_fact)

        train_size_models.append([train_size, reg_model.accuracy, kmeans_model.accuracy])

        del kmeans_model
        del reg_model

    return train_size_models

def get_model_angle_std(model):
    layer_anchor_vecs = get_anchor_vectors(model)
    layer_anchor_vec_angles = get_anchor_vector_angles(layer_anchor_vecs)
    layer_anchor_vec_angle_stds = [np.std(layer_angles) for layer_angles in layer_anchor_vec_angles]
    return layer_anchor_vec_angle_stds

def get_model_mag_std(model):
    layer_anchor_vecs = get_anchor_vectors(model)

    layer_anchor_vec_mags = []
    for layer_anchor_vec in layer_anchor_vecs:
        mags = [np.linalg.norm(anchor_vec) for anchor_vec in layer_anchor_vec]
        layer_anchor_vec_mags.append(np.std(mags))

    return layer_anchor_vec_mags

def get_model_raw_std(model):
    raw_stds = []
    for layer in model.model.layers:
        weights = layer.get_weights()
        if len(weights) > 0:
            weights = weights[0]
            raw_stds.append(np.std(weights))
    return raw_stds


kmeans_model = create_model(0.4, [True] * 5)




# kmeans_model = create_model(train_size, [True] * 5, const_fact)
