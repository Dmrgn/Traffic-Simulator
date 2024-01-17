import pyray as raylib
import math

import overpass
from globals import geocode, buildings
from constants import *
from sect.triangulation import Triangulation
from ground.base import get_context
context = get_context()
Contour, Point, Polygon = context.contour_cls, context.point_cls, context.polygon_cls

class Building:
    x_min = 1e10
    y_min = 1e10
    x_max = -1e10
    y_max = -1e10
    texture = None
    texture_pos = None
    texture_size = None
    def create_building_texture():
        Building.texture_pos = raylib.Vector2(Building.x_min, Building.y_min)
        Building.texture_size = raylib.Vector2(Building.x_max - Building.x_min, Building.y_max - Building.y_min)
        Building.texture = raylib.load_render_texture(int(Building.texture_size.x), int(Building.texture_size.y))

        raylib.begin_texture_mode(Building.texture)
        raylib.clear_background(raylib.Color(0, 0, 0, 0))

        for building in buildings:
            building.draw()

        raylib.end_texture_mode()

    def __init__(self, geometry_object):
        self.triangles = []
        nodes = []
        for node in geometry_object:
            y_offset, x_offset = overpass.geocode_offset(geocode, (node["lat"], node["lon"]))
            pos = raylib.Vector2(x_offset*2, y_offset*2)
            if pos.x < Building.x_min: Building.x_min = pos.x
            if pos.y < Building.y_min: Building.y_min = pos.y
            if pos.x > Building.x_max: Building.x_max = pos.x
            if pos.y > Building.y_max: Building.y_max = pos.y
            nodes.append(pos)
        # raylib can't draw abitrary polygons, so we need to format the vertex data into a list of triangles
        self.triangles = Triangulation.constrained_delaunay(Polygon(Contour([Point(node.x, node.y) for node in nodes]), []), context=context).triangles()

    def draw(self):
        # 7 is the begin mode for quads
        for triangle in self.triangles:
            raylib.draw_triangle(raylib.Vector2(triangle.vertices[2].x-Building.texture_pos.x, triangle.vertices[2].y-Building.texture_pos.y),
                                 raylib.Vector2(triangle.vertices[1].x-Building.texture_pos.x, triangle.vertices[1].y-Building.texture_pos.y),
                                 raylib.Vector2(triangle.vertices[0].x-Building.texture_pos.x, triangle.vertices[0].y-Building.texture_pos.y), raylib.GRAY)