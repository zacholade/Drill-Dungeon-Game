from typing import List

import arcade

from DrillDungeonGame.entity.mixins.controllable_mixin import ControllableMixin
from DrillDungeonGame.entity.entities.drill import Drill
from DrillDungeonGame.entity.entities.spaceship_enemy import SpaceshipEnemy
from DrillDungeonGame.in_game_menus import *
from DrillDungeonGame.map.block import BlockGrid
from DrillDungeonGame.map.dungeon_generator import MapLayer, MAP_WIDTH, MAP_HEIGHT
from DrillDungeonGame.obscure_vision import ObscuredVision
from DrillDungeonGame.sprite_container import SpriteContainer
from DrillDungeonGame.utility import *
from DrillDungeonGame.utility.constants import SCREEN_WIDTH, SCREEN_HEIGHT, VIEWPOINT_MARGIN


class View:
    """

    Class to display and refresh the game window.

    Methods
    -------
    update(centre_sprite: arcade.Sprite)
        Update any changes in the game by updating the view.
    _check_for_scroll_left()
        Scrolls window to the left if player moves to the left.
    _check_for_scroll_right()
        Scrolls window to the right if player moves to the right.
    _check_for_scroll_up()
        Scrolls window up if player moves up.
    _check_for_scroll_down()
        Scrolls window down if player moves down.

    """
    def __init__(self) -> None:
        self.left_offset = 0
        self.bottom_offset = 0
        self._centre_sprite = None
        # TODO store the width/height of the screen. This can then be passed to the Entity.update() function

    def update(self, centre_sprite: arcade.Sprite) -> None:
        """

        Check if drill has reached an edge of the viewport.

        Parameters
        ----------
        centre_sprite: arcade.Sprite
            Center of the screen.

        """
        # Check if the drill has reached the edge of the box
        self._centre_sprite = centre_sprite
        changed = any((self._check_for_scroll_left(), self._check_for_scroll_right(),
                      self._check_for_scroll_up(), self._check_for_scroll_down()))

        self.left_offset = int(self.left_offset)
        self.bottom_offset = int(self.bottom_offset)

        if changed:
            arcade.set_viewport(self.left_offset, SCREEN_WIDTH + self.left_offset,
                                self.bottom_offset, SCREEN_HEIGHT + self.bottom_offset)

    def _check_for_scroll_left(self) -> bool:
        """

        Checks if left scroll is necessary.

        Returns
        -------
        boolean
            True: recenter

        """
        left_boundary = self.left_offset + VIEWPOINT_MARGIN
        if self._centre_sprite.left < left_boundary:
            self.left_offset -= left_boundary - self._centre_sprite.left
            return True
        return False

    def _check_for_scroll_right(self) -> bool:
        """

        Checks if right scroll is necessary.

        Returns
        -------
        boolean
            True: recenter

        """
        right_boundary = self.left_offset + SCREEN_WIDTH - VIEWPOINT_MARGIN
        if self._centre_sprite.right > right_boundary:
            self.left_offset += self._centre_sprite.right - right_boundary
            return True
        return False

    def _check_for_scroll_up(self) -> bool:
        """

        Checks if up scroll is necessary.

        Returns
        -------
        boolean
            True: recenter

        """
        top_boundary = self.bottom_offset + SCREEN_HEIGHT - VIEWPOINT_MARGIN
        if self._centre_sprite.top > top_boundary:
            self.bottom_offset += self._centre_sprite.top - top_boundary
            return True
        return False

    def _check_for_scroll_down(self) -> bool:
        """

        Checks if down scroll is necessary.

        Returns
        -------
        boolean
            True: recenter

        """
        bottom_boundary = self.bottom_offset + VIEWPOINT_MARGIN
        if self._centre_sprite.bottom < bottom_boundary:
            self.bottom_offset -= bottom_boundary - self._centre_sprite.bottom
            return True
        return False


