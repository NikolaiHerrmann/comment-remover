
import os
import numpy as np
import tensorflow as tf
import random
import matplotlib.pyplot as plt

SEED = 42
FIGURE_PATH = "figs"

def set_seed():
    """Set same set for all libraries
    """
    os.environ['PYTHONHASHSEED'] = str(SEED)
    random.seed(SEED)
    np.random.seed(SEED)
    tf.random.set_seed(SEED)

set_seed()


def save_figure(title, fig=None, fig_dir=FIGURE_PATH, show=False, pdf=True, 
                png=True, dpi=400, transparent=True):
    """Save a matplotlib figure

    :param title: filename
    :param fig: figure to save, defaults to None
    :param fig_dir: directory to save in, defaults to FIGURE_PATH
    :param show: where to call plt.show() from matplotlib, defaults to False
    :param pdf: whether to make a pdf plot, defaults to True
    :param png: whether to make a png plot, defaults to True
    :param dpi: resolution of png images, defaults to 400
    :param transparent: whether to have the background as transparent, defaults to True
    """
    if not fig:
        fig = plt.gcf()
    if png:
        fig.savefig(os.path.join(fig_dir, title + ".png"), dpi=dpi, bbox_inches="tight", transparent=transparent)
    if pdf:
        fig.savefig(os.path.join(fig_dir, title + ".pdf"), dpi=dpi, bbox_inches="tight", transparent=transparent)
    if show:
        plt.show()