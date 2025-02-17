#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 19 15:11:53 2021

@author: alxneit
"""
import os
import numpy as np
from skimage.measure import profile_line
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import AutoMinorLocator

def create_overlay(images, colors, legends=None, BG_image=None, outfile=None):
    """Plots overlay of `images` with `colors`.

        Parameters
        ----------
           images:  List or tuple.
                    Images to be overlaid (must be of identical shape).
           colors:  List or tuple.
                    List of colors used to overlay the images provided
                    in the same order as `images`. Surplus colors provided
                    are ignored.
          legends:  List or tuple.
                    List of legends used to annotate individual maps in
                    overlay.
         BG_image:  Ndarray.
                    Background image (grey scale). Must be of same shape as
                    `images`.
          outfile:  Str.
                    Plot is saved as `outfile`. Graphics file type is inferred
                    from extension. Available formats might depend on your
                    installation.

        Notes
        -----
                `images` are overlaid in the sequence given. Thus fully saturated
                pixels of only the last image given are visible. Therefore the
                final figure depends on the order of the images given with the
                most important image last.

        Examples
        --------
        >>>> from JEOL_eds import JEOL_pts
        >>>> from JEOL_eds.utils import create_overlay

        # Load data. Data does not contain drift images and all frames were
        # added, thus only a single frame is present.
        >>>> dc = JEOL_pts('data/complex_oxide.h5')

        # Extract some elemental maps. Where possible, dd contribution of
        # several lines.
        >>>> Ti = dc.map(interval=(4.4, 5.1), energy=True)      # Ka,b
        >>>> Fe = dc.map(interval=(6.25, 6.6), energy=True)     # Ka
        >>>> Sr = dc.map(interval=(13.9, 14.4), energy=True)    # Ka
        >>>> Co = dc.map(interval=(6.75, 7.0), energy=True)     # Ka
        >>>> Co += dc.map(interval=(7.5, 7.8), energy=True)     # Kb
        >>>> O = dc.map(interval=(0.45, 0.6), energy=True)

        # Create overlays. Visualize the SrTiO3 base oxide. No legends plotted.
        # File is saved
        >>>> create_overlay((Sr, Ti, O), ('Red', 'Green', 'Blue'),
                            outfile='test.pdf')

        # Focus on the metals as they are plotted last, include legends.
        >>>> create_overlay([O, Sr, Ti],
                            ['Blue', 'Red', 'Green'],
                            legends=['O', 'Sr', 'Ti'])

        # Visualize the CoFeOx distribution using first of the `drift_images`
        # as background. Note that drift images were not stored in the data
        # supplied and this will raise a TypeError.
        >>>> create_overlay([Fe, Co],
                            ['Maroon', 'Violet'],
                            legends=['Fe', 'Co'],
                            BG_image=dc.drift_images[0])

        # Switch plotting order to obtain a slightly better result.
        >>>> create_overlay([Co, Fe],
                            ['Violet', 'Maroon'])

    """
    assert isinstance(images, (list, tuple))
    assert isinstance(colors, (list, tuple))
    assert len(colors) >= len(images)   # Sufficient colors provided
    assert all(image.shape==images[0].shape for image in images)    # all same shape
    if legends:
        assert isinstance(legends,(list, tuple))
        assert len(legends) == len(images)
    if BG_image is not None:
        assert images[0].shape == BG_image.shape
    if outfile:
        ext = os.path.splitext(outfile)[1][1:].lower()
        supported = plt.figure().canvas.get_supported_filetypes()
        assert ext in supported

    # Show background image
    if BG_image is not None:
        plt.imshow(BG_image, cmap='gist_gray')
    # Create overlays. Use fake image `base` with fully saturated color and
    # use real image as alpha channel (transparency)
    base = np.ones_like(images[0])
    for image, color in zip(images, colors):
        # Custom color map that contains only `color` at full saturation
        cmap = LinearSegmentedColormap.from_list("cmap", (color, color))
        alpha = image / image.max()
        plt.imshow(base, cmap=cmap, alpha=alpha,
                   vmin=0, vmax=1)

    # Fine tune plot
    ax = plt.gca()
    ax.set_xticks([])
    ax.set_yticks([])

    # Add legends. Position and font size depends on image size
    if legends:
        isize = images[0].shape[0]
        fontsize = 12
        delta = isize // fontsize
        x = isize + delta
        for i in range(len(images)):
            y = i * delta
            ax.text(x, y, legends[i],
                    size=fontsize,
                    color=colors[i], backgroundcolor='white')

    if outfile:
        plt.savefig(outfile)


def plot_spectrum(s, E_range=None, M_ticks=None,
                  log_y=False, outfile=None, **kws):
    """Plots a nice spectrum

        Parameters
        ----------
                s:  Ndarray.
                    Spectral data which is expected to cover the energy range
                    0.0 < E <= E_max at an resolution of 0.01 keV per data point.
          E_range:  Tuple (E_low, E_high).
                    Energy range to be plotted.
          M_ticks:  Tuple (mx, my).
                    Number of minor ticks used for x and y axis. If you want to
                    plot minor ticks for a single axis, use None for other axis.
                    Parameter for y axis is ignored in logarithmic plots.
            log_y:  Bool.
                    Plot linear or logarithmic y-axis.
          outfile:  Str.
                    Plot is saved as `outfile`. Graphics file type is inferred
                    from extension. Available formats might depend on your
                    installation.

        Examples
        --------
        >>>> from JEOL_eds import JEOL_pts
        >>>> from JEOL_eds.utils import plot_spectrum

        # Load data.
        >>>> dc = JEOL_pts('data/complex_oxide.h5')

        # Plot full reference spectrum with logaritmic y-axis.
        >>>> plot_spectrum(dc.ref_spectrum, log_y=True)

        # Plot and save reference spectrum between 1.0 and 2.5 keV.
        # Plot one minor tick on x-axis and four on y-axis. Pass
        # some keywords to `matplotlib.pyplot.plot()`.
        >>>> plot_spectrum(dc.ref_spectrum,
                           E_range=(1, 2.5),
                           M_ticks=(1,4),
                           outfile='ref_spectrum.pdf',
                           color='Red', linestyle='-.', linewidth=1.0)
    """
    F = 1/100     # Calibration factor (Energy per channel)
    if outfile:
        ext = os.path.splitext(outfile)[1][1:].lower()
        supported = plt.figure().canvas.get_supported_filetypes()
        assert ext in supported

    if E_range is not None:
        E_low, E_high = E_range
        if E_high > s.shape[0] * F: # E_high is out of range
            E_high = s.shape[0] * F
    else:
        E_low, E_high = 0, s.shape[0] * F

    N = int(np.round((E_high - E_low) / F))    # Number of data points
    x = np.linspace(E_low, E_high, N)   # Energy axis
    # Indices corresponding to spectral interval
    i_low = int(np.round(E_low / F))
    i_high = int(np.round(E_high / F))

    plt.plot(x, s[i_low:i_high], **kws)
    ax = plt.gca()
    ax.set_xlabel('E  [keV]')
    ax.set_ylabel('counts  [-]')

    if log_y:
        ax.set_yscale('log')
    # Plot minor ticks on the axis required. Careful: matplotlib specifies the
    # number of intervals which is one more than the number of ticks!
    if M_ticks is not None:
        mx, my = M_ticks
        if mx is not None:
            ax.xaxis.set_minor_locator(AutoMinorLocator(mx + 1))
        if my is not None:
            ax.yaxis.set_minor_locator(AutoMinorLocator(my + 1))

    if outfile:
        plt.savefig(outfile)

def export_spectrum(s, outfile, E_range=None):
    """Exports spectrum as tab delimited ASCII.

        Parameters
        ----------
                s:  Ndarray.
                    Spectral data which is expected to cover the energy range
                    0.0 < E <= E_max at an resolution of 0.01 keV per data point.
          outfile:  Str.
                    Data is saved in `outfile`.
          E_range:  Tuple (E_low, E_high).
                    Energy range to be plotted.

        Examples
        --------
        >>>> from JEOL_eds import JEOL_pts
        >>>> from JEOL_eds.utils import export_spectrum

        # Load data.
        >>>> dc = JEOL_pts('data/complex_oxide.h5')

        # Export full reference spectrum as 'test_spectrum.dat'.
        >>>> export_spectrum(dc.ref_spectrum, 'test_spectrum.dat')

        # Only export data between 1.0 and 2.5 keV.
        >>>> export_spectrum(dc.ref_spectrum, 'test_spectrum.dat',
                             E_range=(1, 2.5))
    """
    F = 1/100     # Calibration factor (Energy per channel)

    if E_range is not None:
        E_low, E_high = E_range
        if E_high > s.shape[0] * F: # E_high is out of range
            E_high = s.shape[0] * F
    else:
        E_low, E_high = 0, s.shape[0] * F

    N = int(np.round((E_high - E_low) / F))    # Number of data points
    data = np.zeros((N, 2))
    data[:, 0] = np.linspace(E_low, E_high, N)   # Energy axis
    # Indices corresponding to spectral interval
    i_low = int(np.round(E_low / F))
    i_high = int(np.round(E_high / F))
    data[:, 1] = s[i_low:i_high]    # copy desired range

    header = '# E [keV]        counts [-]'
    fmt = '%.2f\t%d'
    np.savetxt(outfile, data, header=header, fmt=fmt)


def plot_tseries(ts, M_ticks=None, outfile=None, **kws):
    """Plots a nice time series.

        Parameters
        ----------
               ts:  Ndarray.
                    Time series (integrated x-ray intensities.
          M_ticks:  Tuple (mx, my).
                    Number of minor ticks used for x and y axis. If you want to
                    plot minor ticks for a single axis, use None for other axis.
          outfile:  Str.
                    Plot is saved as `outfile`. Graphics file type is inferred
                    from extension. Available formats might depend on your
                    installation.

        Examples
        --------
        >>>> from JEOL_eds import JEOL_pts
        >>>> from JEOL_eds.utils import plot_tseries

        # Load data.
        >>>> dc = JEOL_pts('data/128.pts', split_frames=True)

        # Get integrated x-ray intensity for carbon Ka peak but exclude
        # frames 11 and 12)
        >>>> frames = list(range(dc.dcube.shape[0]))
        >>>> frames.remove(11)
        >>>> frames.remove(12)
        >>>> ts = dc.time_series(interval=(0.22, 0.34), energy=True, frames=frames)

        # Plot and save time series
        # some keywords to `matplotlib.pyplot.plot()`.
        >>>> plot_tseries(ts,
                          M_ticks=(9,4),
                          outfile='carbon_Ka.pdf',
                          color='Red', linestyle='-.', linewidth=1.0)
    """
    if outfile:
        ext = os.path.splitext(outfile)[1][1:].lower()
        supported = plt.figure().canvas.get_supported_filetypes()
        assert ext in supported

    plt.plot(ts, **kws)
    ax = plt.gca()
    ax.set_xlabel('frame index  [-]')
    ax.set_ylabel('counts  [-]')
    # Plot minor ticks on the axis required. Careful: matplotlib specifies the
    # number of intervals which is one more than the number of ticks!
    if M_ticks is not None:
        mx, my = M_ticks
        if mx is not None:
            ax.xaxis.set_minor_locator(AutoMinorLocator(mx + 1))
        if my is not None:
            ax.yaxis.set_minor_locator(AutoMinorLocator(my + 1))

    if outfile:
        plt.savefig(outfile)

def export_tseries(ts, outfile):
    """Export time series as tab delimited ASCII.

        Parameters
        ----------
               ts:  Ndarray.
                    Time series (integrated x-ray intensities.
          outfile:  Str.
                    Data is saved as `outfile`.

        Examples
        --------
        >>>> from JEOL_eds import JEOL_pts
        >>>> from JEOL_eds.utils import export_tseries

        # Load data.
        >>>> dc = JEOL_pts('data/128.pts', split_frames=True)

        # Get integrated x-ray intensity for carbon Ka peak but exclude
        # frames 11 and 12)
        >>>> frames = list(range(dc.dcube.shape[0]))
        >>>> frames.remove(11)
        >>>> frames.remove(12)
        >>>> ts = dc.time_series(interval=(0.22, 0.34), energy=True, frames=frames)

        # Export time series
        >>>> export_tseries(ts, 'test_tseries.dat')
    """
    N = ts.shape[0]
    data = np.zeros((N, 2))
    data[:, 0] = range(N)
    data[:, 1] = ts

    header = '# Frame idx [-]        counts [-]'
    fmt = '%d\t%d'
    np.savetxt(outfile, data, header=header, fmt=fmt)

def __linewidth_from_data_units(linewidth, axis):
    """Convert a linewidth in pixels to points.

        Parameters
        ----------
        linewidth:  float
                    Linewidth in pixels.
             axis:  matplotlib axis
                    The axis which is used to extract the relevant
                    transformation data (data limits and size must
                    not change afterwards).

        Returns
        -------
        linewidth:  float
                    Linewidth in points.

        Notes
        -----
                    Adapted from https://stackoverflow.com/questions/19394505
    """
    fig = axis.get_figure()
    length = fig.bbox_inches.width * axis.get_position().width
    value_range = np.diff(axis.get_xlim())[0]
    # Convert length to points
    length *= 72    # 72 points per inch
    # Scale linewidth to value range
    return linewidth * (length / value_range)

def show_line(image, line, linewidth=1, outfile=None, **kws):
    """Plots a white (profile) line on image.

        Parameters
        ----------
            image:  Ndarray
                    Image onto which the line will be plotted.
             line:  Tuple (int, int, int, int).
                    Defines line (start_v, start_h, stop_v, stop_h).
        linewidth:  Int
                    Width (pixels) of line to be drawn.
          outfile:  Str
                    Filename, where plot is saved (or None).

        Notes
        -----
                    **kws are only applied to the image plot and not to the line.

        Examples
        --------
        >>>> from JEOL_eds.utils import show_line

        # Define line (10 pixels wide). Verify definition.
        >>>> line = (80, 5, 110, 100)
        >>>> width = 10
        >>>> show_line(C_map, line, linewidth=width, cmap='inferno')
    """
    if outfile:
        ext = os.path.splitext(outfile)[1][1:].lower()
        supported = plt.figure().canvas.get_supported_filetypes()
        assert ext in supported

    ax = plt.imshow(image, **kws)
    x = (line[1], line[3])
    y = (line[0], line[2])
    width = __linewidth_from_data_units(linewidth, ax.axes)
    plt.plot(x,y, color='white', linewidth=width)

    if outfile:
        plt.savefig(outfile)

def get_profile(image, line, linewidth=1):
    """Returns a profile along line on image.

        Parameters
        ----------
            image:  Ndarray.
                    Image onto which the line will be plotted.
             line:  Tuple (int, int, int, int).
                    Defines line (start_v, start_h, stop_v, stop_h).
        linewidth:  Int.

                    Width of profile line (to be integrated).
        Returns
        -------
                    Ndarray
                    Profile, length unit is pixels (as in image).
        Examples
        --------
        >>>> from JEOL_eds import JEOL_pts
        >>>> from JEOL_eds.utils import show_line
        >>>> import matplotlib.pyplot as plt

        # Load data.
        >>>> dc = JEOL_pts('data/128.pts')

        # Carbon map
        >>>> C_map = dc.map(interval=(0.22, 0.34), energy=True)

        # Define line. Verify definition.
        >>>> line = (80, 5, 110, 100)
        >>>> width = 10
        >>>> show_line(C_map, line, linewidth=width, cmap='inferno')

        # Calculate profile along the line (width equals 10 pixels) and
        # plot it.
        >>>> profile = get_profile(C_map, line, linewidth=width)
        >>>> plt.plot(profile)
    """
    profile = profile_line(image,
                           line[0:2], line[2:],
                           linewidth=linewidth,
                           reduce_func=np.sum,
                           mode='nearest')
    return profile

def show_ROI(image, ROI, outfile=None, alpha=0.4, **kws):
    """Plots ROI on image.

        Parameters
        ----------
            image:  Ndarray
                    Image where ROI will be applied.
              ROI:  Tuple
                    If tuple is (int, int) ROI defines point at the
                    intersection of the vertical and horizontal line.
                    If tupe is (int, int, int) ROI defines circle.
                    If tuple is (int, int, int, int) ROI defines rectangle.
          outfile:  Str
                    Filename, where plot is saved (or None)
            alpha:  Float
                    Transparency used to draw background image for ROI [0.4].

        Examples
        --------
        >>>> from JEOL_eds import JEOL_pts
        >>>> from JEOL_eds.utils import show_ROI

        # Load data and create map of total x-ray intensity.
        >>>> dc = JEOL_pts('data/complex_oxide.h5)
        >>>> my_map = dc.map()

        # We want to get the spectrum of the SrTiO3 substrate on the left
        # of the image. Verify definition of rectangular mask. Make image
        # more visible (less transparent). Then plot the spectrum corresponding
        # to the ROI.
        >>>> show_ROI(my_map, (50, 250, 10, 75), alpha=0.6)
        >>>> plot_spectrum(dc.spectrum(ROI=[50, 250, 10, 75]),
                           E_range=(4,17),
                           M_ticks=(4,None))

        # Extract spectrum of the FeCoOx region using a circular mask. Again
        # check the definition of the mask first. Override the default colormap.
        >>>> show_ROI(my_map, (270, 122, 10), cmap='inferno')
        >>>> plot_spectrum(dc.spectrum(ROI=[270, 122, 10]),
                           E_range=(4,17),
                           M_ticks=(4,None))
    """
    if len(ROI) == 2:
        im = image.copy().astype('float')
        im[ROI[0], :] = np.nan
        im[:, ROI[1]] = np.nan
        plt.imshow(im, **kws)
    elif len(ROI) == 3:
        x, y = np.ogrid[:image.shape[0], :image.shape[1]]
        r = np.sqrt((x - ROI[0])**2 + (y - ROI[1])**2)
        mask = r <= ROI[2]
        plt.imshow(image * mask, **kws)         # ROI
        plt.imshow(image, alpha=alpha, **kws)     # transparent image
    elif len(ROI) == 4:
        mask = np.full_like(image, False, dtype='bool')
        mask[ROI[0]:ROI[1], ROI[2]:ROI[3]] = True
        plt.imshow(image * mask, **kws)         # ROI
        plt.imshow(image, alpha=alpha, **kws)     # transparent image
    else:
        raise ValueError(f'Invalid ROI {ROI}.')

    if outfile:
        plt.savefig(outfile)
