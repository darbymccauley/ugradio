"""This module uses the pyrtlsdr package (built on librtlsdr) to interface
to SDR dongles based on the RTL2832/R820T2 chipset."""

from __future__ import print_function
from rtlsdr import RtlSdr
import numpy as np
import time
try:
    import asyncio
except ImportError as e:
    print(e)

SAMPLE_RATE_TOLERANCE = 0.1  # Hz
BUFFER_SIZE = 4096


async def _streaming(nblocks, nsamples):
    data = np.empty((nblocks, nsamples), dtype="complex64")
    count = 0
    async for samples in sdr.stream(num_samples_or_bytes=nsamples):
        data[count] = samples
        count += 1
        if count >= nblocks:
            break

    stop = sdr.stop()
    await stop
    close = sdr.close()
    await close
    return data


def capture_data(
        direct=True,
        center_freq=1420e6,
        nsamples=2048,
        nblocks=1,
        sample_rate=2.2e6,
        gain=0.,
):
    """
    Use the SDR dongle to capture voltage samples from the input. Note that
     the analog system on these devices only lets through signals from 0.5 to
    24 MHz.

    There are two modes (corresponding to the value of direct):
    direct = True: the direct sampling is enabled (no mixing), center_freq does
    not matter and gain probably does not matter. Data returned is real.
    direct = False: use the standard I/Q sampling, center_freq is the LO of the
    mixer. Returns complex data.

    Arguments:
        direct (bool): which mode to use. Default: True.
        center_freq (float): the center frequency in Hz of the downconverter
        (LO of mixer). Ignored if direct == True. Default: 1420e6.
        nsamples (int): number of samples to acquire. Default: 2048.
        nblocks (int): number of blocks of samples to acquire. Default: 1.
        sample_rate (float): sample rate in Hz. Default: 2.2e6.
        gain (float): gain in dB to apply. Probably unnecessary when
        direct == True. Default: 0.

    Returns:
       numpy.ndarray of type float64 (direct == True) or complex64
       (direct == False). Shape is (nblocks, nsamples) when nblocks > 1 or
       (nsamples,) when nblocks == 1.
    """
    sdr = RtlSdr()
    if direct:
        sdr.set_direct_sampling('q')
        sdr.set_center_freq(0)  # turn off the LO
    else:
        sdr.set_direct_sampling(0)
        sdr.set_center_freq(center_freq)
    sdr.set_gain(gain)
    sdr.set_sample_rate(sample_rate)
    _ = sdr.read_samples(BUFFER_SIZE)  # clear the buffer
    if nblocks == 1:
        data = sdr.read_samples(nsamples)
    else:
        loop = asyncio.get_event_loop()
        data = loop.run_until_complete(_streaming(nblocks, nsamples))
   if direct:
       return data.real
   else:
       return data


