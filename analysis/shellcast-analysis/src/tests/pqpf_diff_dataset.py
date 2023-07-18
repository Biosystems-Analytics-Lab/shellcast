import pygrib
import os
import rasterio
import geopandas as gpd
import pandas as pd

tiff = 'D:/CGAProjects/shellcast/analysis/data/pqpf/nc\intermediate/tiffs/tp_2022093012f024_1p0.tif'
pts_shp = 'D:/CGAProjects/shellcast/analysis/data/pqpf/nc/inputs/ncdmf_leases_20220310_lambert_thresh.shp'
inches_dict = {'1p0': 1.0, '1p5': 1.5, '2p0': 2.0, '2p5': 2.5, '3p0': 3.0, '3p5': 3.5, '4p0': 4.0}
result_gdf = gpd.GeoDataFrame()
gdf = gpd.read_file(pts_shp)

tiff_dir = os.path.join(os.getcwd(), 'tiff')
for t in os.listdir(tiff_dir):
    print(t.split('.')[0][-3:])
    inches = t.split('.')[0][-3:]
    src = rasterio.open(os.path.join(tiff_dir, t))
    # gdf_q = gdf[gdf['rain_in'] == inches_dict[inches]]
    gdf_q = gdf.loc[gdf['rain_in'] == inches_dict[inches]]
    coords = [(x, y) for x, y in zip(gdf_q['geometry'].x, gdf_q['geometry'].y)]
    # for x in src.sample(coords):
    #     print(x[0])
    gdf_q[f'pqpf_24'] = [x[0] for x in src.sample(coords)]
    print(gdf_q)
    result_gdf = pd.concat([result_gdf, gdf_q])
print(result_gdf)
#     coords = [(x, y) for x, y in zip(gdf_q['geometry'].x, gdf_q['geometry'].y)]
#     gdf_q[f'pqpf_24'] = [x[0] for x in src.sample(coords)]
#     result_gdf = pd.concat([result_gdf, gdf_q])
# print(result_gdf)
# gdf_q = gdf[gdf['rain_in'] == 1]
# print(gdf_q)
# coords = [(x, y) for x, y in zip(gdf_q['geometry'].x, gdf_q['geometry'].y)]
#
# src = rasterio.open(tiff)
# gdf_q[f'pqpf_24'] = [x[0] for x in src.sample(coords)]
# print(gdf_q)
# result_gdf = pd.concat([gdf, gdf_q])
# print(result_gdf)