class DrillDungeonGame(arcade.View):
    """
    Contains the game logic.

    Methods
    -------
    setup(number_of_coal_patches: int, number_of_gold_patches: int, number_of_dungeons: int, center_x: int, center_y: int)
        Set up game and initialize variables.
    draw_next_map_layer()
        Generates and loads the next layer of the map when drilling down.
    draw_previous_layer()
        Generates and loads previous layer before drill down action has been performed.
    update_map_configuration()
        Updates the map's configuration specs for the next layer, allowing for increased difficulty.
    on_draw()
        Draws map.
    load_map_layer_from_matrix(map_layer_matrix: List)
        Loads a map from a layer matrix.
    fill_row_with_terrain(map_row: list, y_block_center: Union[float, int], block_width: Union[float, int], block_height: Union[float, int])
        Fills a row with terrain.
    on_key_press(key: int, modifiers: int)
        If key is pressed, it sets that key in self.keys_pressed dict to True.
    on_key_release(key: int, modifiers: int)
        If key is released, sets that key in self.keys_pressed dict to False.
    on_mouse_motion(x: float, y: float, dx: float, dy: float)
        Handles mouse motion.
    on_mouse_press(x: float, y: float, button: int, modifiers: int)
        Executes logic when mouse key is pressed.
    on_mouse_release(x: float, y: float, button: int, modifiers: int)
        Executes logic when mouse key is released.
    reload_chunks()
        Loads fresh set of chunks.
    on_update(delta_time: float)
        Method is called by the arcade library every iteration. Provides basis for game running time.

    """
    # This builds a dictionary of all possible keys that arcade can register as 'pressed'.
    # They unfortunately don't have another method to get this, and populating it before init is not taxing.
    possible_keys = {value: key for key, value in arcade.key.__dict__.items() if not key.startswith('_')}

    def __init__(self, window) -> None:
        """

        Parameters
        ----------
        window: entity
            Window to be shown to the player.

        """
        super().__init__()
        self.game_window = window
        self.keys_pressed = {key: False for key in arcade.key.__dict__.keys() if not key.startswith('_')}

        self.sprites = None
        self.upwards_layer = None
        self.downwards_layer = None
        # Initialize scrolling variables
        self.view = View()

        self.drill_up = False
        self.drill_down = False
        self.current_layer = 0

        self.gold_per_layer = 20
        self.coal_per_layer = 20
        self.dungeons_per_layer = 3

        self.frame = 0
        self.time = 0
        arcade.set_background_color(arcade.color.BLACK)
        # self.firing_mode = ShotType.SINGLE
        self.mouse_position = (1, 1)

        self.vignette = ObscuredVision()

    def setup(self, number_of_coal_patches: int = 20, number_of_gold_patches: int = 20,

              number_of_dungeons: int = 3, number_of_shops: int = 20,
              center_x: int = 128, center_y: int = 128) -> None:
        """

        Set up game and initialize variables.

        Parameters
        ----------
        number_of_coal_patches  : int
            Number of coal patches to be created.
        number_of_gold_patches  : int
            Number of gold patches to be created.
        number_of_dungeons      : int
            Number of dungeon rooms to be created.
        center_x                : int
            x-coordinate of the center.
        center_y                : int
            y-coordinate of the center.

        """
        dirt_list = arcade.SpriteList()
        border_wall_list = arcade.SpriteList()
        shop_list = arcade.SpriteList()
        coal_list = arcade.SpriteList()
        gold_list = arcade.SpriteList()
        explosion_list = arcade.SpriteList()
        entity_list = arcade.SpriteList()
        drill_list = arcade.SpriteList()
        enemy_list = arcade.SpriteList()
        bullet_list = arcade.SpriteList()

        #TODO fix this so that stats arent reset on drill down
        drill = Drill(center_x=center_x, center_y=center_y, current_health=100, max_health=100,
                      ammunition=400, coal=30, gold=0)
        all_blocks_list = arcade.SpriteList()
        destructible_blocks_list = arcade.SpriteList()
        indestructible_blocks_list = arcade.SpriteList()
        self.sprites = SpriteContainer(drill=drill, dirt_list=dirt_list, border_wall_list=border_wall_list,
                                       shop_list=shop_list, coal_list=coal_list, gold_list=gold_list,
                                       explosion_list=explosion_list, entity_list=entity_list,
                                       drill_list=drill_list,
                                       enemy_list=enemy_list,
                                       bullet_list=bullet_list,
                                       all_blocks_list=all_blocks_list,
                                       destructible_blocks_list=destructible_blocks_list,
                                       indestructible_blocks_list=indestructible_blocks_list)
        # generate one enemy
        enemy_one = SpaceshipEnemy(300, 300, vision=200, speed=0.7)
        enemy_two = SpaceshipEnemy(500, 400, vision=200, speed=0.7)
        enemy_three = SpaceshipEnemy(300, 50, vision=200, speed=0.7)
        self.sprites.entity_list.append(enemy_one)
        self.sprites.entity_list.append(enemy_two)
        self.sprites.entity_list.append(enemy_three)
        self.sprites.drill_list.append(self.sprites.drill)

        self.sprites.enemy_list.append(enemy_one)
        self.sprites.enemy_list.append(enemy_two)
        self.sprites.enemy_list.append(enemy_three)

        # Initialize the map layer with some dungeon
        map_layer = MapLayer()

        map_layer_configuration = map_layer.get_full_map_layer_configuration(number_of_dungeons, number_of_coal_patches, number_of_gold_patches, number_of_shops)
        #Test out the chunk manager functionality
        self.block_grid = BlockGrid(map_layer_configuration, self.sprites)
        # self.cmanager = ChunkManager(map_layer_configuration)
        # self.cmanager._update_chunks(center_x, center_y)
        # for active_chunk in self.cmanager.active_chunks:
        #     self.sprites.extend(self.cmanager.chunks_dictionary[active_chunk].chunk_sprites)
        for entity in (*self.sprites.entity_list, self.sprites.drill):
            entity.setup_collision_engine([self.sprites.indestructible_blocks_list])


        # Set viewpoint boundaries - where the drill currently has scrolled to
        self.view.left_offset = 0
        self.view.bottom_offset = 0

    def draw_next_map_layer(self) -> None:
        """

        Generates and loads the next layer of the map when drilling down

        """
        self.upwards_layer = self.cmanager
        if self.downwards_layer == None:
            self.setup(self.coal_per_layer,
                       self.gold_per_layer,
                       self.dungeons_per_layer,
                       self.sprites.drill.center_x,
                       self.sprites.drill.center_y)

            self.update_map_configuration()


        else:
            self.cmanager = self.downwards_layer
            self.downwards_layer = None

        self.current_layer += 1

        arcade.start_render()
        self.sprites.dirt_list.draw()
        self.sprites.border_wall_list.draw()
        self.sprites.coal_list.draw()
        self.sprites.gold_list.draw()
        self.sprites.drill.draw()
        self.sprites.explosion_list.draw()

    def draw_previous_layer(self) -> None:
        """

        Generates and loads previous layer before drill down action has been performed.

        """
        print(self.upwards_layer)
        self.current_layer -= 1
        self.downwards_layer = self.cmanager
        self.cmanager = self.upwards_layer
        self.upwards_layer = None

        arcade.start_render()
        self.sprites.dirt_list.draw()
        self.sprites.border_wall_list.draw()
        self.sprites.shop_list.draw()
        self.sprites.coal_list.draw()
        self.sprites.gold_list.draw()
        self.sprites.drill.draw()
        self.sprites.explosion_list.draw()

    def update_map_configuration(self) -> None:
        """

        Updates the map's configuration specs for the next layer, allowing for
        increased difficulty.

        """
        self.coal_per_layer = generate_next_layer_resource_patch_amount(self.current_layer)
        self.gold_per_layer = generate_next_layer_resource_patch_amount(self.current_layer)
        self.dungeons_per_layer = generate_next_layer_dungeon_amount(self.current_layer)

    def on_draw(self) -> None:
        """

        Draws the map.

        """
        arcade.start_render()
        self.block_grid.air_blocks.draw()
        self.sprites.dirt_list.draw()
        self.sprites.coal_list.draw()
        self.sprites.gold_list.draw()
        self.sprites.border_wall_list.draw()
        self.sprites.shop_list.draw()
        self.sprites.explosion_list.draw()

        for entity in (*self.sprites.entity_list, *self.sprites.bullet_list, self.sprites.drill):
            entity.draw()

        # for entity in self.sprites.entity_list:
        #     if entity.path:
        #         arcade.draw_line_strip(entity.path, arcade.color.BLUE, 2)

        self.vignette.draw(self.sprites.drill.center_x, self.sprites.drill.center_y)

        hud = f"Ammunition: {self.sprites.drill.inventory.ammunition}\nCoal:{self.sprites.drill.inventory.coal}" \
              f"\nGold:{self.sprites.drill.inventory.gold}\nHealth:{self.sprites.drill.current_health}"
        # update hud with screen scroll
        arcade.draw_text(hud, self.view.left_offset + 10, self.view.bottom_offset + 20, arcade.color.BLACK, 20)

    def load_map_layer_from_matrix(self, map_layer_matrix: List) -> None:
        """

        Loads a map from a layer matrix.

        Parameters
        ----------
        map_layer_matrix: List[]
             A matrix containing the map configuration, as generated by the MapLayer class.

        """
        map_layer_height = len(map_layer_matrix)
        map_layer_width = len(map_layer_matrix[0])
        block_height = MAP_HEIGHT / map_layer_height
        block_width = MAP_WIDTH / map_layer_width
        y_block_center = 0.5 * block_height
        for row in map_layer_matrix:
            self.fill_row_with_terrain(row, y_block_center, block_width, block_height)
            y_block_center += block_height

    def fill_row_with_terrain(self, map_row: list, y_block_center: Union[float, int], block_width: Union[float, int],
                              block_height: Union[float, int]) -> None:
        """

        Fills a row with terrain.

        Parameters
        ----------
        map_row         : List[]
            A row of the map matrix.
        y_block_center  : Union[float, int]
            The y of the center of the blocks for the row.
        block_width     : Union[float, int]
            Width of the blocks to fill the terrain.
        block_height    : Union[float, int]
            Height of the blocks to fill the terrain.

        """
        x_block_center = 0.5 * block_width
        for item in map_row:
            wall_sprite = None
            if item == 'X':  # Dirt
                wall_sprite = arcade.Sprite(":resources:images/tiles/grassCenter.png", 0.18)
                # wall_sprite.width = blockWidth
                # wall_sprite.height = blockHeight
                wall_sprite.center_x = x_block_center
                wall_sprite.center_y = y_block_center
                self.sprites.dirt_list.append(wall_sprite)
                self.sprites.destructible_blocks_list.append(wall_sprite)
            if item == 'C':  # Coal
                wall_sprite = arcade.Sprite("resources/images/material/Coal_square.png", 0.03)
                # wall_sprite.width = blockWidth
                # wall_sprite.height = blockHeight
                wall_sprite.center_x = x_block_center
                wall_sprite.center_y = y_block_center
                self.sprites.coal_list.append(wall_sprite)
                self.sprites.destructible_blocks_list.append(wall_sprite)
            if item == 'G':  # Gold
                wall_sprite = arcade.Sprite("resources/images/material/Gold_square.png", 0.03)
                wall_sprite.center_x = x_block_center
                wall_sprite.center_y = y_block_center
                self.sprites.gold_list.append(wall_sprite)
                self.sprites.destructible_blocks_list.append(wall_sprite)
            if item == 'O':  # Border block.
                wall_sprite = arcade.Sprite(":resources:images/tiles/grassMid.png", 0.18)
                wall_sprite.center_x = x_block_center
                wall_sprite.center_y = y_block_center
                self.sprites.border_wall_list.append(wall_sprite)
                self.sprites.indestructible_blocks_list.append(wall_sprite)
            if item == 'S':  # Shop.
                wall_sprite = arcade.Sprite("resources/images/shop/shop.png", 0.18)
                wall_sprite.center_x = x_block_center
                wall_sprite.center_y = y_block_center
                self.sprites.shop_list.append(wall_sprite)
                self.sprites.indestructible_blocks_list.append(wall_sprite)
            if wall_sprite is not None:
                self.sprites.all_blocks_list.append(wall_sprite)
            x_block_center += block_width

    def on_key_press(self, key: int, modifiers: int) -> None:
        """

        If a key is pressed, it sets that key in self.keys_pressed dict to True, and passes the dict onto
        every entity that requires this information.

        Notes
        -----
        For example, all that subclass ControllableMixin.
        This will probably just be the drill...
        but maybe we want controllable minions?

        Parameters
        ----------
        key         : int
            Key of self.keys_pressed
        modifiers   : int
            Modifier value.

        """
        key_stroke = self.possible_keys.get(key)
        if key_stroke is None:
            return

        self.keys_pressed[key_stroke] = True
        for entity in (*self.sprites.entity_list, self.sprites.drill):
            if issubclass(entity.__class__, ControllableMixin):
                entity.handle_key_press_release(self.keys_pressed)

        if self.keys_pressed['T']:
            # Drill down to the next layer.
            self.drill_down = True

        elif self.keys_pressed['ESCAPE']:
            # pause game
            self.keys_pressed = {key:False for key in self.keys_pressed}
            self.sprites.drill.stop_moving()
            pause_menu = PauseMenu(self, self.window, self.view)
            self.window.show_view(pause_menu)

        elif self.keys_pressed['U']:
            if not self.upwards_layer == None:
                self.drill_up = True
            else:
                print("No saved upwards layer")

        # DEBUGGING CONTROLS
        elif self.keys_pressed['O']:
            self.vignette.increase_vision()

        elif self.keys_pressed['L']:
            self.vignette.decrease_vision()

        elif self.keys_pressed['K']:
            self.vignette.blind()

        elif self.keys_pressed['SEMICOLON']:
            self.vignette.far_sight()

    def on_key_release(self, key: int, modifiers: int) -> None:
        """

        If a key is released, it sets that key in self.keys_pressed dict to False, and passes the dict onto
        every entity that requires this information.

        Parameters
        ----------
        key         : int
            Key of self.keys_pressed
        modifiers   : int
            Modifier value.

        """
        key_stroke = self.possible_keys.get(key)
        if key_stroke is None:
            return

        self.keys_pressed[key_stroke] = False
        for entity in (*self.sprites.entity_list, self.sprites.drill):
            if issubclass(entity.__class__, ControllableMixin):
                entity.handle_key_press_release(self.keys_pressed)

        if self.keys_pressed['T']:
            self.drill_down = False

        elif self.keys_pressed['U']:
            self.drill_up = False

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float) -> None:
        """

        Handle Mouse Motion.

        Parameters
        ----------
        x       : float
            x-coordinate.
        y       : float
            y-coordinate.
        dx      : float
            Change in x-coordinate.
        dy      : float
            Change in y-coordinate.

        """
        self.mouse_position = (x, y)

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int) -> None:
        """

        Detects when button on mouse is pressed.

        Parameters
        ----------
        x           : float
            x-coordinate.
        y           : float
            y-coordinate.
        button      : int
            Button pressed.
        modifiers   : int
            Modifier value.

        """
        for shop in self.sprites.shop_list:
            if shop.collides_with_point((self.view.left_offset+x,self.view.bottom_offset+y,)) and \
               (arcade.get_distance_between_sprites(shop, self.sprites.drill)<70):
                self.sprites.drill.stop_moving()
                self.keys_pressed = {key: False for key in self.keys_pressed}
                shop = ShopMenu(self, self.window, self.view)
                self.window.show_view(shop)

        for entity in (*self.sprites.entity_list, self.sprites.drill):
            if issubclass(entity.__class__, ControllableMixin):
                entity.handle_mouse_click(button)

    def on_mouse_release(self, x: float, y: float, button: int, modifiers: int) -> None:
        """

        Detects when button on mouse is released.

        Parameters
        ----------
        x           : float
            x-coordinate.
        y           : float
            y-coordinate.
        button      : int
            Button pressed.
        modifiers   : int
            Modifier value.

        """
        for entity in (*self.sprites.entity_list, self.sprites.drill):
            if issubclass(entity.__class__, ControllableMixin):
                entity.handle_mouse_release(button)

    # moved on_update to the end of the main
    def on_update(self, delta_time: float) -> None:
        """

        This method is called by the arcade library every iteration (or frame).

        Notes
        -----
        We can add these up each time this function is called
        to get the 'running time' of the game.

        Parameters
        ----------
        delta_time  : float
            Time since last iteration

        """
        self.frame += 1
        self.time += delta_time

        # Check for side scrolling
        self.view.update(self.sprites.drill)

        # TODO move this into entities.Drill.update(). We need to pass view as a param to update()
        self.sprites.drill.children[0].aim(self.mouse_position[0] + self.view.left_offset,
                                           self.mouse_position[1] + self.view.bottom_offset)

        for entity in (*self.sprites.entity_list, *self.sprites.bullet_list, self.sprites.drill):
            # pass the sprite Container so update function can interact with other sprites.
            entity.update(self.time, delta_time, self.sprites, self.block_grid)

        self.sprites.explosion_list.update()

        if self.drill_down:
            self.draw_next_map_layer()
            self.drill_down = False

        if self.drill_up:
            self.draw_previous_layer()
            self.drill_up = False

        for bullet in self.sprites.bullet_list:
            if bullet.center_x > self.game_window.width + self.view.left_offset or bullet.center_x < self.view.left_offset or \
                    bullet.center_y > self.game_window.width + self.view.bottom_offset or \
                    bullet.center_y < self.view.bottom_offset:
                bullet.remove_from_sprite_lists()

        # TODO don't use frame as measure of doing task every x loops. Store a variable in each entity class such
        # as last_updated. We can iterate over all entities and check when entity tasks were last updated.
        # if self.frame % 30 == 0:  # Do something every 30 frames.
        #     for entity in self.sprites.entity_list:
        #         # When this gets moved to entity.update(), we won't need to do all this isinstance checks
        #         # We only have this code here now as it isn't abstracted yet.
        #         if isinstance(entity, (PathFindingMixin, ShootingMixin)) and \
        #                 entity.has_line_of_sight_with(self.sprites.drill, self.sprites.all_blocks_list):
        #             if isinstance(entity, PathFindingMixin):
        #                 entity.path_to_position(*self.sprites.drill.position, self.sprites.destructible_blocks_list)
        #             if isinstance(entity, ShootingMixin):
        #                 entity.shoot(ShotType.SINGLE)
