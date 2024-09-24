from numpy import mean, searchsorted, sum, abs
from numpy.typing import ArrayLike

from scipy.fft import fftfreq, fft
from scipy.signal import savgol_filter  # For advanced smoothing

from numba import jit, float64, boolean

@jit(float64(float64, float64, float64))
def clip(x:float, vmin:float, vmax:float) -> float:
    return max(vmin, min(x, vmax))

@jit(float64(float64[:], float64[:], float64))
def close_far_field_integral_fraction(xf: ArrayLike, yf_mag: ArrayLike, f: float):
    """Calculates integral of Fourier magnitude (abs(fft(y))) of close and far field.
    Close field is defined as +- 5% around peak frequency,
    far field is defined as +- 10% around peak frequency.

    Args:
        xf (ArrayLike): frequency spectrum
        yf_mag (ArrayLike): Fourier magnitude
        f (float): peak frequency

    Returns:
        float: two times fraction of integrals
    """
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

@jit(boolean(float64[:], float64[:], float64))
def subharmonics_present(xf: ArrayLike, yf_mag: ArrayLike, f0: float):
    """Subharmonics detection function based on close_far_field_integral_fraction method.
    Subharmonics detection values (found in return) are fitted using experimental data.

    Args:
        xf (ArrayLike): frequency spectrum
        yf_mag (ArrayLike): Fourier magnitude
        f0 (float): generator frequency

    Returns:
        bool: are subharmonics 3/2f0 OR 5/2f0 present?
    """
    # yf_mag = savgol_filter(yf_mag, window_length=51, polyorder=2)

    peak32=close_far_field_integral_fraction(xf, yf_mag, 3/2 * f0)
    peak52=close_far_field_integral_fraction(xf, yf_mag, 5/2 * f0)

    return (peak32>0.95) or (peak52>1.0)

@jit(float64(float64, float64[:], float64[:], float64))
def calculate_voltage(v0 : float, xf: ArrayLike, yf_mag: ArrayLike, f0: float) -> float:
    """Calculates new voltage value based on the current voltage and presence of subharmonics.
    Maximum rate of change is dv = 0.02 V. Resoulting voltage is cliped to stay below 2V for savety reasons.

    Args:
        v0 (float): current voltage
        xf (ArrayLike): frequency spectrum
        yf_mag (ArrayLike): Fourier magnitude
        f0 (float): generator frequency

    Returns:
        float: new voltage
    """
    dv = 0.02 # voltage change

    subharmonics=subharmonics_present(xf, yf_mag, f0)

    # subharmonics present -> drop voltage
    if subharmonics == True:
        dv=-dv
    else:
        dv=+dv
    
    return clip(v0+dv, 0.020, 2.0) # min voltage 20 mV, max voltage 2 V

class RollingRegister(list):
    def __init__(self, maxlen : int) -> None:
        """Rolling register based on list. Keeps last maxlen records.
        Used for calculating rolling averedges of past recorded values.

        Args:
            maxlen (int): maximum number of values/objects keps in register
        """
        self._maxlen = maxlen

    @property
    def maxlen(self):
        return self._maxlen

    def append(self, x : ArrayLike) -> None:
        super().append(x)
        if len(self) > self._maxlen:
            super().pop(0)

class AmplitudeRegulator:
    def __init__(self, window_length : int) -> None:
        """Regulates generator voltage

        Args:
            window_length (int): number of signal samples - used for averaging of signal
        """
        self.voltageRegister   = RollingRegister(window_length)
    
    def updateAmplitude(self, sample_rate : float,
                        v0 : float, f0 : float) -> float:
        """Calculates new voltage peak to peak based on the old one. With all safety features included.

        Args:
            sample_rate (float): sample rate of signals stored in register.
            v0 (float): vpp of generator ouput
            f0 (float): frequency of generator ouput

        Returns:
            float: calculated new vpp
        """
        meanSignal=mean(self.voltageRegister, axis=0)

        xf=fftfreq(len(meanSignal), 1/sample_rate)[:len(meanSignal)//2]
        yf=abs(fft(meanSignal))[:len(meanSignal)//2]

        return calculate_voltage(v0, xf, yf, f0)
