from enum import Enum
from recordclass import recordclass
from datetime import datetime

class WaterDetectionSensor(Enum):
    S2_NDWI = 'S2_NDWI'
    S2_NDWI_DEM = 'S2_NDWI_DEM'
    S1_VH_DB = 'S1_VH_DB'
    
class WaterDetectionStatus(Enum):
    UNKNOWN_ERROR = -1
    MEASUREMENT_VALID = 1
    INVALID_DATA = 2
    TOO_CLOUDY = 3
    SH_REQUEST_ERROR = 4
    SH_NO_DATA = 5
    SH_NO_CLOUD_DATA = 6
    INVALID_POLYGON = 7

Measurement = recordclass('SurfaceWaterLevelMeasurement', 
                          ['BLUEDOT_WB_ID', 
                          'BLUEDOT_MEAS_DATE', 'SAT_IMAGE_DATE', 'SENSOR_TYPE',
                          'MEAS_STATUS', 'MEAS_ALG_VER',
                          'CLOUD_COVERAGE', 'SURF_WATER_LEVEL', 'CC_ORIG', 'CC_CLEAN', 'ALG_STATUS', 'GEOMETRY', 'S3_IMAGE_URL'])

def get_new_measurement_entry(dam_id, date, sensor, version):
    return Measurement(BLUEDOT_WB_ID = dam_id, 
                       BLUEDOT_MEAS_DATE = datetime.today().strftime('%Y-%m-%d'),
                       SAT_IMAGE_DATE = date.strftime('%Y-%m-%d'),
                       SENSOR_TYPE = sensor.value,
                       MEAS_STATUS = WaterDetectionStatus.UNKNOWN_ERROR.value,
                       MEAS_ALG_VER = version,
                       CLOUD_COVERAGE = 1.0,
                       SURF_WATER_LEVEL = 0.0,
                       CC_ORIG = 0,
                       CC_CLEAN = 0,
                       ALG_STATUS = -1,
                       GEOMETRY = 'POINT (0 0)',
                       S3_IMAGE_URL = 'none')

def copy_measurement(measurement):
    return Measurement(BLUEDOT_WB_ID = measurement.BLUEDOT_WB_ID, 
                       BLUEDOT_MEAS_DATE = measurement.BLUEDOT_MEAS_DATE, 
                       SAT_IMAGE_DATE = measurement.SAT_IMAGE_DATE, 
                       SENSOR_TYPE = measurement.SENSOR_TYPE,
                       MEAS_STATUS = measurement.MEAS_STATUS, 
                       MEAS_ALG_VER = measurement.MEAS_ALG_VER,
                       CLOUD_COVERAGE = measurement.CLOUD_COVERAGE, 
                       SURF_WATER_LEVEL = measurement.SURF_WATER_LEVEL, 
                       CC_ORIG = measurement.CC_ORIG,
                       CC_CLEAN = measurement.CC_CLEAN,
                       ALG_STATUS = measurement.ALG_STATUS, 
                       GEOMETRY = measurement.GEOMETRY, 
                       S3_IMAGE_URL = measurement.S3_IMAGE_URL)

def set_measurement_status(measurement, status):
    measurement.MEAS_STATUS = status.value
    
