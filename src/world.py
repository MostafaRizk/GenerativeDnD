import json

from collections import deque
from helpers import *

class Tree:
    def __init__(self, name, description, children):
        self.name = name
        self.description = description
        self.children = children

class World:
    def __init__(self, world_file_path):
        f = open(world_file_path)
        world_map_data = json.load(f)
        f.close()
        self.world_tree = self.recurse_world_tree(world_map_data)
    
    def recurse_world_tree(self, root):
        if len(root["children"]) == 0:
            return Tree(name=root["name"], 
                        description=root["description"], 
                        children=[])
        
        name = root["name"]
        description = root["description"]
        children = [self.recurse_world_tree(child) for child in root["children"]]

        return Tree(name=name, description=description, children=children)
    
    def get_node_from_location_string(self, location_string):
        levels = deque(location_string.split(":"))
        nodes = deque([self.world_tree])
        
        while len(nodes) > 0 and len(levels) > 0:
            curr_node = nodes.popleft()
            curr_level = levels[0]

            if curr_node.name == curr_level:
                levels.popleft()
                for child in curr_node.children:
                    nodes.append(child)
        
        if len(levels) == 0:
            return curr_node
        
        else:
            return None
    
    def get_siblings_from_node(self, node):
        assert self.world_tree != node, "Cannot get siblings of the root node"

        queue = deque([(None, self.world_tree)])

        while len(queue) > 0:
            parent, curr = queue.popleft()
            
            if curr == node:
                return [sibling.name for sibling in parent.children]
            
            for child in curr.children:
                queue.append((curr, child))
    
    def expand_loc_string(self, loc_string, cutoff_index=None):
        if not cutoff_index:
            places = loc_string.split(":")[::-1]
        else:
            places = loc_string.split(":")[cutoff_index+1:][::-1]
        return ", in ".join(places)
    
    def get_location_context_for_character(self, character):
        loc_node = self.get_node_from_location_string(character.location)
        main_location_idx = 1 # Index 0 is the world tree's root node
        main_location = character.location.split(":")[main_location_idx]
        specific_location = self.expand_loc_string(character.location, main_location_idx)
        adjacent_locations = self.get_siblings_from_node(loc_node)
        known_locations = [l.name for l in self.world_tree.children]
    
        verbose_location_string = f"{character.name} is currently in {main_location} (specifically {specific_location})"
        adjacent_locations_string = f"{main_location} contains: {list_entities(adjacent_locations)}"
        location_observation_string = f"{character.name} sees the following:\n{loc_node.description}"
        known_locations_string = f"{character.name} knows about the following locations in {self.world_tree.name}: {list_entities(known_locations)}"
        
        return verbose_location_string, adjacent_locations_string, location_observation_string, known_locations_string