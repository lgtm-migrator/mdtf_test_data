""" Collection of tools to coarsen model data """

__all__ = ["construct_rect_grid", "regrid_lat_lon_dataset"]

import warnings

import numpy as np
import xarray as xr
import xesmf as xe


def construct_rect_grid(dlon, dlat):
    """Generate a rectilinear grid based on values of dx and dy

    Parameters
    ----------
    dlon : float
        Grid spacing in the x-dimension (longitude)
    dlat : float
        Grid spacing in the y-dimension (latitude)

    Returns
    -------
    xarray.Dataset
        Empty shell dataset with lat and lon dimensions
    """

    if 180.0 % dlat != 0:
        dlat = 180.0 / np.floor(180.0 / dlat)
        warnings.warn(
            f"180 degrees does not divide evenly by dlat. Adjusting dlat to {dlat}"
        )

    if 360.0 % dlon != 0:
        dlon = 360.0 / np.floor(360.0 / dlon)
        warnings.warn(
            f"360 degrees does not divide evenly by dlon. Adjusting dlon to {dlon}"
        )

    lat = np.arange(-90.0 + (dlat / 2.0), 90.0, dlat)
    lon = np.arange(0.0 + (dlon / 2.0), 360.0, dlon)

    dset = xr.Dataset(
        {
            "lat": (["lat"], lat),
            "lon": (["lon"], lon),
        }
    )

    return dset


def regrid_lat_lon_dataset(dset, dlon=10.0, dlat=10.0, method="bilinear"):
    """Regrids xarray dataset to a standard lat-lon grid

    Parameters
    ----------
    dset : xarray.Dataset
        Input dataset.  Must have horizonatal dimensions of "lat" and "lon"
    dlon : float, optional
        Grid spacing in the x-dimension (longitude)
    dlat : float, optional
        Grid spacing in the y-dimension (latitude)
    method : str, optional
        xESMF regridding option, by default "bilinear"

    Returns
    -------
    xarray.Dataset
        Regridded data set
    """

    # Define output grid.
    dset_out = construct_rect_grid(dlon=dlon, dlat=dlat)

    # Create xESMF regridder object
    regridder = xe.Regridder(dset, dset_out, method)

    # Loop over variables
    for var in list(dset.variables):
        _dim = list(dset[var].dims)
        if "lat" in _dim and "lon" in _dim:
            _regridded = regridder(dset[var])
            dset_out[var] = _regridded.astype(dset[var].dtype)
            dset_out[var].attrs = dset[var].attrs
        elif var not in ["lat", "lon"]:
            dset_out[var] = dset[var]

    # Copy coordinate metadata
    dset_out["lat"].attrs = dset["lat"].attrs
    dset_out["lon"].attrs = dset["lon"].attrs

    # Copy dataset metadata
    dset_out.attrs = dset.attrs
    dset_out.attrs["coarsen_method"] = f"xESMF {method}"

    return dset_out
