from __future__ import annotations

import arcade

from typing import TYPE_CHECKING, Dict

from ..entity import Entity
from ...map.block import BLOCK

if TYPE_CHECKING:
    from ...sprite_container import SpriteContainer


class DiggingMixin:
    """
    Class that handles the interaction/removal of blocks upon collision.

    Methods
    -------
    update(time: float, delta_time: float, sprites: SpriteContainer, block_grid)
        Keeps track of collisions and removes blocks and updates drill inventory.
    """
    sprite_list: arcade.SpriteList
    children: Dict[str, Entity]

    def update(self, time: float, delta_time: float, sprites: SpriteContainer, block_grid) -> None:
        """
        Checks if this entity collides with any destructible block, and if so destroys it,
        incrementing the inventory accordingly.

        Notes
        -----
        This function is called every game loop iteration for each entity which implements this Mixin.

        Parameters
        ----------
        time       : float
            The time that the game has been running for. We can store this to do something every x amount of time.
        delta_time : float
            The time in seconds since the last game loop iteration.
        sprites    : SpriteContainer
            The SpriteContainer class which contains all sprites so we can interact and do calculations with them.
        block_grid : BlockGrid
            Reference to all blocks in the game.
        """
        blocks_to_remove = []
        destructible_blocks = sprites.destructible_blocks_list
        blocks_to_remove.extend(arcade.check_for_collision_with_list(self, destructible_blocks))
        for block in blocks_to_remove:
            if hasattr(self, 'inventory'):
                if type(block) == BLOCK.COAL:
                    self.inventory.coal += 1  # We found coal!

                elif type(block) == BLOCK.GOLD:
                    self.inventory.gold += 1  # We found gold!

            block_grid.break_block(block, sprites)
