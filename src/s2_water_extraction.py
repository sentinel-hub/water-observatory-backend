import numpy as np
import numpy.ma as ma

from sentinelhub import WcsRequest, MimeType, CustomUrlParam
from sentinelhub import DownloadFailedException
from sentinelhub.download import ImageDecodingError
from s2cloudless import CloudMaskRequest

from skimage.filters import threshold_otsu
from skimage.feature import canny
from skimage.morphology import disk, binary_dilation

from geom_utils import get_water_extent, get_optimal_resolution, get_optimal_cloud_resolution
from geom_utils import get_bbox, apply_DEM_veto, get_simplified_poly

from sh_requests import get_optical_data, get_S2_dates, get_S2_request, get_DEM_request, get_S2_wmsrequest

from definitions import Measurement, WaterDetectionSensor, WaterDetectionStatus, get_new_measurement_entry, set_measurement_status, copy_measurement

from datetime import datetime, timedelta

from shapely.wkt import loads
import sys
import gc

from tqdm import tqdm_notebook as tqdm

S2_WATER_DETECTOR_VERSION = 'v.0.2'
S2_MAX_CC = 0.5
S2_MIN_VALID_FRACTION = 0.98
S2_MAX_CLOUD_COVERAGE = 0.20
S2_CLOUD_BANDS_SCRIPT = 'return [B01,B02,B04,B05,B08,B8A,B09,B10,B11,B12]'

def get_water_mask_from_S2(ndwi, canny_sigma=4, canny_threshold=0.3, selem=disk(4)):
    """
    Make water detection on input NDWI single band image.
    
    """
    # default threshold (no water detected)
    otsu_thr = 1.0
    status = 0
    
    # transform NDWI values to [0,1]
    ndwi_std = (ndwi - np.min(ndwi))/np.ptp(ndwi)
    
    if len(np.unique(ndwi)) > 1:
        edges = canny(ndwi_std, sigma=canny_sigma, high_threshold=canny_threshold)
        edges = binary_dilation(edges, selem)
        ndwi_masked = ma.masked_array(ndwi, mask=np.logical_not(edges))
        
        if len(np.unique(ndwi_masked.data[~ndwi_masked.mask])) > 1:
            # threshold determined using dilated canny edge + otsu
            otsu_thr = threshold_otsu(ndwi_masked.data[~ndwi_masked.mask])
            status = 1

            # if majority of pixels above threshold have negative NDWI values
            # change the threshold to 0.0
            fraction = np.count_nonzero(ndwi>0)/np.count_nonzero(ndwi>otsu_thr)
            if fraction < 0.9:
                otsu_thr = 0.0
                status = 3
        else:
            # theshold determined with otsu on entire image
            otsu_thr = threshold_otsu(ndwi)
            status = 2
            
            # if majority of pixels above threshold have negative NDWI values
            # change the threshold to 0.0
            fraction = np.count_nonzero(ndwi>0)/np.count_nonzero(ndwi>otsu_thr)
            if fraction < 0.9:
                otsu_thr = 0.0
                status = 4

    return status, (ndwi>otsu_thr).astype(np.uint8)

def get_water_level_optical(timestamp, ndwi, dam_poly, dam_bbox, simplify=True):
    """
    Run water detection algorithm for an NDWI image.
    """
    water_det_status, water_mask = get_water_mask_from_S2(ndwi)
    measured_water_extent = get_water_extent(water_mask, dam_poly, dam_bbox, simplify)
    
    return {'alg_status':water_det_status,
            'water_level':measured_water_extent.area/dam_poly.area,
            'geometry':measured_water_extent}

