import pyray as raylib
import math

import overpass
import car
import road
import building
from constants import *
from globals import camera, roads, buildings

def main():
    road_type_counter = 0
    road_section_counter = 0

    # Initialize window
    raylib.init_window(IMAGE_SIZE, IMAGE_SIZE, b"Raylib Boilerplate - Python")

    # Set the frames-per-second
    raylib.set_target_fps(1000)

    camera.zoom = 1.0

    for road_type, overpass_objects in overpass.data_roads.items():
        for overpass_object in overpass_objects:
            roads.append(road.Road(road_type, overpass_object))
    road.Road.create_road_texture()
    
    for overpass_object in overpass.data_buildings:
        buildings.append(building.Building(overpass_object))
    building.Building.create_building_texture()

    # data = [["primary", raylib.Vector2(-400, 30), raylib.Vector2(-101, 0.2)],
    #         ["primary", raylib.Vector2(-101, 0.2), raylib.Vector2(100, 0.1), raylib.Vector2(150, -50), raylib.Vector2(151, -100), raylib.Vector2(152, -200)],
    #         ["secondary", raylib.Vector2(0, -201), raylib.Vector2(300, -202)]]

    # data = [
    #     ["secondary", raylib.Vector2(400, 400), raylib.Vector2(401, 300)],
    #     ["secondary", raylib.Vector2(300, 400), raylib.Vector2(401, 400.1)],
    #     ["secondary", raylib.Vector2(401, 400.1), raylib.Vector2(500, 400.1)],
    #     ["secondary", raylib.Vector2(400, 420), raylib.Vector2(401, 400)],
    #     ["secondary", raylib.Vector2(400, 500), raylib.Vector2(401, 420)],
    # ]

    # for r in data:
    #     roads.append(road.Road(r.pop(0), _points=r))

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

    # Main game loop
    frame_count = 0
    while not raylib.window_should_close():
        frame_count += 1
        if frame_count % 800 == 0:
            for node in road.Road.dead_end_nodes:
                if len(node["road"].pieces) == 0:
                    continue
                lane = node["road"].pieces[0 if node["type"] == "start" else -1].lanes[0 if node["type"] == "start" else -1]
                if lane != 0:
                    lane.cars.append(car.Car(lane))

        if raylib.is_key_pressed(raylib.KeyboardKey.KEY_SPACE):
            if road_section_counter != -1:
                items = list(overpass.roads.items())
                roads.append(road.Road(items[road_type_counter][0], items[road_type_counter][1][road_section_counter]))
                road_section_counter += 1
                if road_section_counter >= len(items[road_type_counter][1]):
                    road_section_counter = 0
                    road_type_counter += 1
                if road_type_counter == 3:
                    road_section_counter = -1
        # update
        if raylib.is_mouse_button_down(raylib.MOUSE_BUTTON_RIGHT):
            delta = raylib.get_mouse_delta()
            delta = raylib.vector2_scale(delta, -1.0 / camera.zoom)
            camera.target = raylib.vector2_add(camera.target, delta)
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
            r.update()
            r.draw_cars()
            r.draw_debug()

        for node in road.Road.dead_end_nodes:
            raylib.draw_circle(int(node["pos"].x), int(node["pos"].y), 4, raylib.GREEN)

        # m_pos = raylib.get_screen_to_world_2d(raylib.get_mouse_position(), camera)

        raylib.end_mode_2d()
        raylib.draw_fps(IMAGE_SIZE-80, 10)

        raylib.end_drawing()

    # Close window
    raylib.close_window()

if __name__ == "__main__":
    main()