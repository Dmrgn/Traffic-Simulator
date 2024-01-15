import math
import pyray as raylib

from constants import *
from globals import geocode, roads as global_roads, camera
from lane import Lane, Connection

class RoadPiece:
    def __init__(self, road, start_pos, end_pos):
        self.road = road
        self.num_lanes = self.road.num_lanes
        self.start_pos = start_pos
        self.end_pos = end_pos
        # unit vector pointing in the direction of the road
        self.slope = raylib.vector2_normalize(raylib.Vector2(1, (self.end_pos.y-self.start_pos.y if self.end_pos.y-self.start_pos.y != 0 else 0.00001)/(self.end_pos.x-self.start_pos.x)))
        # unit vector pointing perpendicular to the road
        self.normal = raylib.vector2_normalize(raylib.vector2_rotate(self.slope, math.pi/2))
        self.length = raylib.vector_2distance(start_pos, end_pos)
        self.next_piece = None
        self.previous_piece = None
        self.lanes = []
        self.connections = []
        self.has_been_visited = False
        # create lanes
        self.create_lanes()

    def create_lanes(self):
        self.lanes = []
        lane_angles = []
        for i in range(self.num_lanes):
            # get the start pos of the lane 
            lane_start_pos = raylib.vector2_add(raylib.vector2_scale(self.normal, (-(self.num_lanes-1)+2*i)*(LANE_WIDTH/2)), self.start_pos)
            lane_end_pos = raylib.vector2_add(raylib.vector2_scale(self.normal, (-(self.num_lanes-1)+2*i)*(LANE_WIDTH/2)), self.end_pos)
            lane_angle = raylib.vector2_angle(raylib.vector2_add(lane_end_pos, raylib.vector2_scale(self.start_pos, -1)), self.normal)/math.pi*180
            if lane_angle < 0:
                # we only want the angle counter clockwise from the x axis
                lane_angle += 360
            lane_angles.append({
                "angle": lane_angle,
                "lane_start_pos": lane_start_pos,
                "lane_end_pos": lane_end_pos
            })
        lane_angles = sorted(lane_angles, key=lambda x: x["angle"])
        for i in range(self.num_lanes):
            if i < self.num_lanes/2:
                self.lanes.append(Lane(self, lane_angles[i]["lane_start_pos"], lane_angles[i]["lane_end_pos"]))
            else:
                if self.road.is_one_way:
                    # if the lane is one way, fill the spot so that calculations still line up,
                    # but don't create a new lane object
                    self.lanes.append(0)
                    continue
                self.lanes.append(Lane(self, lane_angles[i]["lane_end_pos"], lane_angles[i]["lane_start_pos"]))
            if len(self.lanes) > 1:
                # if both lanes are left and going in the same direction
                if (i-1 < self.num_lanes/2) and (i < self.num_lanes/2):
                    self.lanes[i-1].previous_lane = self.lanes[i]
                    self.lanes[i].next_lane = self.lanes[i-1]
                # if both lanes are right and going in the same direction
                elif (i-1 >= self.num_lanes/2) and (i >= self.num_lanes/2):
                    self.lanes[i-1].next_lane = self.lanes[i]
                    self.lanes[i].previous_lane = self.lanes[i-1]

    # merge two neighbouring road pieces which are part of the same road
    # this will reduce the number of road pieces in the parent road by 1
    def merge_road_piece(self, other_road_piece):
        my_nodes = [
            {"type":"start", "pos":self.start_pos}, 
            {"type":"end", "pos":self.end_pos}]
        other_nodes = [
            {"type":"start", "pos":other_road_piece.start_pos}, 
            {"type":"end", "pos":other_road_piece.end_pos}]
        # find which nodes are touching
        # it is garunteed that exactly one node in this road piece is touching exactly one node in the other road piece
        # because they are neighbouring road pieces in the same road
        distances = []
        for node in my_nodes:
            for other_node in other_nodes:
                distances.append((raylib.vector_2distance(node["pos"], other_node["pos"]), node["type"]+other_node["type"]))
        distances = sorted(distances, key=lambda x: x[0])
        transformations = {
            "startstart": [other_road_piece.end_pos, self.end_pos],
            "startend": [other_road_piece.start_pos, self.end_pos],
            "endstart": [self.start_pos, other_road_piece.end_pos],
            "endend": [self.start_pos, other_road_piece.start_pos],
        }
        transformation = transformations[distances[0][1]]
        self.start_pos = raylib.Vector2(transformation[0].x, transformation[0].y)
        self.end_pos = raylib.Vector2(transformation[1].x, transformation[1].y)
        self.slope = raylib.vector2_normalize(raylib.Vector2(1, (self.end_pos.y-self.start_pos.y if self.end_pos.y-self.start_pos.y != 0 else 0.00001)/(self.end_pos.x-self.start_pos.x)))
        self.normal = raylib.vector2_normalize(raylib.vector2_rotate(self.slope, math.pi/2))
        self.length = raylib.vector_2distance(self.start_pos, self.end_pos)
        # remove the other road piece from the parent node
        self.road.pieces.remove(other_road_piece)
        # update the lanes in this road piece
        # this is probably very slow, but idk how to do it otherwise
        self.create_lanes()

    # sets the lanes in this piece to line up with the lanes in adjacent pieces
    def set_adjacent_piece_lanes(self):
        for i in range(self.num_lanes):
            # if this lane is closed because the street is one way
            if self.lanes[i] == 0:
                continue
            # if this lane doesn't have neighbouring pieces to connect to 
            if self.lanes[i].next_piece_lane is not None and self.lanes[i].previous_piece_lane is not None:
                continue
            previous_lane_potentials = []
            next_lane_potentials = []
            # make sure the connecting lane is part of the same road
            for j in range(len(self.road.pieces)):
                if self is self.road.pieces[j]: continue
                for k in range(self.road.pieces[j].num_lanes):
                    # if the lane we are trying to connect to is closed because it is one way
                    if self.road.pieces[j].lanes[k] == 0:
                        continue
                    # if this lane's start is near my lane end
                    previous_distance = raylib.vector_2distance(self.road.pieces[j].lanes[k].start_pos, self.lanes[i].end_pos)
                    if previous_distance < LANE_WIDTH*self.num_lanes/2:
                        previous_lane_potentials.append({
                            "lane": self.road.pieces[j].lanes[k],
                            "distance": previous_distance
                        })
                    # if this lane's end is near my lane start
                    next_distance = raylib.vector_2distance(self.road.pieces[j].lanes[k].end_pos, self.lanes[i].start_pos)
                    if next_distance < LANE_WIDTH*self.num_lanes/2:
                        if len(previous_lane_potentials) > 0:
                            if previous_lane_potentials[-1]["lane"] is self.road.pieces[j].lanes[k]:
                                if next_distance < previous_distance:
                                    previous_lane_potentials.pop()
                                else:
                                    continue
                        next_lane_potentials.append({
                            "lane": self.road.pieces[j].lanes[k],
                            "distance": next_distance
                        })
                        # just take the first result (in theory there should only be one result anyways, but issues can be corrected on a per case basis)
            # pick closest lane start and end
            previous_lane_potentials = sorted(previous_lane_potentials, key=lambda x: x["distance"])
            next_lane_potentials = sorted(next_lane_potentials, key=lambda x: x["distance"])
            # set previous lane
            if len(previous_lane_potentials) > 0:
                self.lanes[i].next_piece_lane = previous_lane_potentials[0]["lane"]
                previous_lane_potentials[0]["lane"].previous_piece_lane = self.lanes[i]
            # set next lane
            if len(next_lane_potentials) > 0:
                self.lanes[i].previous_piece_lane = next_lane_potentials[0]["lane"]
                next_lane_potentials[0]["lane"].next_piece_lane = self.lanes[i]
        # now we need to make a list of connecting lanes which are part of other roads
        for road in global_roads:
            if road is self.road: continue
            for piece in road.pieces:
                my_nodes = [
                    {"type":"start", "pos":self.start_pos}, 
                    {"type":"end", "pos":self.end_pos}]
                other_nodes = [
                    {"type":"start", "pos":piece.start_pos},
                    {"type":"end", "pos":piece.end_pos}]
                connection_type = None
                connection_other_position = None
                connection_self_position = None
                is_intersection = False # if this road's node doesn't just meet a single other node, and instead meets multiple other nodes or a line segment or both
                for other_node in other_nodes:
                    # check if the nodes of these two roads collide with each other
                    collided_types = []
                    for node in my_nodes:
                        if raylib.vector_2distance(node["pos"], other_node["pos"]) < LANE_WIDTH/10:
                            collided_types.extend([node["type"], other_node["type"]])
                    if len(collided_types) > 0:
                        # if two start nodes or two end nodes collide than the lanes that intersect have opposite indexes
                        # if a start node and an end node collide than the lanes that intersect have the same indexes
                        connection_self_position = 0 if collided_types[0] == "start" else 1 # start where the node is in the lane
                        connection_other_position = 0 if collided_types[1] == "start" else 1 # start where the node is in the lane
                        if collided_types[0] == collided_types[1]:
                            connection_type = "opposite"
                        else:
                            connection_type = "same"
                    else:
                        # check if a road piece's node collides with a middle portion of this road piece (we have a t intersection, or four way intersection with one road split in half)
                        if raylib.check_collision_point_line(other_node["pos"], self.start_pos, self.end_pos, LANE_WIDTH):
                            is_intersection = True # we need to add more than one connection per lane (e.g, turning left or right instead of just straight)
                            # if the start node is colliding with this road piece, the lanes that intersect have the same indexes
                            # if the end node is collinding with this road piece, the lanes that intersect have 
                            # opposite indexes (e.g index 1 maps to index 2 on a 4 lane street)
                            if other_node["type"] == "start":
                                connection_type = "same"
                            else:
                                connection_type = "opposite"
                            # get the distance between the other node and the this road piece's start node
                            # as a percentage so we can use to it tell where the car needs to start when
                            # it moves to its new lane
                            connection_self_position = raylib.vector_2distance(other_node["pos"], self.start_pos)/self.length
                            connection_other_position = 0 if other_node["type"] == "start" else 1
                            break # no need to search the other node
                if connection_type is not None:
                    # if there is a connection than we need to hook up all the lanes in each piece
                    for j in range(piece.num_lanes):
                        # if this lane is closed because the road is one way
                        if piece.lanes[j] == 0:
                            continue
                        mapping_functions = [lambda x, o, w: x, lambda x, o, w: x] # index 0 is self to other lane index transformation, index 1 is other to self
                        if piece.num_lanes != self.num_lanes:
                            if connection_type == "same":
                                mapping_functions[0] = lambda x, o, w: int((o-w)/2)+x
                                mapping_functions[1] = lambda x, o, w: int(x*o/w)
                            else:
                                mapping_functions[0] = lambda x, o, w: o-1-x-int((o-w)/2)
                                mapping_functions[1] = lambda x, o, w: o-1-int(x*o/w)
                            if piece.num_lanes <= self.num_lanes:
                                temp = mapping_functions[0]
                                mapping_functions[0] = mapping_functions[1]
                                mapping_functions[1] = temp
                        elif connection_type == "opposite":
                            mapping_functions[0] = lambda x, o, w: x
                            mapping_functions[1] = lambda x, o, w: o-1-x
                        self_index = mapping_functions[1](j, self.num_lanes, piece.num_lanes)
                        # if this lane is in the opposite direction of the road piece, we need to change the connection position
                        if is_intersection:
                            # print("CREATING INTERSECTION CONNECTION")
                            # print("\t Id", id(self), id(piece))
                            for k in range(self.num_lanes):
                                # if this lane is closed because this is a one way road
                                if self.lanes[k] == 0 or piece.lanes[j] == 0:
                                    continue
                                # print("\t Self lane index:", k, "Piece lane Index", j)
                                # print("\t Positions before correction:", connection_self_position, connection_other_position)
                                correct_self_position = connection_self_position if k < self.num_lanes/2 else 1-connection_self_position
                                correct_other_position = connection_other_position if j < piece.num_lanes/2 else 1-connection_other_position
                                # print("\t Positions after correction:", correct_self_position, correct_other_position)
                                self.lanes[k].connections.add(Connection(self.lanes[k], piece.lanes[j], correct_self_position, correct_other_position))
                                piece.lanes[j].connections.add(Connection(piece.lanes[j], self.lanes[k], correct_other_position, correct_self_position))
                        else:
                            # print("CREATING CONNECTION")
                            # print("\t Id", id(self), id(piece))
                            # print("\t Self lane index:", self_index, "Piece lane Index", j)
                            # print("\t Positions before correction:", connection_self_position, connection_other_position)
                            correct_self_position = connection_self_position if self_index < self.num_lanes/2 else 1-connection_self_position
                            correct_other_position = connection_other_position if j < piece.num_lanes/2 else 1-connection_other_position
                            # print("\t Positions after correction:", correct_self_position, correct_other_position)
                            # if this lane is closed because this is a one way road
                            # piece.lanes[j] is already checked at the top of this loop
                            if self.lanes[self_index] == 0:
                                continue
                            self.lanes[self_index].connections.add(Connection(self.lanes[self_index], piece.lanes[j], correct_self_position, correct_other_position))
                            piece.lanes[j].connections.add(Connection(piece.lanes[j], self.lanes[self_index], correct_other_position, correct_self_position))
                            
    def update(self):
        for i in range(self.num_lanes):
            # if the lane is closed because this is a one way road
            if self.lanes[i] == 0:
                continue
            self.lanes[i].update()

    def draw(self):
        for i in range(self.num_lanes):
            # if the lane is closed because this is a one way road
            if self.lanes[i] == 0:
                continue
            self.lanes[i].draw()

    def draw_cars(self):
        for i in range(self.num_lanes):
            # if the lane is closed because this is a one way road
            if self.lanes[i] == 0:
                continue
            self.lanes[i].draw_cars()
    
    def draw_debug(self):
        for i in range(self.num_lanes):
            # if the lane is closed because this is a one way road
            if self.lanes[i] == 0:
                continue
            self.lanes[i].draw_debug()
