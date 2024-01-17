import pyray as raylib
import math
import random

import overpass
import car
import road
import building
import light
from constants import *
from globals import camera, roads, buildings, lights, time, paused

def spawn_rate(x):
    return -8.95231329283598e-19*x**17 + 4.31967000169694e-17*x**16 + 2.58805718149825e-15*x**15 - 2.23814494359364e-13*x**14 + 4.70443715788563e-12*x**13 - 7.54772235401552e-13*x**12 - 3.28570778431105e-11*x**11 - 3.84142447500097e-8*x**10 + 1.3619746937588e-8*x**9 + 4.54299609178217e-5*x**8 - 0.0013192773445446*x**7 + 0.0182270587731075*x**6 - 0.141903845390944*x**5 + 0.628859739453891*x**4 - 1.4872860983282*x**3 + 1.64903911599613*x**2 - 0.519628414894235*x + 0.189744648760354

def main():
    global time, paused, SCREEN_WIDTH, SCREEN_HEIGHT

    raylib.set_config_flags(raylib.ConfigFlags.FLAG_WINDOW_RESIZABLE)
    raylib.init_window(SCREEN_WIDTH, SCREEN_HEIGHT, b"Raylib Boilerplate - Python")
    raylib.set_target_fps(60)

    SCREEN_HEIGHT = raylib.get_screen_height()
    SCREEN_WIDTH = raylib.get_screen_width()

    camera.zoom = 1.0

    for overpass_object in overpass.data_lights:
        lights.append(light.Light(overpass_object))

    for road_type, overpass_objects in overpass.data_roads.items():
        for overpass_object in overpass_objects:
            roads.append(road.Road(road_type, overpass_object))
    road.Road.create_road_texture()
    
    for overpass_object in overpass.data_buildings:
        buildings.append(building.Building(overpass_object))
    building.Building.create_building_texture()

    count = 0
    # the data from overpass is utter dogshit and needs to be cleaned up a lot
    for r in roads:
        count+=1
        print("contract", count, "/",len(roads))
        # make 2 road intersections into one road
        r.contract_connecting_roads()   
    # count = 0  
    # for r in roads:
    #     count+=1
    #     print("simplify", count, "/",len(roads))
    #     # reduce the number of road pieces near intersections
    #     r.simplify_intersections()
    count = 0
    for r in roads:
        count+=1
        print("connect", count, "/",len(roads))
        # create intersections between road pieces
        r.create_connections()

    frame_count = 0
    while not raylib.window_should_close():
        if not paused:
            frame_count += 1
            time += 1/1000
            if time > 24: time = 0
            print(time)
            if frame_count % 60 == 0:
                for node in road.Road.dead_end_nodes:
                    if random.random()*(ROAD_SPAWN_RATES[node["road"].road_type]/spawn_rate(time)) > 1: continue
                    if len(node["road"].pieces) == 0:
                        continue
                    lane = node["road"].pieces[0 if node["type"] == "start" else -1].lanes[0 if node["type"] == "start" else -1]
                    if lane != 0:
                        lane.cars.append(car.Car(lane))
            
        if raylib.is_key_pressed(raylib.KeyboardKey.KEY_SPACE):
            paused = not paused
        if raylib.is_mouse_button_down(raylib.MOUSE_BUTTON_RIGHT):
            delta = raylib.get_mouse_delta()
            delta = raylib.vector2_scale(delta, -1.0 / camera.zoom)
            camera.target = raylib.vector2_add(camera.target, delta)
        if raylib.is_window_resized():
            SCREEN_HEIGHT = raylib.get_screen_height()
            SCREEN_WIDTH = raylib.get_screen_width()
        # zoom based on mouse wheel
        wheel = raylib.get_mouse_wheel_move()
        if wheel != 0:
            mouseWorldPos = raylib.get_screen_to_world_2d(raylib.get_mouse_position(), camera)
            camera.offset = raylib.get_mouse_position()
            camera.target = mouseWorldPos
            camera.zoom += (wheel * MOUSE_ZOOM_INCREMENT)
            if camera.zoom < MOUSE_ZOOM_INCREMENT:
                camera.zoom = MOUSE_ZOOM_INCREMENT

        raylib.begin_drawing()
        raylib.clear_background(raylib.Color(156, 220, 99))
        raylib.begin_mode_2d(camera)

        raylib.draw_texture_rec(building.Building.texture.texture, raylib.Rectangle(0, 0, building.Building.texture_size.x, -building.Building.texture_size.y), building.Building.texture_pos, raylib.WHITE)
        raylib.draw_texture_rec(road.Road.texture.texture, raylib.Rectangle(0, 0, road.Road.texture_size.x, -road.Road.texture_size.y), road.Road.texture_pos, raylib.WHITE)

        for r in roads:
            if not paused:
                r.update()
            r.draw_cars()
            r.draw_debug()

        for l in lights:
            if not paused:
                l.update()
            l.draw()

        for node in road.Road.dead_end_nodes:
            raylib.draw_circle(int(node["pos"].x), int(node["pos"].y), 4, raylib.GREEN)

        # m_pos = raylib.get_screen_to_world_2d(raylib.get_mouse_position(), camera)


        raylib.end_mode_2d()
        raylib.draw_rectangle(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, raylib.Color(0, 0, 0, int(255*(1-1/4*(math.sin(time/4 - 1) + 3)))))
        raylib.draw_fps(SCREEN_WIDTH-100, 10)

        raylib.end_drawing()

    # Close window
    raylib.close_window()

if __name__ == "__main__":
    main()