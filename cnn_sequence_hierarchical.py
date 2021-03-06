#!/usr/bin/env python

'''
THEANO_FLAGS=mode=FAST_RUN,device=gpu,floatX=float32 python cnn_sequence_hierarchical.py
'''

import numpy
from keras.models import Sequential
from keras.layers.core import (
    Dense, Dropout, Activation, Flatten)
from keras.layers.convolutional import Convolution1D, MaxPooling1D
from keras.layers.recurrent import LSTM
from keras.optimizers import SGD
from sklearn.metrics import classification_report
from keras.utils import np_utils
from utils import (
    shuffle, train_val_test_split,
    get_gene_ontology, encode_seq_one_hot)
import sys
import os
from collections import deque

LAMBDA = 24
DATA_ROOT = 'data/cnn/'
MAXLEN = 500

go = get_gene_ontology()
go_model = dict()


def load_data(parent_id, go_id):
    pass


def get_model(
        go_id,
        parent_id,
        level):
    filepath = DATA_ROOT + 'level_' + str(level) + '/' + parent_id + '/' + go_id + '.hdf5'
    if not os.path.exists(filepath):
        return None
    key = parent_id + "_" + go_id
    if key in go_model:
        return go_model[key]
    model = Sequential()

    model.add(Convolution1D(input_dim=20,
                            input_length=MAXLEN,
                            nb_filter=320,
                            filter_length=20,
                            border_mode='valid',
                            activation='relu',
                            subsample_length=1))
    model.add(MaxPooling1D(pool_length=10, stride=10))
    model.add(Dropout(0.25))
    model.add(Convolution1D(nb_filter=32,
                            filter_length=32,
                            border_mode='valid',
                            activation='relu',
                            subsample_length=1))
    model.add(MaxPooling1D(pool_length=8))
    model.add(LSTM(128))
    model.add(Dense(1024))
    model.add(Activation('relu'))
    model.add(Dropout(0.5))
    model.add(Dense(1))
    model.add(Activation('sigmoid'))

    model.compile(
        loss='binary_crossentropy', optimizer='rmsprop', class_mode='binary')
    # Loading saved weights
    print 'Loading weights for ' + parent_id + '-' + go_id
    try:
        model.load_weights(filepath)
    except Exception, e:
        print 'Could not load weights for %s %s %d' % (parent_id, go_id, level)
        return None

    go_model[key] = model
    return model


def get_go_classifier(go_id, level):
    global model_n
    if level < 4:
        for ch_id in go[go_id]['children']:
            model = get_model(ch_id, go_id, level + 1)
            go[ch_id]['model'] = model
            if model is not None:
                get_go_classifier(ch_id, level + 1)
    return go[go_id]


def load_unseen_proteins():
    data = list()
    with open(DATA_ROOT + 'test.txt', 'r') as f:
        for line in f:
            line = line.strip().split()
            prot_id = line[0]
            seq = line[1]
            data.append((prot_id, seq))
    return data


def predict_functions(classifier, seq):
    q = deque()
    q.append(classifier)
    functions = list()
    data = numpy.array([encode_seq_one_hot(seq, maxlen=MAXLEN)])
    while len(q) > 0:
        x = q.popleft()
        ok = True
        for ch_id in x['children']:
            if 'model' in go[ch_id] and go[ch_id]['model']:
                model = go[ch_id]['model']
                pred = model.predict_classes(
                    data,
                    batch_size=1,
                    verbose=0)
                if pred[0][0] == 1:
                    ok = False
                    q.append(go[ch_id])
        if ok:
            functions.append(x['id'])

    return functions


def main(*args, **kwargs):
    try:
        classifier = get_go_classifier('GO:0003674', 0)
        print 'Total number of models %d' % (len(go_model), )
        print 'Loading unseen proteins'
        prots = load_unseen_proteins()
        with open(DATA_ROOT + 'predictions.txt', 'w') as f:
            for prot_id, seq in prots:
                f.write(prot_id)
                functions = predict_functions(classifier, seq)
                for func in functions:
                    f.write(' ' + func)
                f.write('\n')
    except Exception, e:
        print e

if __name__ == '__main__':
    main(*sys.argv)
