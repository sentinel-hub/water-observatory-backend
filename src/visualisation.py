""" Module for visualisation of satellite imagery and water extents. """

from sentinelhub import BBox
from shapely.geometry import MultiPolygon, Polygon
import numpy as np

import matplotlib as mpl
# mpl.use('Agg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import matplotlib.pyplot as plt

from matplotlib import patches, patheffects

import os, sys, gc
from PIL import Image

def draw_outline(o, lw):
    o.set_path_effects([patheffects.Stroke(
        linewidth=lw, foreground='black'), patheffects.Normal()])

def draw_circ(ax, pos, radius, color='white'):
    patch = ax.add_patch(patches.Circle(pos, radius, fill=True, edgecolor=color, color=color, lw=2))
    draw_outline(patch, 4)
    
def draw_poly(ax, poly, color='xkcd:lime', lw=2):
    if poly is None:
        return
    if poly.exterior is None:
        return
    
    x, y = poly.exterior.coords.xy
    xy = np.moveaxis(np.array([x, y]),0,-1)
    patch = ax.add_patch(patches.Polygon(xy, closed=True, edgecolor=color, fill=False, lw=lw))
    draw_outline(patch, 4)

def draw_multi(ax, multi, color='xkcd:lime', lw=2):
    for poly in multi:
        draw_poly(ax, poly, color=color, lw=lw)

def draw_text(ax, xy, txt, sz=14, color='white'):
    text = ax.text(*xy, txt,
        verticalalignment='top', color=color, fontsize=sz, weight='bold')
    draw_outline(text, 1)
    
def plot_water_body(img, date, dam_poly, dam_bbox, water_extent, water_level, clip=0, 
                    color_nominal='white', color_current='xkcd:lime',
                    hide_axis=True, file_name=None, add_text=False):

    shape = img.shape[0:2]
    dpi = 300
    size = [float(i)/dpi*10 for i in shape]
    
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=size)
    #if hide_axis:
    #    ax.set_axis_off()
        
    if clip>0:
        ax.imshow(img,extent=[dam_bbox.min_x,dam_bbox.max_x,dam_bbox.min_y,dam_bbox.max_y],
                  vmin=0, vmax=np.percentile(img,clip))
    else:
        ax.imshow(img,extent=[dam_bbox.min_x,dam_bbox.max_x,dam_bbox.min_y,dam_bbox.max_y])
    
    if isinstance(dam_poly, Polygon):
        draw_poly(ax,dam_poly, color=color_nominal)
    elif isinstance(dam_poly, MultiPolygon):
        draw_multi(ax,dam_poly, color=color_nominal)
        
    if isinstance(water_extent, Polygon):
        draw_poly(ax,water_extent, color=color_current)
    elif isinstance(water_extent, MultiPolygon):
        draw_multi(ax, water_extent, color=color_current)

    if add_text:
        draw_text(ax, (dam_bbox.get_lower_left()[0], dam_bbox.get_upper_right()[1]), f'{date} | {water_level*100: 3.0f}%')
    
    if file_name is not None:
        fig.savefig(file_name, bbox_inches='tight', pad_inches=0, transparent=True, dpi=dpi)
        fig.clf()
        plt.close('all')
    
    del fig, ax
    
def plot_water_body_oo(img, date, dam_poly, dam_bbox, water_extent, water_level, clip=0, 
                        color_nominal='white', color_current='xkcd:lime',
                        hide_axis=True, file_name=None, add_text=False):

    shape = img.shape[0:2]
    dpi = 300
    size = [float(i)/dpi*10 for i in shape]
    
    fig = Figure(figsize=size)
    canvas = FigureCanvas(fig)
    ax = fig.add_subplot(1, 1, 1)

    if hide_axis:
        ax.xaxis.set_major_locator(plt.NullLocator())
        ax.yaxis.set_major_locator(plt.NullLocator())

    if clip>0:
        ax.imshow(img,extent=[dam_bbox.min_x,dam_bbox.max_x,dam_bbox.min_y,dam_bbox.max_y],
                  vmin=0, vmax=np.percentile(img,clip))
    else:
        ax.imshow(img,extent=[dam_bbox.min_x,dam_bbox.max_x,dam_bbox.min_y,dam_bbox.max_y])
    
    if isinstance(dam_poly, Polygon):
        draw_poly(ax,dam_poly, color=color_nominal)
    elif isinstance(dam_poly, MultiPolygon):
        draw_multi(ax,dam_poly, color=color_nominal)
        
    if isinstance(water_extent, Polygon):
        draw_poly(ax,water_extent, color=color_current)
    elif isinstance(water_extent, MultiPolygon):
        draw_multi(ax, water_extent, color=color_current)

    if add_text:
        draw_text(ax, (dam_bbox.get_lower_left()[0], dam_bbox.get_upper_right()[1]), f'{date} | {water_level*100: 3.0f}%')
    
    if file_name is not None:
        canvas.print_figure(file_name, bbox_inches='tight', dpi=dpi, transperent=True)
    
    del fig, ax, canvas    

def resize_image(orig, resized, width, height):
    im_orig = Image.open(orig)
    im_res  = im_orig.resize([width,height], Image.ANTIALIAS)
    im_res.save(resized, "PNG")
    im_res.close()
    im_orig.close()
    del im_res, im_orig
    gc.collect()