import dash_leaflet as dl

from pyowm.utils.geo import Point
from pyowm.commons.tile import Tile

'''
Converts latitude and longitude to map tile coordinates.
'''
def get_tile_coords(lat, lon, zoom):
    geopoint = Point(lon, lat)
    tile_x, tile_y = Tile.tile_coords_for_point(geopoint, zoom)
    return tile_x, tile_y

'''
Retrieves coordinates of bounding corners for a given map tile.
'''
def get_tile_bounds(tile_x, tile_y, zoom):
    x1, y1, x2, y2 = Tile.tile_coords_to_bbox(tile_x, tile_y, zoom)
    tile_bounds = [[y1,x1],[y2,x2]]
    return tile_bounds

'''
Loads a weathermap layer for a given tile and map mode.
'''
def get_weathermap_layer(tile_x, tile_y, zoom, api_key, mode='precipitation'):
    img_url = f'https://tile.openweathermap.org/map/{mode}/{zoom}/{tile_x}/{tile_y}.png?appid={api_key}'
    tile_bounds = get_tile_bounds(tile_x, tile_y, zoom)

    return dl.ImageOverlay(url=img_url, bounds=tile_bounds)

'''
Class for managing weather map layers.
'''
class WeatherMap():

    def __init__(self, center, zoom, bounds, owm_key):
        self.center = center
        self.zoom = zoom
        self.bounds = bounds
        self.tile_zoom = zoom
        self.key = owm_key
        self.layers = self.get_layers()
        
    def get_layers(self):
        new_layers = [dl.TileLayer()]

        if not self.bounds:
            self.layers = new_layers
        
        lat1, lon1 = self.bounds[0]
        lat2, lon2 = self.bounds[1]

        p0 = tuple(self.center)
        p1 = (lat1, lon1)
        p2 = (lat1, lon2)
        p3 = (lat2, lon1)
        p4 = (lat2, lon2)

        points = [p0, p1, p2, p3, p4]

        while True:
            tiles = [get_tile_coords(lat, lon, self.tile_zoom) for lat, lon in points]
            unique_tiles = list(set(tiles))

            if len(unique_tiles) <= 2:
                break
            
            self.tile_zoom = self.tile_zoom - 1

        img_layers = [get_weathermap_layer(x, y, self.tile_zoom, self.key) for x,y in unique_tiles]
        new_layers.extend(img_layers)

        return new_layers