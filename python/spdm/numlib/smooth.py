import typing
import numpy as np

from spdm.utils.logger import logger
from spdm.utils.type_hint import array_type
from spdm.numlib.interpolate import interpolate
from spdm.core.expression import Expression


def smooth(x, window_len=11, window="hanning"):
    """smooth the data using a window with requested size.

    This method is based on the convolution of a scaled window with the signal.
    The signal is prepared by introducing reflected copies of the signal
    (with the window size) in both ends so that transient parts are minimized
    in the begining and end part of the output signal.

    input:
        x: the input signal
        window_len: the dimension of the smoothing window; should be an odd integer
        window: the type of window from 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'
            flat window will produce a moving average smoothing.

    output:
        the smoothed signal

    example:

    t=linspace(-2,2,0.1)
    x=sin(t)+randn(len(t))*0.1
    y=smooth(x)

    see also:

    numpy.hanning, numpy.hamming, numpy.bartlett, numpy.blackman, numpy.convolve
    scipy.signal.lfilter

    TODO: the window parameter could be the window itself if an array instead of a string
    NOTE: length(output) != length(input), to correct this: return y[(window_len/2-1):-(window_len/2)] instead of just y.

    @ref: https://scipy-cookbook.readthedocs.io/items/SignalSmooth.html
    """

    if x.ndim != 1:
        raise ValueError("smooth only accepts 1 dimension arrays.")

    if x.size < window_len:
        raise ValueError("Input vector needs to be bigger than window size.")

    if window_len < 3:
        return x

    if not window in ["flat", "hanning", "hamming", "bartlett", "blackman"]:
        raise ValueError("Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'")

    s = np.r_[x[window_len - 1 : 0 : -1], x, x[-2 : -window_len - 1 : -1]]

    if window == "flat":  # moving average
        w = np.ones(window_len, "d")
    else:
        w = eval("np." + window + "(window_len)")

    res = np.convolve(w / w.sum(), s, mode="same")[window_len - 1 : -window_len + 1]
    return res


def smooth_1d(x, y, i_begin=0, i_end=None, **kwargs):
    dy = interpolate(x, y).derivative()(x)
    dy[i_begin:i_end] = smooth(dy[i_begin:i_end], **kwargs)
    y_new = interpolate(x, dy).antiderivative()(x) + y[0]
    return y_new


def rms_residual(a, b):
    return np.abs((a - b) / (a + b) * 2) * 100


from scipy.signal import savgol_filter


class SmoothOp(Expression):
    def __init__(self, op, *args, **kwargs) -> None:
        super().__init__(op or savgol_filter, *args, options=kwargs)

    def __eval__(self, y: array_type, *args, **kwargs) -> typing.Any:
        if len(args) + len(kwargs) > 0:
            logger.warning(f"Ignore {args} {kwargs}")

        return self._op(y, **self._kwargs.get("options", {}))

    def __call__(self, *args, **kwargs):
        if len(args) + len(kwargs) > 0:
            return super().__call__(*args, **kwargs)
        else:
            return self.__eval__(*self._children)


# def smooth(expr, *args, op=None, **kwargs):
#     if isinstance(expr, array_type):
#         return SmoothOp(op, expr, *args, **kwargs)()
#     else:
#         return SmoothOp(op, expr, *args, **kwargs)
