def get_desired_location(self, character, character_summary, world, recent_conversation_history):
    verbose_location_string, adjacent_locations_string, location_observation_string, known_locations_string = world.get_location_context_for_character(character)
    world_context = f"{verbose_location_string}\n{adjacent_locations_string}\n{location_observation_string}\n{known_locations_string}\n"

    prompt = f"""{character_summary}\n\n{world_context}\n\nBased on the above conversation, is {character.name} going somewhere or staying where they are? Start your answer with '{character.name} is...'"""
    
    history = deque(list(recent_conversation_history))

    history.appendleft({"role": "system", "content": f"{self.summary_system_message}"})
    history.append({"role": "user", "content": f"{prompt}", "character": f"user"})

    return self.model.inference_from_history(history, self.name, inference_type="summary")