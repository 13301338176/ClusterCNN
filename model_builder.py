from logistic_regression import LogisticRegression
from hidden_layer import HiddenLayer
from lenet import LeNetConvPoolLayer
import theano
import numpy
from theano import tensor as T

def build_lenet_layers(rng, batchSize, layers, x, imageSize=(28, 28), nkerns=[6, 16]):
    if layers is None:
        layers = []
        for i in range(4):
            layers.append(None)

    # Reshape to be compatable with input to LeNet
    layer0Input = x.reshape((batchSize, 1, imageSize[0], imageSize[1]))

    # Conv -> (28-5+1 , 28-5+1) = (24, 24)
    # Pooling -> (24/2, 24/2) = (12, 12)
    # Output -> (batch_size, nkerns[0], 12, 12))
    layer0 = LeNetConvPoolLayer(
        rng,
        input = layer0Input,
        imageShape = (batchSize, 1, imageSize[0], imageSize[1]),
        filterShape = (nkerns[0], 1, 5, 5),
        poolSize = (2, 2),
        setParams = layers[0]
    )

    # Conv -> (12-5+1, 12-5+1) = (8, 8)
    # Pooling -> (8/2, 8/2) = (4, 4)
    # Output -> (batch_size, nkerns[1], 4, 4)
    layer1 = LeNetConvPoolLayer(
        rng,
        input=layer0.output,
        imageShape=(batchSize, nkerns[0], 12, 12),
        filterShape=(nkerns[1], nkerns[0], 5, 5),
        poolSize=(2, 2),
        setParams = layers[1]
    )

    layer2Input = layer1.output.flatten(2)

    # Output -> (batch_size, nkerns[1] * 4 * 4)
    # construct a fully-connected sigmoidal layer
    layer2 = HiddenLayer(
        rng,
        input=layer2Input,
        nIn=nkerns[1] * 4 * 4,
        nOut=batchSize,
        activation=T.tanh,
        setParams = layers[2]
    )

    # The final classifier.
    outputLayer = LogisticRegression(input=layer2.output,
                                nIn=batchSize,
                                nOut=10,
                                setParams = layers[3])

    return (layer0, layer1, layer2, outputLayer)



def build_lenet_model(batchIndex, trainSet, validateSet, testSet, rng, imageSize=(28, 28), nkerns=[20, 50], learningRate=0.1, batchSize=500, layers=None):
    print '- Building the model'


    # The image data.
    x = T.matrix('x')
    # The label data. This is an integer vector
    y = T.ivector('y')

    layer0, layer1, layer2, outputLayer = build_lenet_layers(rng, batchSize, layers, x, imageSize, nkerns)

    # the cost we minimize during training is the NLL of the model
    cost = outputLayer.negative_log_likelihood(y)

    testSetX, testSetY = testSet
    validateSetX, validateSetY = validateSet
    trainSetX, trainSetY = trainSet

    # create a function to compute the mistakes that are made by the model
    testModel = theano.function(
        [batchIndex],
        outputLayer.errors(y),
        givens={
            x: testSetX[batchIndex * batchSize: (batchIndex + 1) * batchSize],
            y: testSetY[batchIndex * batchSize: (batchIndex + 1) * batchSize]
        }
    )

    validateModel = theano.function(
        [batchIndex],
        outputLayer.errors(y),
        givens={
            x: validateSetX[batchIndex * batchSize: (batchIndex + 1) * batchSize],
            y: validateSetY[batchIndex * batchSize: (batchIndex + 1) * batchSize]
        }
    )

    # The list of all the model parameters that must be trained by the network.
    params = outputLayer.params + layer2.params + layer1.params + layer0.params

    # create a list of gradients for all model parameters
    gradients = T.grad(cost, params)

    # SGD update
    updates = [
        (iParam, iParam - learningRate * iGrad)
        for iParam, iGrad in zip(params, gradients)
    ]

    trainModel = theano.function(
        [batchIndex],
        cost,
        updates=updates,
        givens={
            x: trainSetX[batchIndex * batchSize: (batchIndex + 1) * batchSize],
            y: trainSetY[batchIndex * batchSize: (batchIndex + 1) * batchSize]
        }
    )

    print '- Finished creating model'

    return [trainModel, validateModel, testModel, [layer0, layer1, layer2, outputLayer]]