from sentinelhub import BBox, CRS, bbox_to_resolution
import rasterio
import rasterio.features
import geopandas as gpd
import numpy as np
import numpy.ma as ma
from shapely.geometry import Point
import sys

from skimage.morphology import closing
from skimage.morphology import disk
from skimage.measure import label

def get_bbox(polygon, inflate_bbox=0.1):
    """
    Determines the BBOX from polygon. BBOX is inflated in order to include polygon's surroundings. 
    """
    minx, miny, maxx, maxy = polygon.bounds
    delx=maxx-minx
    dely=maxy-miny

    minx=minx-delx*inflate_bbox
    maxx=maxx+delx*inflate_bbox
    miny=miny-dely*inflate_bbox
    maxy=maxy+dely*inflate_bbox
    
    return BBox(bbox=[minx, miny, maxx, maxy], crs=CRS.WGS84)

def get_optimal_resolution(bbox):
    """
    Determines the optimal resolution of the image:
        * best resolution that still produces an image smaller than 5000x5000 pixels
    """
    x_pxs, y_pxs = bbox_to_resolution(bbox, width=1, height=1)

    resx = (int((x_pxs-1)/50000)+1)*10
    resy = (int((y_pxs-1)/50000)+1)*10
    return resx, resy

def get_optimal_cloud_resolution(res_x=10, res_y=10):
    """
    Determines the optimal resolution for cloud detection:
        * 80m x 80m or worse
    """
    cloud_res_x = 80 if res_x < 80 else res_x
    cloud_res_y = 80 if res_y < 80 else res_y
    
    return cloud_res_x, cloud_res_y

def get_simplified_poly(poly, simpl_fact = 0.0, simpl_step = 0.0001, threshold=20000):
    """
    Simplifies the polygon. Reduces the number of vertices.
    """
    while len(poly.wkt) > threshold:
        poly = poly.simplify(simpl_fact, preserve_topology=False)
        simpl_fact += simpl_step
            
    return poly
    
def get_water_extent(water_mask, dam_poly, dam_bbox, simplify=True):
    """
    Returns the polygon of measured water extent.
    """
    src_transform = rasterio.transform.from_bounds(*dam_bbox.get_lower_left(),
                                                   *dam_bbox.get_upper_right(),
                                                   width=water_mask.shape[1],
                                                   height=water_mask.shape[0])
        
    # do vectorization of raster mask
    results = ({'properties': {'raster_val': v}, 'geometry': s} 
               for i, (s, v) in enumerate(rasterio.features.shapes(water_mask, transform=src_transform)) if v==1)
    
    geoms = list(results)
    if len(geoms)==0:
        return Point(0,0), 0, 0

    gpd_polygonized_raster = gpd.GeoDataFrame.from_features(geoms)
    intrscts_idx = gpd_polygonized_raster.index[(gpd_polygonized_raster.intersects(dam_poly)==True)] 
    
    measured_water_extent = gpd_polygonized_raster.loc[intrscts_idx].cascaded_union
    measured_water_extent = measured_water_extent.buffer(0)
    
    if simplify:
        measured_water_extent = get_simplified_poly(measured_water_extent, 0.0, 0.0001, min(100000, len(dam_poly.wkt)*100))
    
    return measured_water_extent

def get_raster_mask(dam_poly, dam_bbox, width, height):
    """
    Burns the dam's nominal water extent to raster.
    """
    dst_transform = rasterio.transform.from_bounds(*dam_bbox, width=width, height=height)
    raster = np.zeros((height, width), dtype=np.uint8)
    rasterio.features.rasterize([(dam_poly.buffer(0), 1)], out=raster, transform=dst_transform, dtype=np.uint8)
    return raster

def apply_DEM_veto(dem, dam_nominal, dam_current, dam_bbox, resx, resy, dem_threshold=15, simplify=True):
    """
    Applies veto to measured water extent based on Digital Eleveation Model (DEM) data. Regions of detected water above 15 meters
    above mean dem height of the lake are excluded.
    """
    wb_nominal = get_raster_mask(dam_nominal, dam_bbox, dem.shape[1], dem.shape[0])
    wb_current = get_raster_mask(dam_current, dam_bbox, dem.shape[1], dem.shape[0])
    
    dem_masked = ma.masked_array(dem, mask=np.logical_not(wb_nominal))
    
    dem_valid = dem<ma.mean(dem_masked)+dem_threshold
    dem_valid = np.logical_or(dem_valid, wb_nominal)
    
    wb_current = np.logical_and(dem_valid, wb_current)
    
    return get_water_extent(wb_current.astype(np.uint8), dam_nominal, dam_bbox, simplify)