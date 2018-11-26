"""This module contains all the rules used to update avatars in a game."""
from abc import ABC, abstractmethod

class _AvatarRule(ABC):
    """Inherit from this class if you want to add a rule to update avatars on a map."""
    
    @abstractmethod
    def apply(self, world_map):
        """Update the avatars inside of the given world_map."""
        raise NotImplementedError

class ScoreRule(_AvatarRule):
    """When an avatar lands on a score location, we increase their score by 1."""
    
    def apply(self, world_map):
        for cell in world_map.score_cells():
            try:
                cell.avatar.score += 1
            except AttributeError:
                pass

class PickupRule(_AvatarRule):
    """When an avatar lands on a cell with a pickup, apply that pickup to the avatar."""

    def apply(self, world_map):
        for cell in world_map.pickup_cells():
            if cell.avatar is not None:
                cell.pickup.apply(cell.avatar)