from __future__ import annotations

from typing import Union

from .bullets import BlueNormalBullet
from .turret import Turret
from ..enemy import Enemy
from ..mixins import DiggingMixin, PathFindingMixin, ShotType


class TankBoss(Enemy, DiggingMixin, PathFindingMixin):
    """

    Represents the Tank boss the player encounters.

    Methods
    -------
    update(time: float, sprites)
        Handles specific update logic of the enemy.

    """
    def __init__(self, center_x: int, center_y: int, vision: Union[float, int],
                 speed: Union[float, int] = 1) -> None:
        """

        Parameters
        ----------
        center_x    :   int
            The starting x position in the map for this entity.
        center_y    :   int
            The starting y position in the map for this entity.
        vision      :   Union[float, int]
            The vision/detection field of the enemy.
        speed       :   Union[float, int]
            The movement speed of the enemy.

        """

        base_sprite: str = "resources/images/enemy/tank.png"
        sprite_scale: float = 0.4
        turret_sprite = "resources/images/enemy/tank_turret.png"
        turret_scale = 0.4
        current_health = 50
        max_health = 50

        super().__init__(base_sprite, sprite_scale, center_x, center_y, speed=speed,
                         current_health=current_health, max_health=max_health)
        PathFindingMixin.__init__(self, vision)
        self.children.append(Turret(turret_sprite, turret_scale, parent=self, bullet_type=BlueNormalBullet,
                                    firing_mode=ShotType.SINGLE))

    def update(self, time: float, delta_time: float, sprites, block_grid) -> None:
        """

        Handles update logic specific to this Enemy.
        Attempts to shoot at and pathfind to the drill every x seconds.

        Note
        ----
        As this function is implemented in an Entity subclass, we need to call super().update() at the end of this
        function so that collision engines are updated accordingly.

        Parameters
        ----------
        time       :   float
            The time that the game has been running for. We can store this to do something every x amount of time.
        delta_time : float
            The time in seconds since the last game loop iteration.
        sprites    :   SpriteContainer
            The SpriteContainer class which contains all sprites so we can interact and do calculations with them.
        block_grid : BlockGrid
            Reference to all blocks in the game.

        """
        if (time - self._last_line_of_sight_check_time) > 1:
            self._last_line_of_sight_check_time = time
            if self.has_line_of_sight_with(sprites.drill, sprites.all_blocks_list):
                self._has_line_of_sight_with_drill = True
            else:
                self._has_line_of_sight_with_drill = False

        if self._has_line_of_sight_with_drill:
            if (time - self._last_shot_time) > 1.5:
                self._last_shot_time = time
                self.children[0].aim(*sprites.drill.position)
                self.children[0].shoot(self.children[0].firing_mode)

            if (time - self._last_pathfind_time) > 1:
                self._last_pathfind_time = time
                self.path_to_position(sprites.drill.center_x, sprites.drill.center_y, sprites.all_blocks_list)

        super().update(time, delta_time, sprites, block_grid)
