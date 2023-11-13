from character import Character
from llm import LLM

class Conversation():
    def __init__(self, characters, setup):
        assert type(characters) == list, "Must pass a list of characters"
        assert len(characters) > 0, "Character list is empty"
        
        for i in range(len(characters)):
            for j in range(i+1, len(characters)):
                assert characters[i] != characters[j], "List contains duplicate characters"
        
        self.characters = characters
        self.current_speaker_index = 0

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
        self.current_speaker_index += 1
        self.current_speaker_index %= len(characters)
        
        return character.name, response

if __name__ == "__main__":
    model = LLM()
    characters = [Character("src/assets/Bazza_Summerwood.json", model), Character("src/assets/Leanah_Rasteti.json", model)]
    setup = "It is dawn and Bazza has just walked into the empty tavern to find Leanah doing inventory"
    conversation = Conversation(characters, setup)
    
    for i in range(10):
        name, response = conversation.generate_next_message()
        print(f"{name}: {response}")
        print()
