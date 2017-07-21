import numpy as np
from mimic3models import nn_utils
from mimic3models import common_utils

def read_chunk(reader, chunk_size):
    data = []
    ys = []
    ts = []
    header = None
    for i in range(chunk_size):
        (X, t, y, header) = reader.read_next()
        data.append(X)
        ts.append(t)
        ys.append(y)
    return (data, ts, ys, header)


def load_data(reader, discretizer, normalizer, small_part=False, pad=False):
    N = reader.get_number_of_examples()
    if (small_part == True):
        N = 1000
    (data, ts, ys, header) = read_chunk(reader, N)
    data = [discretizer.transform(X, end=t)[0] for (X, t) in zip(data, ts)]
    if (normalizer is not None):
        data = [normalizer.transform(X) for X in data]
    ys = np.array(ys, dtype=np.int32)
    if pad:
        return (nn_utils.pad_zeros(data), ys)
    return (data, ys)


class BatchGen(object):

    def __init__(self, reader, discretizer, normalizer,
                 batch_size, small_part):
        self.data = load_data(reader, discretizer, normalizer, small_part)
        self.batch_size = batch_size
        self.steps = len(self.data[0]) // batch_size
        self.generator = self._generator()

    def _generator(self):
        B = self.batch_size
        while True:
            self.data = common_utils.sort_and_shuffle(self.data, B)
            self.data[1] = np.array(self.data[1]) # this is important for Keras
            for i in range(0, len(self.data[0]), B):
                x = self.data[0][i:i+B]
                y = self.data[1][i:i+B]
                yield (nn_utils.pad_zeros(x), y)

    def __iter__(self):
        return self.generator

    def next(self):
        return self.generator.next()

    def __next__(self):
        return self.generator.__next__()
