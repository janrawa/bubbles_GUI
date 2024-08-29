from numpy import array, searchsorted, sum, abs

def clip(x, vmin, vmax):
    return max(vmin, min(x, vmax))

def subharmonics_present(xf: array, yf: array, f0: float):
    # @njit(float64(float64[:], float64[:], float64))
    def close_far_field_integral_fraction(xf: array, yf: array, f: float):
        f_close_arglim = (
            searchsorted(xf, f * 0.95),  # 95% of f
            searchsorted(xf, f * 1.05)   # 105% of f
        )

        f_far_arglim = (
            searchsorted(xf, f * 0.9),  # 90% of f
            searchsorted(xf, f * 1.1)   # 110% of f
        )

        # Sum close field
        f_close_sum = sum(yf[f_close_arglim[0]:f_close_arglim[1]])
        
        # Sum far field by concatenating slices
        f_far_sum   = sum(yf[f_far_arglim[0]:f_far_arglim[1]])

        # multiplied by 2 becouse close range is 10% and far range is 20%
        return 2*f_close_sum / f_far_sum
    
    peak32=close_far_field_integral_fraction(xf, abs(yf), 3/2 * f0)
    peak52=close_far_field_integral_fraction(xf, abs(yf), 5/2 * f0)
    
    return {
        '3/2f0':(peak32, peak32>1.05), # detection threshold set by experimentation
        '5/2f0':(peak52, peak52>1.2),  # detection threshold set by experimentation
    }