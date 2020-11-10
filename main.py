# -*- coding: utf-8 -*-
"""
Created on Sat Oct 31 17:12:48 2020

"""

import math
import random
import arcade
from utils.drill import *
from utils.dungeon_generator import *
from utils.explosion import * # explosion/smoke
from utils.funcs import *

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

MAP_WIDTH = 2400
MAP_HEIGHT = 2400
SCREEN_TITLE = "Welcome to the Drill Dungeon"

VIEWPOINT_MARGIN = 40



class DrillDungeonGame(arcade.Window):
    """
    Basic map class
    """

    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        #Sprite variables
        self.drill_list = None
        self.wall_list = None
        self.coal_list = None # coal/fuel increment
        self.gold_list = None # gold increment
        self.border_wall_list = None
        self.bullet_list = None #  shooting/aiming
        self.explosions_list = None
        
        
        
        self.a_pressed = False
        self.d_pressed = False
        self.w_pressed = False
        self.s_pressed = False


        #Initialize scrolling variables
        self.view_bottom = 0
        self.view_left = 0


        self.drill_down = False

        self.current_layer = 0

        self.gold_per_layer = 20
        self.coal_per_layer = 20
        self.dungeons_per_layer = 3
        
        arcade.set_background_color(arcade.color.BROWN_NOSE)

    def setup(self, number_of_coal_patches=20, number_of_gold_patches=20, number_of_dungeons=3, drillX=64, drillY=128):
        """
        Set up game and initialize variables
        """
        self.wall_list = arcade.SpriteList(use_spatial_hash=True) # spatial hash, makes collision detection faster
        self.border_wall_list = arcade.SpriteList(use_spatial_hash=True)
        self.coal_list = arcade.SpriteList(use_spatial_hash=True) # coal/fuel
        self.gold_list = arcade.SpriteList(use_spatial_hash=True) # gold increment
        self.bullet_list = arcade.SpriteList() # shooting/aiming
        self.explosions_list = arcade.SpriteList() # explosion/smoke


        #Initialize the map layer with some dungeon
        mapLayer = MapLayer(100, 100, meanDungeonSize=400, meanCoalSize=10, meanGoldSize=10)
        mapLayer.generate_blank_map()
        for i in range(number_of_dungeons):
            mapLayer.generate_dungeon()
        for i in range(number_of_coal_patches):
            mapLayer.generate_coal()
        for i in range(number_of_gold_patches):
            mapLayer.generate_gold()

        mapLayer.generate_border_walls()

        #Load map layer from mapLayer
        self.load_map_layer_from_matrix(mapLayer.mapLayerMatrix)

        drillSpriteImage="resources/images/drills/drill_v2_2.png"
        turretSpriteImage="resources/images/weapons/turret1.png"

        self.drill_list=Drill(drillSpriteImage, 0.3, turretSpriteImage, 0.12, startPositionX=drillX, startPositionY=drillY)
        self.drill_list.physics_engine_setup(self.border_wall_list)


        #Set viewpoint boundaries - where the drill currently has scrolled to
        self.view_left = 0 
        self.view_bottom = 0 

    def draw_next_map_layer(self):
        """
        Generates and loads the next layer of the map when drilling down
        """
        self.setup(self.coal_per_layer, self.gold_per_layer, self.dungeons_per_layer, self.drill_list.turret.center_x, self.drill_list.turret.center_y)
        self.current_layer += 1
        self.update_map_configuration()

        arcade.start_render()
        self.wall_list.draw()
        self.coal_list.draw() 
        self.gold_list.draw()
        self.drill_list.draw()
        self.bullet_list.draw() 
        self.explosions_list.draw() 
        self.border_wall_list.draw()
        
    def update_map_configuration(self):
        """
        Updates the map's configuration specs for the next layer, allowing for
        increased difficulty
        """
        self.coal_per_layer = generate_next_layer_resource_patch_amount(self.current_layer) 
        self.gold_per_layer = generate_next_layer_resource_patch_amount(self.current_layer) 
        self.dungeons_per_layer = generate_next_layer_dungeon_amount(self.current_layer)
      

    def on_draw(self):
        """
        Draws the map
        """
        arcade.start_render()
        self.wall_list.draw()
        self.coal_list.draw() # coal/fuel
        self.gold_list.draw() # gold increment
        self.border_wall_list.draw()
        self.drill_list.draw()
        self.bullet_list.draw() # shooting/aiming
        self.explosions_list.draw() # explosion/smoke


        hud = f"Ammunition: {self.drill_list.ammunition}\nCoal:{self.drill_list.coal}\nGold:{self.drill_list.gold}" 
        
        arcade.draw_text(hud, self.view_left + 10, self.view_bottom + 20, arcade.color.BLACK, 20) # update hud with screen scroll
        
    def load_map_layer_from_matrix(self, mapLayerMatrix):
        """
        Loads a map from a layer matrix
        list mapLayer Matrix : A matrix containing the map configuration, as
        generated by the MapLayer class
        """
        mapLayerHeight = len(mapLayerMatrix)
        mapLayerWidth = len(mapLayerMatrix[0])
        blockHeight = MAP_HEIGHT / mapLayerHeight
        blockWidth = MAP_WIDTH / mapLayerWidth
        yBlockCenter = 0.5 * blockHeight
        for row in mapLayerMatrix:
            self.fill_row_with_terrain(row, yBlockCenter, blockWidth, blockHeight)
            yBlockCenter += blockHeight

    def fill_row_with_terrain(self, mapRow, yBlockCenter, blockWidth, blockHeight):
        """
        Fills a row with terrain
        list mapRow        : a row of the map matrix
        int yBlockCenter   : the y of the center of the blocks for the row
        int blockWidth     : width of the blocks to fill the terrain
        int blockHeight    : height of the blocks to fill the terrain
        """
        xBlockCenter = 0.5 * blockWidth
        for item in mapRow:
            if item == 'X':
                wallsprite = arcade.Sprite(":resources:images/tiles/grassCenter.png", 0.18)
                #wallsprite.width = blockWidth
                #wallsprite.height = blockHeight
                wallsprite.center_x = xBlockCenter
                wallsprite.center_y = yBlockCenter
                self.wall_list.append(wallsprite)
            if item == 'C':
                wallsprite = arcade.Sprite(":resources:images/tiles/dirtCenter.png", 0.18)
                #wallsprite.width = blockWidth
                #wallsprite.height = blockHeight
                wallsprite.center_x = xBlockCenter
                wallsprite.center_y = yBlockCenter
                self.coal_list.append(wallsprite) # append coal to coal list
            if item == 'G':
                wallsprite = arcade.Sprite(":resources:images/tiles/lava.png", 0.18)
                wallsprite.center_x = xBlockCenter
                wallsprite.center_y = yBlockCenter
                self.gold_list.append(wallsprite) # append gold to gold list
            if item == 'O':
                wallsprite = arcade.Sprite(":resources:images/tiles/grassMid.png", 0.18)
                wallsprite.center_x = xBlockCenter
                wallsprite.center_y = yBlockCenter
                self.border_wall_list.append(wallsprite)
            xBlockCenter += blockWidth

    def on_key_press(self, key, modifiers): 

        """Called whenever a key is pressed. """

        if key == arcade.key.W:
            self.w_pressed = True
        elif key == arcade.key.S:
            self.s_pressed = True
        elif key == arcade.key.A:
            self.a_pressed = True
        elif key == arcade.key.D:
            self.d_pressed = True
        elif key == arcade.key.T:
            self.drill_down = True

    def on_key_release(self, key, modifiers):
        """Called when the user releases a key. """

        if key == arcade.key.W:
            self.w_pressed = False
        elif key == arcade.key.S:
            self.s_pressed = False
        elif key == arcade.key.A:
            self.a_pressed = False
        elif key == arcade.key.D:
            self.d_pressed = False

    def on_mouse_motion(self, x, y, dx, dy):
        """ Handle Mouse Motion """
        self.drill_list.aim_turret(x+self.view_left, y+self.view_bottom)

       


    def on_mouse_press(self, x, y, button, modifiers): # shooting/aiming
        # sprite scaling laser
        bullet = arcade.Sprite(":resources:images/space_shooter/laserBlue01.png", 0.4)

        start_x = self.drill_list.turret.center_x
        start_y = self.drill_list.turret.center_y
        bullet.center_x = start_x
        bullet.center_y = start_y

        dest_x = x + self.view_left
        dest_y = y + self.view_bottom

        x_diff = dest_x - start_x
        y_diff = dest_y - start_y
        angle = math.atan2(y_diff, x_diff)

        bullet.angle = math.degrees(angle)

        #bullet speed at the end
        bullet.change_x = math.cos(angle) * 7
        bullet.change_y = math.sin(angle) * 7

        # limited ammunition
            
        if self.drill_list.ammunition > 0:
            self.bullet_list.append(bullet) # if empty, no more bullets append to bullet_list, no shooting
            self.drill_list.ammunition = self.drill_list.ammunition - 1

    def update_map_view(self):
        #Check if the drill has reached the edge of the box
        changed = False
        changed = self.check_for_scroll_left(changed)
        changed = self.check_for_scroll_right(changed)
        changed = self.check_for_scroll_up(changed)
        changed = self.check_for_scroll_down(changed)

        self.view_left = int(self.view_left)
        self.view_bottom = int(self.view_bottom)

        if changed:
            arcade.set_viewport(self.view_left, SCREEN_WIDTH + self.view_left, self.view_bottom, SCREEN_HEIGHT + self.view_bottom)




    def move_drill(self):
        if self.w_pressed and not (self.s_pressed or self.a_pressed or self.d_pressed):
            self.drill_list.moveDrill("UP")
        # move diagonal up right
        elif self.w_pressed and self.d_pressed and not (self.s_pressed or self.a_pressed):
            self.drill_list.moveDrill("UPRIGHT")
        # move down
        elif self.s_pressed and not (self.w_pressed or self.a_pressed or self.d_pressed):
            self.drill_list.moveDrill("DOWN")
        # move diagonal down right
        elif self.s_pressed and self.d_pressed and not (self.w_pressed or self.a_pressed):
            self.drill_list.moveDrill("DOWNRIGHT")
        # move left
        elif self.a_pressed and not (self.w_pressed or self.s_pressed or self.d_pressed):
            self.drill_list.moveDrill("LEFT")
        # move digonal up left
        elif self.a_pressed and self.w_pressed and not  ( self.s_pressed or self.d_pressed):
            self.drill_list.moveDrill("UPLEFT")
        # move right
        elif self.d_pressed and not (self.w_pressed or self.s_pressed or self.a_pressed):
            self.drill_list.moveDrill("RIGHT")
        # move digonal down left
        elif self.a_pressed and self.s_pressed and not  ( self.w_pressed or self.d_pressed):
            self.drill_list.moveDrill("DOWNLEFT")




    def check_for_scroll_left(self, changed):
        left_boundary = self.view_left + VIEWPOINT_MARGIN
        if self.drill_list.left() < left_boundary:
            self.view_left -= left_boundary - self.drill_list.left()
            changed = True
        return changed

    def check_for_scroll_right(self, changed):
        right_boundary = self.view_left + SCREEN_WIDTH - VIEWPOINT_MARGIN
        if self.drill_list.right() > right_boundary:
            self.view_left += self.drill_list.right() - right_boundary
            changed = True
        return changed

    def check_for_scroll_up(self, changed):
        top_boundary = self.view_bottom + SCREEN_HEIGHT - VIEWPOINT_MARGIN
        if self.drill_list.top() > top_boundary:
            self.view_bottom += self.drill_list.top() - top_boundary
            changed = True
        return changed

    def check_for_scroll_down(self, changed):
        bottom_boundary = self.view_bottom + VIEWPOINT_MARGIN
        if self.drill_list.bottom() < bottom_boundary:
            self.view_bottom -= bottom_boundary - self.drill_list.bottom()
            changed = True
        return changed

