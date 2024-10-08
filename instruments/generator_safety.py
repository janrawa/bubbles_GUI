from numpy import array, mean, searchsorted, any, iinfo, int64
from numpy.typing import ArrayLike

from scipy.fft import fftfreq, fft
from scipy.signal import find_peaks  # For advanced smoothing

def clip(x:float, vmin:float, vmax:float) -> float:
    return max(vmin, min(x, vmax))

def find_argpeaks_around_f(xf:ArrayLike, yf:ArrayLike, f:float, threshold: float) -> int:
    """Detects peaks in +- 5% range around specified freaquency.
    Becouse of distance parameter of find_peaks beeing equal to 
    argrange:
    This function should return only ONE peak or infinity.

    Args:
        xf (ArrayLike): frequency values - sorted
        yf (ArrayLike): signal spectrum
        f  (float):     approximate peak frequency
        threshold (float, optional): threshold value used in scipy.signal.find_peaks. Defaults to .25.

    Returns:
        int: index of peak
    """    
    argrange = (
        searchsorted(xf, f * 0.95),  # 95% of f
        searchsorted(xf, f * 1.05)   # 105% of f
    )

    # becouse of distance, find_peaks should always
    # find one peak - the tallest one
    argpeaks = find_peaks(yf[argrange[0]: argrange[1]],
                          distance=argrange[1]-argrange[0],
                          threshold=threshold,)[0] + argrange[0]
    
    if len(argpeaks) == 0:
        return iinfo(int64).max
    else:
        return argpeaks[0]

def subharmonic_detected(xf:ArrayLike, yf:ArrayLike, f0:float, threshold: float) -> bool:
    """If any subharmonic detected return true
    if none detected return false.

    Args:
        xf (ArrayLike): frequency values - sorted
        yf (ArrayLike): signal spectrum
        f0 (float):     generator frequency

    Returns:
        bool: truth value of detected peak
    """
    
    argpeaks_detected=array([
        find_argpeaks_around_f(xf, yf, 3/2*f0, threshold),
        find_argpeaks_around_f(xf, yf, 5/2*f0, threshold),
    ])
    
    argpeaks=array([
        searchsorted(xf, 3/2*f0),
        searchsorted(xf, 5/2*f0),
    ])

    distance=abs(argpeaks_detected - argpeaks)

    return bool(any(distance < 8))

def calculate_voltage(v0 : float, xf: ArrayLike, yf_mag: ArrayLike, f0: float, threshold: float) -> float:
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

    subharmonics=subharmonic_detected(xf, yf_mag, f0, threshold)

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
    def __init__(self, window_length : int, threshold:float=100) -> None:
        """Regulates generator voltage

        Args:
            window_length (int): number of signal samples - used for averaging of signal
        """
        self.signalRegister   = RollingRegister(window_length)
        self.threshold         = threshold
    
    def updateAmplitude(self, v0 : float, f0 : float,
                        sample_rate : float) -> float:
        """Calculates new voltage peak to peak based on the old one. With all safety features included.

        Args:
            sample_rate (float): sample rate of signals stored in register.
            v0 (float): vpp of generator ouput
            f0 (float): frequency of generator ouput

        Returns:
            float: calculated new vpp
        """

        if len(self.signalRegister) < 2:
            return v0
        
        y=array(self.signalRegister)
        xf=fftfreq(y.shape[1], 1/sample_rate)[:y.shape[1]//2]
        yf=abs(fft(y, axis=1))[:, :y.shape[1]//2]
        mean_yf = mean(yf, axis=0)

        return calculate_voltage(v0, xf, mean_yf, f0, self.threshold)