def extract_surface_water_area_per_frame(dam_id, dam_poly, dam_bbox, date, resx, resy):
    """
    Run water detection algorithm for a single timestamp.
    """
    measurement = get_new_measurement_entry(dam_id, date, WaterDetectionSensor.S2_NDWI, S2_WATER_DETECTOR_VERSION)
    
    # initialise requests
    try:
        wcs_ndwi_request = WcsRequest(layer='NDWI', bbox=dam_bbox, time=date.strftime('%Y-%m-%d'), maxcc=S2_MAX_CC,
                                      resx=f'{resx}m', resy=f'{resy}m', image_format=MimeType.TIFF_d32f, 
                                      time_difference=timedelta(hours=2),
                                      custom_url_params={CustomUrlParam.SHOWLOGO: False,
                                                         CustomUrlParam.TRANSPARENT: True})

        cloudresx, cloudresy = get_optimal_cloud_resolution(resx, resy)   
        wcs_bands_request = WcsRequest(layer='NDWI', bbox=dam_bbox, time=date.strftime('%Y-%m-%d'), maxcc=S2_MAX_CC,
                                       resx=f'{cloudresx}m', resy=f'{cloudresy}m', image_format=MimeType.TIFF_d32f,
                                       time_difference=timedelta(hours=2),
                                       custom_url_params={CustomUrlParam.EVALSCRIPT: S2_CLOUD_BANDS_SCRIPT})

    except (RuntimeError, DownloadFailedException):
        set_measurement_status(measurement, WaterDetectionStatus.SH_REQUEST_ERROR)
        return measurement
     
    # download NDWI
    try:
        ndwi = np.asarray(wcs_ndwi_request.get_data())
    except (DownloadFailedException, ImageDecodingError):
        set_measurement_status(measurement, WaterDetectionStatus.SH_REQUEST_ERROR)
        return measurement

    if len(ndwi)==0:
        set_measurement_status(measurement, WaterDetectionStatus.SH_NO_DATA)
        return measurement
    
    # check that image has no INVALID PIXELS
    valid_pxs_frac = np.count_nonzero(ndwi[...,1])/np.size(ndwi[...,1])
    if valid_pxs_frac < S2_MIN_VALID_FRACTION:
        del ndwi
        set_measurement_status(measurement, WaterDetectionStatus.INVALID_DATA)
        return measurement

    # run cloud detection
    try:
        all_cloud_masks = CloudMaskRequest(ogc_request=wcs_bands_request, threshold=0.4)
        cloud_mask = all_cloud_masks.get_cloud_masks()
    except (DownloadFailedException, ImageDecodingError):
        set_measurement_status(measurement, WaterDetectionStatus.SH_REQUEST_ERROR)
        return measurement

    if len(ndwi)==0:
        set_measurement_status(measurement, WaterDetectionStatus.SH_NO_CLOUD_DATA)
        return measurement
          
    # check cloud coverage
    cloud_cov = np.count_nonzero(cloud_mask)/np.size(cloud_mask)
    if cloud_cov > S2_MAX_CLOUD_COVERAGE:
        del cloud_mask, all_cloud_masks
        set_measurement_status(measurement, WaterDetectionStatus.TOO_CLOUDY)
        return measurement
  
    measurement.CLOUD_COVERAGE = cloud_cov
    try:
        # run water detction algorithm
        result = get_water_level_optical(date, ndwi[0,...,0], dam_poly, dam_bbox, simplify=True)
        
        set_measurement_status(measurement, WaterDetectionStatus.MEASUREMENT_VALID)
        measurement.SURF_WATER_LEVEL = result['water_level']
        measurement.GEOMETRY = result['geometry'].wkt
        measurement.ALG_STATUS = result['alg_status']
        
        del result
    except AttributeError:
        set_measurement_status(measurement, WaterDetectionStatus.INVALID_POLYGON)
    
    del ndwi, cloud_mask, all_cloud_masks, wcs_ndwi_request, wcs_bands_request 
    
    return measurement

def surface_water_area_with_dem_veto(measurement, the_dam_nominal, the_dam_bbox, resx, resy, dem_threshold):
    water_level_dem = copy_measurement(measurement)
    
    try:
        dam_vetoed = apply_DEM_veto(get_optical_data(get_DEM_request(the_dam_bbox, resx, resy)),
                                    the_dam_nominal, loads(measurement.GEOMETRY), the_dam_bbox, resx, resy, 
                                    dem_threshold, simplify=True)
        water_level_dem.SURF_WATER_LEVEL = dam_vetoed.area/the_dam_nominal.area
        water_level_dem.GEOMETRY = dam_vetoed.wkt
        del dam_vetoed
    except (DownloadFailedException, ImageDecodingError):
        set_measurement_status(water_level_dem, WaterDetectionStatus.SH_REQUEST_ERROR)
    except AttributeError:
        set_measurement_status(measurement, WaterDetectionStatus.INVALID_POLYGON)
     
    return water_level_dem
