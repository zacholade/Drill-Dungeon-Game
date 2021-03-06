from typing import Union

import arcade

from ..bullet import Bullet
from ..entity import Entity
from ...map import BLOCK
from ...particles.explosion import ParticleGold, Smoke, ParticleCoal, ParticleDirt, ParticleShield
from ...utility import make_explosion_particles


class BlueNormalBullet(Bullet):
    def __init__(self, parent: Entity, relative_x: Union[float, int] = 0.0, relative_y: Union[float, int] = 0.0,
                 angle: float = 0.0, speed: Union[float, int] = 3) -> None:
        """

        Represents a basic blue bullet.
        Removed upon collision.
        Damages and makes explosion particles.

        Parameters
        ----------
        parent      :   Entity
            The entity that created fired this bullet.
        relative_x  :   Union[float, int]
            The x position, relative to the parent to spawn the bullet at.
        relative_y  :   Union[float, int]
            The y position, relative to the parent to spawn the bullet at.
        angle       :   float
            The starting angle that the bullet should be facing when shot.
        speed       :   Union[float, int]
            The speed that the bullet will travel at.

        Methods
        -------
        on_collision(sprite:arcade.Sprite, time: float, sprites)
            Bullet specific collision logic.

        """
        base_sprite = ":resources:images/space_shooter/laserBlue01.png"
        sprite_scale = 0.4
        damage = 15
        super().__init__(base_sprite, sprite_scale, parent, relative_x=relative_x, relative_y=relative_y,
                         speed=speed, angle=angle, damage=damage)

    def on_collision(self, sprite: arcade.Sprite, time: float, sprites, block_grid) -> None:
        """
        Bullet specific logic to do when it collides with another object.
        This bullet creates explosion particles as well as hurting the colliding sprite if it has a health attribute.

        Parameters
        ----------
        sprite  :   arcade.Sprite
            The sprite that the Entity collided with.
        time    :   float
            The time that the collision happened.
        sprites :   SpriteContainer
            The SpriteContainer class which contains all sprites so we can interact and do calculations with them.
        block_grid : BlockGrid
            Reference to all blocks in the game.

        """
        if type(sprite) == BLOCK.GOLD:
            make_explosion_particles(ParticleGold, sprite.position, time, sprites)
            block_grid.break_block(sprite, sprites)
            self.remove_from_sprite_lists()

        elif type(sprite) == BLOCK.COAL:
            make_explosion_particles(ParticleCoal, sprite.position, time, sprites)
            smoke = Smoke(50)
            smoke.position = sprite.position
            sprites.explosion_list.append(smoke)
            block_grid.break_block(sprite, sprites)
            self.remove_from_sprite_lists()

        elif type(sprite) == BLOCK.DIRT:
            make_explosion_particles(ParticleDirt, sprite.position, time, sprites)
            block_grid.break_block(sprite, sprites)
            self.remove_from_sprite_lists()

        elif sprite in sprites.indestructible_blocks_list:
            make_explosion_particles(ParticleDirt, sprite.position, time, sprites)
            self.remove_from_sprite_lists()

        # The second and statement here makes sure the bullet doesnt belong to the sprite that shot it.
        elif sprite in (*sprites.enemy_list, sprites.drill):
            # Little check to make sure the bullet isn't hitting the turret or any parent. Bullets spawn inside this.
            if sprite in self.get_all_parents:
                return

            if hasattr(sprite, 'shield_enabled') and sprite.shield_enabled is True:
                make_explosion_particles(ParticleShield, sprite.position, time, sprites)
                self.remove_from_sprite_lists()

            else:

                make_explosion_particles(ParticleDirt, sprite.position, time, sprites)
                smoke = Smoke(50)
                smoke.position = sprite.position
                sprites.explosion_list.append(smoke)

                self.remove_from_sprite_lists()
                if hasattr(sprite, 'hurt'):
                    sprite.hurt(self.damage)

class FireBall(Bullet):
    def __init__(self, parent: Entity, relative_x: Union[float, int] = 0.0, relative_y: Union[float, int] = 0.0,
                 angle: float = 0.0, speed: Union[float, int] = 2) -> None:
        """

        Represents a fireball.
        Removed upon collision.
        Damages and makes explosion particles.

        Parameters
        ----------
        parent      :   Entity
            The entity that created fired this bullet.
        relative_x  :   Union[float, int]
            The x position, relative to the parent to spawn the bullet at.
        relative_y  :   Union[float, int]
            The y position, relative to the parent to spawn the bullet at.
        angle       :   float
            The starting angle that the bullet should be facing when shot.
        speed       :   Union[float, int]
            The speed that the bullet will travel at.

        Methods
        -------
        on_collision(sprite:arcade.Sprite, time: float, sprites)
            Bullet specific collision logic.

        """
        base_sprite = "resources/images/weapons/fireball.png"
        sprite_scale = 0.4
        damage = 15
        super().__init__(base_sprite, sprite_scale, parent, relative_x=relative_x, relative_y=relative_y,
                         speed=speed, angle=angle, damage=damage)

    def on_collision(self, sprite: arcade.Sprite, time: float, sprites, block_grid) -> None:
        """
        Bullet specific logic to do when it collides with another object.
        This bullet creates explosion particles as well as hurting the colliding sprite if it has a health attribute.

        Parameters
        ----------
        sprite  :   arcade.Sprite
            The sprite that the Entity collided with.
        time    :   float
            The time that the collision happened.
        sprites :   SpriteContainer
            The SpriteContainer class which contains all sprites so we can interact and do calculations with them.
        block_grid : BlockGrid
            Reference to all blocks in the game.

        """
        if type(sprite) == BLOCK.GOLD:
            make_explosion_particles(ParticleGold, sprite.position, time, sprites)
            block_grid.break_block(sprite, sprites)
            self.remove_from_sprite_lists()

        elif type(sprite) == BLOCK.COAL:
            make_explosion_particles(ParticleCoal, sprite.position, time, sprites)
            smoke = Smoke(50)
            smoke.position = sprite.position
            sprites.explosion_list.append(smoke)
            block_grid.break_block(sprite, sprites)
            self.remove_from_sprite_lists()

        elif type(sprite) == BLOCK.DIRT:
            make_explosion_particles(ParticleDirt, sprite.position, time, sprites)
            block_grid.break_block(sprite, sprites)
            self.remove_from_sprite_lists()

        elif sprite in sprites.indestructible_blocks_list:
            make_explosion_particles(ParticleDirt, sprite.position, time, sprites)
            self.remove_from_sprite_lists()

        # The second and statement here makes sure the bullet doesnt belong to the sprite that shot it.
        elif sprite in (*sprites.enemy_list, sprites.drill):
            # Little check to make sure the bullet isn't hitting the turret or any parent. Bullets spawn inside this.
            if sprite in self.get_all_parents:
                return

            if hasattr(sprite, 'shield_enabled') and sprite.shield_enabled is True:
                make_explosion_particles(ParticleShield, sprite.position, time, sprites)
                self.remove_from_sprite_lists()

            else:

                make_explosion_particles(ParticleDirt, sprite.position, time, sprites)
                smoke = Smoke(50)
                smoke.position = sprite.position
                sprites.explosion_list.append(smoke)

                self.remove_from_sprite_lists()
                if hasattr(sprite, 'hurt'):
                    sprite.hurt(self.damage)
