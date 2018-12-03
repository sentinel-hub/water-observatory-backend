from sentinelhub import BBox
from sentinelhub import WcsRequest, WmsRequest
from sentinelhub import MimeType, CustomUrlParam, DataSource
from sentinelhub import SHConfig
import numpy as np
from datetime import datetime, timedelta
    
def get_S2_request(layer, dam_bbox, date, resx, resy, maxcc):
    return WcsRequest(data_folder=None,
                      layer=layer,
                      bbox=dam_bbox, 
                      time=date.strftime('%Y-%m-%d') if isinstance(date, datetime) else date, 
                      resx=f'{resx}m', resy=f'{resy}m',
                      image_format=MimeType.TIFF_d32f,
                      maxcc=maxcc,
                      time_difference=timedelta(hours=2),
                      custom_url_params={CustomUrlParam.SHOWLOGO: False})

def get_S2_wmsrequest(layer, dam_bbox, date, width, height, maxcc):
    return WmsRequest(data_folder=None,
                      layer=layer,
                      bbox=dam_bbox, 
                      time=date.strftime('%Y-%m-%d') if isinstance(date, datetime) else date, 
                      width=width, height=height,
                      image_format=MimeType.TIFF_d32f,
                      maxcc=maxcc,
                      time_difference=timedelta(hours=2),
                      custom_url_params={CustomUrlParam.SHOWLOGO: False})

def get_S2_dates(layer, time_interval, dam_bbox, resx, resy, maxcc):
    date_request = get_S2_request(layer, dam_bbox, time_interval, resx=resx, resy=resy, maxcc=maxcc)
    return date_request.get_dates()

def get_optical_data(request):
    return np.asarray(request.get_data())[0]

def get_DEM_request(dam_bbox, resx, resy):
    return WcsRequest(data_source=DataSource.DEM,
                      layer='DEM',
                      resx=f'{resx}m', resy=f'{resy}m',
                      bbox=dam_bbox,
                      image_format=MimeType.TIFF_d32f,
                      custom_url_params={CustomUrlParam.SHOWLOGO: False})

