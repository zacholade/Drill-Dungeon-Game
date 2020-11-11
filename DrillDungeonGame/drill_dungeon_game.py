import arcade

from DrillDungeonGame.entity.mixins import ShootingMixin, DiggingMixin, PathFindingMixin, ControllableMixin
from DrillDungeonGame.entity.entities.drill import Drill
from DrillDungeonGame.entity.entities.spaceship_enemy import SpaceshipEnemy
from DrillDungeonGame.map.dungeon_generator import MapLayer
from DrillDungeonGame.particles.explosion import PARTICLE_COUNT, ParticleDirt, ParticleCoal, Smoke, ParticleGold
from DrillDungeonGame.utility import *

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
MAP_WIDTH = 2400
MAP_HEIGHT = 2400
SCREEN_TITLE = "Welcome to the Drill Dungeon"
VIEWPOINT_MARGIN = 40


class SpriteMap:
    def __init__(self):



class DrillDungeonGame(arcade.Window):
    """
    Basic map class
    """
    # This builds a dictionary of all possible keys that arcade can register as 'pressed'.
    # They unfortunately don't have another method to get this, and populating it before init is not taxing.
    possible_keys = {value: key for key, value in arcade.key.__dict__.items() if not key.startswith('_')}

    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        # Sprite variables
        self.drill_list = None
        self.wall_list = None
        self.coal_list = None  # coal/fuel increment
        self.gold_list = None  # gold increment
        self.border_wall_list = None
        self.bullet_list = None  # shooting/aiming
        self.explosions_list = None
        self.entity_list = None

        self.keys_pressed = {key: False for key in arcade.key.__dict__.keys() if not key.startswith('_')}

        # Initialize scrolling variables
        self.view_bottom = 0
        self.view_left = 0

        self.drill_down = False

        self.current_layer = 0

        self.gold_per_layer = 20
        self.coal_per_layer = 20
        self.dungeons_per_layer = 3

        self.frame = 0
        self.time = 0
        arcade.set_background_color(arcade.color.BROWN_NOSE)

    def setup(self, number_of_coal_patches=20, number_of_gold_patches=20,
              number_of_dungeons=3, center_x=64, center_y=128):
        """
        Set up game and initialize variables
        """
        self.wall_list = arcade.SpriteList(use_spatial_hash=True)  # spatial hash, makes collision detection faster
        self.border_wall_list = arcade.SpriteList(use_spatial_hash=True)
        self.coal_list = arcade.SpriteList(use_spatial_hash=True)  # coal/fuel
        self.gold_list = arcade.SpriteList(use_spatial_hash=True)  # gold increment
        self.bullet_list = arcade.SpriteList()  # shooting/aiming
        self.explosions_list = arcade.SpriteList()  # explosion/smoke
        self.entity_list = arcade.SpriteList()  # All enemies

        # Initialize the map layer with some dungeon
        map_layer = MapLayer(100, 100, meanDungeonSize=400, meanCoalSize=10, meanGoldSize=10)
        map_layer.generate_blank_map()
        for i in range(number_of_dungeons):
            map_layer.generate_dungeon()
        for i in range(number_of_coal_patches):
            map_layer.generate_coal()
        for i in range(number_of_gold_patches):
            map_layer.generate_gold()

        map_layer.generate_border_walls()

        # Load map layer from mapLayer
        self.load_map_layer_from_matrix(map_layer.mapLayerMatrix)

        self.drill_list = Drill(center_x=center_x, center_y=center_y)
        self.drill_list.physics_engine_setup(self.border_wall_list)
        self.entity_list.append(SpaceshipEnemy(200, 200, 200, 0.3))

        for entity in self.entity_list:
            entity.physics_engine_setup(self.border_wall_list)

        # Set viewpoint boundaries - where the drill currently has scrolled to
        self.view_left = 0
        self.view_bottom = 0

    def draw_next_map_layer(self):
        """
        Generates and loads the next layer of the map when drilling down
        """
        self.setup(self.coal_per_layer,
                   self.gold_per_layer,
                   self.dungeons_per_layer,
                   self.drill_list.turret.center_x,
                   self.drill_list.turret.center_y)

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
        self.coal_list.draw()  # coal/fuel
        self.gold_list.draw()  # gold increment
        self.border_wall_list.draw()
        self.drill_list.draw()
        self.bullet_list.draw()  # shooting/aiming
        self.explosions_list.draw()  # explosion/smoke
        for entity in self.entity_list:
            entity.draw()

        for entity in self.entity_list:
            if entity.path:
                arcade.draw_line_strip(entity.path, arcade.color.BLUE, 2)

        hud = f"Ammunition: {self.drill_list.ammunition}\nCoal:{self.drill_list.coal}\nGold:{self.drill_list.gold}"
        # update hud with screen scroll
        arcade.draw_text(hud, self.view_left + 10, self.view_bottom + 20, arcade.color.BLACK, 20)

    def load_map_layer_from_matrix(self, map_layer_matrix):
        """
        Loads a map from a layer matrix
        list map_layer_matrix : A matrix containing the map configuration, as
        generated by the MapLayer class
        """
        map_layer_height = len(map_layer_matrix)
        map_layer_width = len(map_layer_matrix[0])
        block_height = MAP_HEIGHT / map_layer_height
        block_width = MAP_WIDTH / map_layer_width
        y_block_center = 0.5 * block_height
        for row in map_layer_matrix:
            self.fill_row_with_terrain(row, y_block_center, block_width, block_height)
            y_block_center += block_height

    def fill_row_with_terrain(self, map_row, y_block_center, block_width, block_height):
        """
        Fills a row with terrain
        list map_row        : a row of the map matrix
        int y_block_center   : the y of the center of the blocks for the row
        int block_width     : width of the blocks to fill the terrain
        int block_height    : height of the blocks to fill the terrain
        """
        x_block_center = 0.5 * block_width
        for item in map_row:
            if item == 'X':
                wall_sprite = arcade.Sprite(":resources:images/tiles/grassCenter.png", 0.18)
                # wall_sprite.width = blockWidth
                # wall_sprite.height = blockHeight
                wall_sprite.center_x = x_block_center
                wall_sprite.center_y = y_block_center
                self.wall_list.append(wall_sprite)
            if item == 'C':
                wall_sprite = arcade.Sprite("resources/images/material/Coal_square.png", 0.03)
                # wall_sprite.width = blockWidth
                # wall_sprite.height = blockHeight
                wall_sprite.center_x = x_block_center
                wall_sprite.center_y = y_block_center
                self.coal_list.append(wall_sprite)  # append coal to coal list
            if item == 'G':
                wall_sprite = arcade.Sprite("resources/images/material/Gold_square.png", 0.03)
                wall_sprite.center_x = x_block_center
                wall_sprite.center_y = y_block_center
                self.gold_list.append(wall_sprite)  # append gold to gold list
            if item == 'O':
                wall_sprite = arcade.Sprite(":resources:images/tiles/grassMid.png", 0.18)
                wall_sprite.center_x = x_block_center
                wall_sprite.center_y = y_block_center
                self.border_wall_list.append(wall_sprite)
            x_block_center += block_width

    def on_key_press(self, key, modifiers):
        """If a key is pressed, it sets that key in self.keys_pressed dict to True, and passes the dict onto
        every entity that requires this information. ie All that subclass ControllableMixin.
        This will probably just be the drill... but maybe we wan't controllable minions?"""
        key_stroke = self.possible_keys.get(key)
        if key_stroke is None:
            return

        self.keys_pressed[key_stroke] = True
        for entity in (self.drill_list, *self.entity_list):
            if issubclass(entity.__class__, ControllableMixin):
                entity.update_keys(self.keys_pressed)

        if self.keys_pressed['T']:
            self.drill_down = True

    def on_key_release(self, key, modifiers):
        """Same as above function, but it sets the value to False"""
        key_stroke = self.possible_keys.get(key)
        if key_stroke is None:
            return

        self.keys_pressed[key_stroke] = False
        for entity in (self.drill_list, *self.entity_list):
            if issubclass(entity.__class__, ControllableMixin):
                entity.update_keys(self.keys_pressed)

        if self.keys_pressed['T']:
            self.drill_down = False

    def on_mouse_motion(self, x, y, dx, dy):
        """ Handle Mouse Motion """
        self.drill_list.aim(x+self.view_left, y+self.view_bottom)

    def on_mouse_press(self, x, y, button, modifiers):  # shooting/aiming
        # for entity in (self.drill_list, *self.entity_list):
        #     if issubclass(entity.__class__, ShootingMixin):
        #         entity.shoot()
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

        # bullet speed at the end
        bullet.change_x = math.cos(angle) * 7
        bullet.change_y = math.sin(angle) * 7

        # limited ammunition
        if self.drill_list.ammunition > 0:
            self.bullet_list.append(bullet)  # if empty, no more bullets append to bullet_list, no shooting
            self.drill_list.ammunition = self.drill_list.ammunition - 1

    def update_map_view(self):
        # Check if the drill has reached the edge of the box
        changed = False
        changed = self.check_for_scroll_left(changed)
        changed = self.check_for_scroll_right(changed)
        changed = self.check_for_scroll_up(changed)
        changed = self.check_for_scroll_down(changed)

        self.view_left = int(self.view_left)
        self.view_bottom = int(self.view_bottom)

        if changed:
            arcade.set_viewport(self.view_left, SCREEN_WIDTH + self.view_left,
                                self.view_bottom, SCREEN_HEIGHT + self.view_bottom)

    def check_for_scroll_left(self, changed):
        left_boundary = self.view_left + VIEWPOINT_MARGIN
        if self.drill_list.left < left_boundary:
            self.view_left -= left_boundary - self.drill_list.left
            changed = True
        return changed

    def check_for_scroll_right(self, changed):
        right_boundary = self.view_left + SCREEN_WIDTH - VIEWPOINT_MARGIN
        if self.drill_list.right > right_boundary:
            self.view_left += self.drill_list.right - right_boundary
            changed = True
        return changed

    def check_for_scroll_up(self, changed):
        top_boundary = self.view_bottom + SCREEN_HEIGHT - VIEWPOINT_MARGIN
        if self.drill_list.top > top_boundary:
            self.view_bottom += self.drill_list.top - top_boundary
            changed = True
        return changed

    def check_for_scroll_down(self, changed):
        bottom_boundary = self.view_bottom + VIEWPOINT_MARGIN
        if self.drill_list.bottom < bottom_boundary:
            self.view_bottom -= bottom_boundary - self.drill_list.bottom
            changed = True
        return changed

    # moved on_update to the end of the main
    def on_update(self, delta_time):
        """ Movement and game logic """
        self.frame += 1
        self.time += delta_time

        # for entity in (self.drill_list, *self.entity_list):
        #     entity.stop_moving()

        for entity in (self.drill_list, *self.entity_list):
            entity.update_physics_engine()

        for entity in (self.drill_list, *self.entity_list):
            # clears map to leave tunnel behind drill
            if issubclass(entity.__class__, DiggingMixin):
                entity.dig(self.wall_list)

        # collects coal and increments fuel tank
        self.drill_list.collect_coal(self.coal_list)
        # collect gold and increments gold
        self.drill_list.collect_gold(self.gold_list)

        # Check for side scrolling
        self.update_map_view()

        # self.physics_engine.update()

        for entity in (self.drill_list, *self.entity_list):
            entity.update()

        self.bullet_list.update()
        self.explosions_list.update()
        self.bullet_update()

        if self.drill_down:
            self.draw_next_map_layer()
            self.drill_down = False

        for entity in self.entity_list:
            if isinstance(entity, ShootingMixin) and entity.has_line_of_sight_with(self.drill_list, self.wall_list):
                entity.aim(self.drill_list.center_x, self.drill_list.center_y)

        # TODO don't use frame as measure of doing task every x loops. Use time instead.
        if self.frame % 30 == 0:
            if isinstance(entity, PathFindingMixin) and \
                    entity.has_line_of_sight_with(self.drill_list, self.wall_list):
                entity.path_to_position(*self.drill_list.position, self.wall_list)

            for entity in self.entity_list:
                if isinstance(entity, ShootingMixin) and entity.has_line_of_sight_with(self.drill_list, self.wall_list):
                    entity.shoot()

    def bullet_update(self):
        for bullet in self.bullet_list:
            hit_list_wall = arcade.check_for_collision_with_list(bullet, self.wall_list)
            # add to remove gold and coal blocks when they're shot
            hit_list_coal = arcade.check_for_collision_with_list(bullet, self.coal_list)
            hit_list_gold = arcade.check_for_collision_with_list(bullet, self.gold_list)
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

                    gold.remove_from_sprite_lists()

            # later also add for enemies

            if bullet.center_x > self.width + self.view_left or bullet.center_x < self.view_left or \
                    bullet.center_y > self.width+self.view_bottom or bullet.center_y < self.view_bottom:
                bullet.remove_from_sprite_lists()