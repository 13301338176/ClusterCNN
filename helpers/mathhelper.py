import numpy as np


def unit_vector(vector):
    return vector / np.linalg.norm(vector)

def angle_between(v1, v2):
    v1_u = unit_vector(v1)
    v2_u = unit_vector(v2)
    return np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))


def get_layer_anchor_vectors(layer_data):
    sp = layer_data.shape
    if len(sp) > 2:
        anchor_vecs = []
        for conv_filter in layer_data:
            conv_filter = conv_filter.flatten()
            anchor_vecs.append(conv_filter)
        return anchor_vecs
    else:
        print sp[0]
        return layer_data


# A helper function to get the anchor vectors of all layers..
def get_anchor_vectors(model0):
    anchor_vectors = []

    for layer in model0.model.layers:
        params = layer.get_weights()
        if len(params) > 0:
            weights = params[0]
            if len(weights.shape) > 2:
                # This is a convolution layer
                add_anchor_vectors = []
                for conv_filter in weights:
                    conv_filter = conv_filter.flatten()
                    add_anchor_vectors.append(conv_filter)
                anchor_vectors.append(add_anchor_vectors)
            else:
                sp = weights.shape
                weights = weights.reshape(sp[1], sp[0])
                anchor_vectors.append(weights)

    return anchor_vectors


def get_anchor_vector_angles(layer_anchor_vecs):
    angles = []
    for anchor_vecs in layer_anchor_vecs:
        layer_angles = []
        for anchor_vec in anchor_vecs:
            compare_vec = np.zeros(len(anchor_vec))
            compare_vec[0] = 1.
            angle = angle_between(compare_vec, anchor_vec)
            layer_angles.append(angle)
        angles.append(layer_angles)

    return angles


def set_anchor_vectors(model, anchor_vectors, nkerns, filter_size):
    sps = [anchor_vector.shape for anchor_vector in anchor_vectors]

    # Conolutional layer 0.
    anchor_vectors[0] = anchor_vectors[0].reshape(sps[0][0], 1, filter_size[0], filter_size[1])

    # Convolutional layer 1.
    sp = anchor_vectors[1].shape
    anchor_vectors[1] = anchor_vectors[1].reshape(sps[1][0], nkerns[0], filter_size[0], filter_size[1])

    # Switch the dimensions of the FC layers.
    for i in range(2, 5):
        anchor_vectors[i] = anchor_vectors[i].reshape(sps[i][1], sps[i][0])

    anchor_vectors_index = 0
    for i, layer in enumerate(model.layers):
        params = layer.get_weights()
        if len(params) > 0:
            # This is a layer that has network parameters.
            set_anchor_vector = anchor_vectors[anchor_vectors_index]
            anchor_vectors_index += 1
            weights = params[0]
            bias = params[1]
            assert set_anchor_vector.shape == weights.shape, 'Anchor Vec Shape: %s, Weights Shape: %s' % (set_anchor_vector.shape, weights.shape)
            # Does not matter if it is a convolution or fully connected layer.
            model.layers[i].set_weights([set_anchor_vector, bias])