# moved on_update to the end of the main 
    def on_update(self, delta_time):
        """ Movement and game logic """

        
        self.drill_list.stopMoving()
        self.move_drill()


        self.drill_list.update_physics_engine()
        #clears map to leave tunnel behind drill
        self.drill_list.clear_dirt(self.wall_list)
        #collects coal and increments fuel tank
        self.drill_list.collectCoal(self.coal_list)
        #collect gold and increments gold
        self.drill_list.collectGold(self.gold_list) 

        #Check for side scrolling
        self.update_map_view()        

        #self.physics_engine.update()        
        self.bullet_list.update()
        self.explosions_list.update()

        self.bullet_update()

        if self.drill_down:
            self.draw_next_map_layer()
            self.drill_down = False

        
       
    def bullet_update(self):
        for bullet in self.bullet_list:
            hit_list_wall = arcade.check_for_collision_with_list(bullet, self.wall_list)
            hit_list_coal = arcade.check_for_collision_with_list(bullet, self.coal_list) # add to remove coal block when shot
            hit_list_gold = arcade.check_for_collision_with_list(bullet, self.gold_list) # add to remove gold block when shot
            # remove bullet
            if len(hit_list_wall) > 0:
                bullet.remove_from_sprite_lists()
            # remove hit wall    
            for wall in hit_list_wall:
            # explosion and smoke when wall hit
                for i in range(PARTICLE_COUNT):
                    particle = ParticleDirt(self.explosions_list)
                    particle.position = wall.position
                    self.explosions_list.append(particle)
                    
                smoke = Smoke(50)
                smoke.position = wall.position
                self.explosions_list.append(smoke)
                wall.remove_from_sprite_lists()
                
                
            if len(hit_list_coal) > 0:
                bullet.remove_from_sprite_lists()
            for coal in hit_list_coal:       
                for i in range(PARTICLE_COUNT):
                    particle = ParticleCoal(self.explosions_list)
                    particle.position = coal.position
                    self.explosions_list.append(particle)
                    
                smoke = Smoke(50)
                smoke.position = coal.position
                self.explosions_list.append(smoke)
                coal.remove_from_sprite_lists()
                
                
            if len(hit_list_gold) > 0:
                bullet.remove_from_sprite_lists()                
            for gold in hit_list_gold:       
                for i in range(PARTICLE_COUNT):
                    particle = ParticleGold(self.explosions_list)
                    particle.position = gold.position
                    self.explosions_list.append(particle)
                    
                smoke = Smoke(50)
                smoke.position = gold.position
                self.explosions_list.append(smoke)
                gold.remove_from_sprite_lists()                    

     
                
            # later also add for enemies 


            
            if bullet.center_x > self.width+self.view_left or bullet.center_x < self.view_left or bullet.center_y > self.width+self.view_bottom or bullet.center_y < self.view_bottom:
                bullet.remove_from_sprite_lists()




def main():
    window = DrillDungeonGame()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()
