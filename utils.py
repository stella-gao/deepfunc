import numpy


def train_val_test_split(labels, data, split=0.8, batch_size=16):
    """This function is used to split the labels and data
    Input:
        labels - array of labels
        data - array of data
        split - percentage of the split, default=0.8\
    Return:
        Three tuples with labels and data
        (train_labels, train_data), (val_labels, val_data), (test_labels, test_data)
    """
    n = len(labels)
    train_n = int((n * split) / batch_size) * batch_size
    val_test_n = int((n - train_n) / 2)

    train_data = data[:train_n]
    train_labels = labels[:train_n]
    train = (train_labels, train_data)

    val_data = data[train_n:][0:val_test_n]
    val_labels = labels[train_n:][0:val_test_n]
    val = (val_labels, val_data)

    test_data = data[train_n:][val_test_n:]
    test_labels = labels[train_n:][val_test_n:]
    test = (test_labels, test_data)

    return (train, val, test)


def shuffle(*args, **kwargs):
    """
    Shuffle list of arrays with the same random state
    """
    seed = None
    if 'seed' in kwargs:
        seed = kwargs['seed']
    rng_state = numpy.random.get_state()
    for arg in args:
        if seed is not None:
            numpy.random.seed(seed)
        else:
            numpy.random.set_state(rng_state)
        numpy.random.shuffle(arg)


def get_gene_ontology():
    # Reading Gene Ontology from OBO Formatted file
    go = dict()
    obj = None
    with open('data/go.obo', 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line == '[Term]':
                if obj is not None:
                    go[obj['id']] = obj
                obj = dict()
                obj['is_a'] = list()
                continue
            elif line == '[Typedef]':
                obj = None
            else:
                if obj is None:
                    continue
                l = line.split(": ")
                if l[0] == 'id':
                    obj['id'] = l[1]
                elif l[0] == 'is_a':
                    obj['is_a'].append(l[1].split(' ! ')[0])
    if obj is not None:
        go[obj['id']] = obj
    for go_id, val in go.iteritems():
        if 'children' not in val:
            val['children'] = list()
        for g_id in val['is_a']:
            if 'children' not in go[g_id]:
                go[g_id]['children'] = list()
            go[g_id]['children'].append(go_id)
    return go