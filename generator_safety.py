from numpy import searchsorted, sum, abs
from numpy.typing import ArrayLike

from scipy.signal import savgol_filter  # For advanced smoothing


def clip(x, vmin, vmax):
    return max(vmin, min(x, vmax))

def subharmonics_present(xf: ArrayLike, yf_mag: ArrayLike, f0: float):
    def close_far_field_integral_fraction(xf: ArrayLike, yf_mag: ArrayLike, f: float):
        f_close_arglim = (
            searchsorted(xf, f * 0.95),  # 95% of f
            searchsorted(xf, f * 1.05)   # 105% of f
        )

        f_far_arglim = (
            searchsorted(xf, f * 0.9),  # 90% of f
            searchsorted(xf, f * 1.1)   # 110% of f
        )

        # Sum close field
        f_close_sum = sum(yf_mag[f_close_arglim[0]:f_close_arglim[1]])
        
        # Sum far field by concatenating slices
        f_far_sum   = sum(yf_mag[f_far_arglim[0]:f_far_arglim[1]])

        # multiplied by 2 becouse close range is 10% and far range is 20%
        return 2*f_close_sum / f_far_sum
    
    yf_mag = savgol_filter(yf_mag, window_length=51, polyorder=2)

    peak32=close_far_field_integral_fraction(xf, yf_mag, 3/2 * f0)
    peak52=close_far_field_integral_fraction(xf, yf_mag, 5/2 * f0)
    
    return {
        '3/2f0':(peak32, peak32>0.95), # detection threshold set by experimentation
        '5/2f0':(peak52, peak52>1.0),  # detection threshold set by experimentation
    }

def calculate_voltage(v0 : float, xf: ArrayLike, yf: ArrayLike, f0: float):
    def raw_change(xf: ArrayLike, yf: ArrayLike, f0: float):
        dv = 0.02 # voltage change

        subharmonics=subharmonics_present(xf, yf, f0)

        # subharmonics present -> drop voltage
        if True in subharmonics.items():
            return -dv
        else:
            return +dv
    
    dv=raw_change(xf, yf, f0)
    return clip(v0+dv, 0.020, 2.0) # min voltage 20 mV, max voltage 2 V