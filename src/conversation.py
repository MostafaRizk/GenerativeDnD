from character import NonPlayerCharacter, PlayerCharacter, Character
from llm import LLM
from assistant import Assistant
from datetime import datetime
from collections import deque

class Conversation():
    def __init__(self, characters, setup, model):
        assert type(characters) == list, "Must pass a list of characters"
        assert len(characters) > 0, "Character list is empty"
        
        for i in range(len(characters)):
            for j in range(i+1, len(characters)):
                assert characters[i] != characters[j], "List contains duplicate characters"
        
        self.characters = characters
        self.current_speaker_index = 0
        self.buffer_size = 1
        self.conversation_buffer = deque(maxlen=len(characters)*self.buffer_size)
        self.assistant = Assistant(model)

        for character in self.characters:
            character.listen(setup, "", "system")
    
    def add_character(self, character):
        assert type(character) == Character, "The character must be of type Character"
        assert character not in characters, "The character must not already be in the conversation"

        self.characters.append(character)
    
    def remove_character(self, character):
        assert character in self.characters, "The character is not in the conversation"
        
        index_to_remove = self.characters.index(character)
        self.characters.remove(index_to_remove)

        if self.current_speaker_index == index_to_remove:
            self.current_speaker_index %= len(characters)
        
        elif self.current_speaker_index > index_to_remove:
            self.current_speaker_index -= 1
    
    def generate_next_message(self):
        character = self.characters[self.current_speaker_index]
        response = character.speak()
        self.conversation_buffer.append({"role": "assistant", "content": f"{response}", "character": f"{character.name}"})

        for other_character in characters:
            if other_character != character:
                other_character.listen(response, character, "assistant")

        self.current_speaker_index += 1
        self.current_speaker_index %= len(characters)

        observation = self.assistant.get_observation_for_character(self.conversation_buffer, character)
        
        return character.name, response, observation

    
    def is_player_next(self):
        next_speaker = self.characters[self.current_speaker_index]
        if type(next_speaker) == PlayerCharacter:
            return True
        else:
            return False
    
    def get_speaker_name(self):
        next_speaker = self.characters[self.current_speaker_index]
        return next_speaker.name

if __name__ == "__main__":
    model = LLM()
    characters = [NonPlayerCharacter("src/assets/characters/Bazza_Summerwood.json", model), NonPlayerCharacter("src/assets/characters/Leanah_Rasteti.json", model), PlayerCharacter("src/assets/players/Lorde_Moofilton.json")]
    assistant = Assistant(model)
    # plans = [assistant.get_plan_for_character(character) for character in characters if type(character) != PlayerCharacter]
    # current_time = "10:00AM"
    # time_format = "%I:%M%p"
    # current_time = datetime.strptime(current_time, time_format)
    # character_activities = []

    setup = "Bazza and Leanah are having a mellow conversation behind the Red Olive reception desk on a quiet day"
    print(setup)
    print()
    
    conversation = Conversation(characters, setup, model)
    
    while True:
        if conversation.is_player_next():
            name = conversation.get_speaker_name()
            print(f"{name}: ", end="")
            _,_,observation = conversation.generate_next_message()
        else:
            name, response, observation = conversation.generate_next_message()
            print(f"{name}: {response}")
        
        print("----")
        print(observation)
        print("----")
        print()
