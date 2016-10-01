from theano.tensor.signal import pool
import theano
import numpy as np
from theano import tensor as T
from theano.tensor.nnet import conv2d

class LeNetConvPoolLayer(object):
    def __init__(self, rng, input, filterShape, imageShape, poolSize = (2,2), setParams=None):
        assert imageShape[1] == filterShape[1]
        self.input = input

        if not setParams is None:
            W, b = setParams
        else:
            fanIn = np.prod(filterShape[1:])
            fanOut = (filterShape[0] * numpy.prod(filterShape[2:]) / numpy.prod(poolSize))
            wBound = numpy.sqrt(6. / (fanIn + fanOut))

            # Output shape is product of array.
            W = np.asarray(
                    rng.uniform(
                        low=-wBound,
                        high=wBound,
                        size=filterShape),
                    dtype=theano.config.floatX)
            b = np.zeros((filterShape[0],), dtype=theano.config.floatX)

        self.W = theano.shared(W, borrow=True)

        self.b = theano.shared(value=b, borrow=True)

        convOut = conv2d(input=self.input,
                        filters=self.W,
                        filter_shape=filterShape,
                        input_shape=imageShape,
                        subsample=(1,1),
                        border_mode='valid')

        # Pooling
        pooledOut = pool.pool_2d(
            input=convOut,
            ds=poolSize,
            ignore_border=True
        )

        self.output = T.tanh(pooledOut + self.b.dimshuffle('x', 0, 'x', 'x'))
        self.params = [self.W, self.b]


def get_image_patches(inputImg, inputShape, stride, filterShape):
    # Reconstruct the image as a matrix.
    rows = []
    for i in range(inputShape[0]):
        row = []
        for j in range(inputShape[1]):
            row.append(inputImg[(i * inputShape[0]) + j])
        rows.append(row)

    imageMat = np.array(rows)

    # Get the patch.

    rowOffset = 0
    colOffset = 0
    patches = []
    while rowOffset < inputShape[0] - filterShape[0]:
        while colOffset < inputShape[1] - filterShape[1]:
            patch = imageMat[rowOffset:rowOffset+filterShape[0], colOffset:colOffset+filterShape[1]]
            patches.append(patch)
            colOffset += stride[1]
        rowOffset += stride[0]
        colOffset = 0

    return patches