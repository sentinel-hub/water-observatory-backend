from sentinelhub import BBox
from sentinelhub import WcsRequest, WmsRequest
from sentinelhub import MimeType, CustomUrlParam, DataSource
from sentinelhub import SHConfig
import numpy as np
from datetime import datetime, timedelta

S2_DEM_SCRIPT_V3 = """
    //VERSION=3
    function setup() {
        return {
            input: [{
                bands: ["DEM"],
            }],
            output: {
                bands: 1,
                sampleType: "FLOAT32"
            }
        };
    }

    function evaluatePixel(sample) {
        return [sample.DEM];
    }
"""

S2_NDWI_SCRIPT_V3 = """
    //VERSION=3
    function setup() {
        return {
            input: [{
                bands: ["B03", "B08", "dataMask"],
            }],
            output: {
                bands: 3,
                sampleType: "FLOAT32"
            }
        };
    }

    function evaluatePixel(sample) {
        return [sample.B03,
                sample.B08,
				sample.dataMask];
    }
"""

S2_TRUECOLOR_SCRIPT_V3 = """
    //VERSION=3
    function setup() {
        return {
            input: [{
                bands: ["B02", "B03", "B04", "dataMask"],
            }],
            output: {
                bands: 4,
                sampleType: "FLOAT32"
            }
        };
    }

    function evaluatePixel(sample) {
        return [2.*sample.B04,
				2.*sample.B03,
                2.*sample.B02,
				sample.dataMask];
    }
"""
    
def get_S2_request(layer, dam_bbox, date, resx, resy, maxcc):
    return WcsRequest(data_folder=None,
                      layer=layer,
                      bbox=dam_bbox, 
                      time=date.strftime('%Y-%m-%d') if isinstance(date, datetime) else date, 
                      resx=f'{resx}m', resy=f'{resy}m',
                      image_format=MimeType.TIFF_d32f,
                      maxcc=maxcc,
                      time_difference=timedelta(hours=2),
                      custom_url_params={CustomUrlParam.EVALSCRIPT: S2_NDWI_SCRIPT_V3 if layer == 'NDWI' else S2_TRUECOLOR_SCRIPT_V3, CustomUrlParam.SHOWLOGO: False})

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
                      custom_url_params={CustomUrlParam.EVALSCRIPT: S2_DEM_SCRIPT_V3, CustomUrlParam.SHOWLOGO: False})