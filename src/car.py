from constants import *
import pyray as raylib
import random

class Car:
    def __init__(self, lane):
        self.lane = lane
        self.position = 0
        self.velocity = 0
        self.acceleration = 0
        self.lane_change_cooldown = 0
        self.is_dead = False

    def move_to_next_piece(self):
        if self.lane.next_piece_lane is not None:
            self.lane.next_piece_lane.cars.append(self)
            self.lane.cars.remove(self)
            self.position = 0
            self.lane = self.lane.next_piece_lane
        else:
            possible_connections = []
            for connection in list(self.lane.connections):
                if abs(connection.from_position - self.position) < LANE_WIDTH/self.lane.road_piece.length:
                    possible_connections.append(connection)
            if len(possible_connections) > 0:
                connection = random.choice(possible_connections)
                connection.to_lane.cars.append(self)
                self.position = connection.to_position
                self.lane.cars.remove(self)
                self.lane = connection.to_lane
            else:
                self.is_dead = True

    def update(self):
        self.lane_change_cooldown -= raylib.get_frame_time()
        if self.lane_change_cooldown < 0: self.lane_change_cooldown = 0

        distance_until_collision = self.check_future_collision(40)
        # we need to determine what the acceleration should be such that we are stationary 1 frame before we collide with another car
        if distance_until_collision == -1:
            self.acceleration = 0.007
        else:
            denominator = (-(distance_until_collision))
            if denominator == 0:
                self.acceleration = -0.1
            else:
                self.acceleration = ((self.velocity)**2)/(2*denominator)
        self.velocity += self.acceleration
        if self.velocity > ROAD_SPEED_LIMITS[self.lane.road_piece.road.road_type]:
            self.velocity = ROAD_SPEED_LIMITS[self.lane.road_piece.road.road_type]
        if self.velocity < 0:
            self.velocity = 0
        self.position += self.velocity*60*raylib.get_frame_time()/self.lane.road_piece.length

        other_lanes = [self.lane.next_lane, self.lane.previous_lane]
        for other_lane in other_lanes:
            if (other_lane is not None 
                and self.velocity < ROAD_SPEED_LIMITS[self.lane.road_piece.road.road_type]/2
                and self.velocity > 0.1
                and self.acceleration < 0
                and self.lane_change_cooldown == 0):
                can_change_lanes = True
                for c in other_lane.cars:
                    if abs((c.position-self.position)*self.lane.road_piece.length) < LANE_WIDTH*4:
                        can_change_lanes = False
                        break
                if can_change_lanes:
                    if random.random() < 0.4:
                        other_lane.cars.append(self)
                        self.lane.cars.remove(self)
                        self.lane = other_lane
                    self.lane_change_cooldown = 60


        for connection in self.lane.connections:
            if abs(self.position-connection.from_position)*self.lane.road_piece.length < self.velocity:
                if random.random() < 0.2:
                    connection.to_lane.cars.append(self)
                    self.position = connection.to_position
                    self.lane.cars.remove(self)
                    self.lane = connection.to_lane

        if self.position > 1:
            self.move_to_next_piece()

    def check_light_state(self, light):
        light_state = None
        for ol in light.lanes:
            if ol["lane"] is self.lane:
                light_state = ol["state"]
                break
        return light_state

    def draw(self):
        pos = raylib.vector2_lerp(self.lane.start_pos, self.lane.end_pos, self.position)
        start_pos = raylib.vector2_add(raylib.vector2_scale(self.lane.road_piece.slope, LANE_WIDTH*1.4), pos)
        end_pos = raylib.vector2_add(raylib.vector2_scale(self.lane.road_piece.slope, -LANE_WIDTH*1.4), pos)
        raylib.draw_line_ex(start_pos, end_pos, LANE_WIDTH*1.4, raylib.Color(51, 153, 255, 255))

    # save the current state of this car, then fast forward timesteps
    # time steps and see if we collide with anything, if we do, then
    # return to our original state
    def check_future_collision(self, distance):
        state = {
            "lane": self.lane,
            "position": self.position,
            "velocity": self.velocity,
            "acceleration": self.acceleration,
            "is_dead": self.is_dead,
            "lane_change_cooldown": self.lane_change_cooldown
        }
        distance_until_collision = -1
        lane_movement = 0
        # while the end of the current road piece is within the distance left to search
        while (1-self.position)*self.lane.road_piece.length < distance:
            for car in self.lane.cars:
                if car is self: continue
                # if there is a car infront of me before the end of this lane
                if car.position > self.position:
                    proposed_distance_until_collision = (car.position-self.position)*self.lane.road_piece.length + lane_movement
                    if distance_until_collision == -1 or proposed_distance_until_collision < distance_until_collision:
                        distance_until_collision = proposed_distance_until_collision
                        distance = 0
            for l in self.lane.lights:
                light_position, light = l
                if self.check_light_state(light) == "green": continue
                if light_position > self.position:
                    proposed_distance_until_collision = (light_position-self.position)*self.lane.road_piece.length + lane_movement
                    if distance_until_collision == -1 or proposed_distance_until_collision < distance_until_collision:
                        distance_until_collision = proposed_distance_until_collision
                        distance = 0
            if distance == 0: break
            distance -= (1-self.position)*self.lane.road_piece.length
            lane_movement += (1-self.position)*self.lane.road_piece.length
            self.position = 1
            self.move_to_next_piece()
            if self.is_dead: break # if we move off a dead end
        # if there is still distance left to search and we haven't already crashed, check for cars in this lane
        if distance_until_collision == -1:
            for car in self.lane.cars:
                if car is self: continue
                # if there is a car infront of me and less than distance away
                if car.position > self.position and (car.position-self.position)*self.lane.road_piece.length <= distance:
                    proposed_distance_until_collision = (car.position-self.position)*self.lane.road_piece.length + lane_movement
                    if distance_until_collision == -1 or proposed_distance_until_collision < distance_until_collision:
                        distance_until_collision = proposed_distance_until_collision
            for l in self.lane.lights:
                light_position, light = l
                if self.check_light_state(light) == "green": continue
                if light_position > self.position and (light_position-self.position)*self.lane.road_piece.length <= distance:
                    proposed_distance_until_collision = (light_position-self.position)*self.lane.road_piece.length + lane_movement
                    if distance_until_collision == -1 or proposed_distance_until_collision < distance_until_collision:
                        distance_until_collision = proposed_distance_until_collision
            # if we don't find any cars within the range of distance, then we won't crash
        if state["lane"] is not self.lane:
            state["lane"].cars.append(self)
            self.lane.cars.remove(self)
        self.lane = state["lane"]
        self.position = state["position"]
        self.velocity = state["velocity"]
        self.acceleration = state["acceleration"]
        self.is_dead = state["is_dead"]
        self.lane_change_cooldown = state["lane_change_cooldown"]
        if distance_until_collision > LANE_WIDTH*4:
            distance_until_collision -= LANE_WIDTH*4
        elif distance_until_collision != -1:
            distance_until_collision = 0
        return distance_until_collision


        