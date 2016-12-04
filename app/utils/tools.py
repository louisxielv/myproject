import datetime
import os
import random


def gen_rnd_filename(filename):
    fname, fext = os.path.splitext(filename)
    filename_prefix = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    return '{}{}{}'.format(filename_prefix, str(random.randrange(10000, 100000)), fext)
