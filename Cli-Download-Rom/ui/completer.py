from prompt_toolkit.completion import Completer, Completion

class CliCompleter(Completer):
    def __init__(self, command_map):
        self.command_map = command_map
        self.main_commands = list(command_map.keys())

    def get_completions(self, document, complete_event):
        text_before_cursor = document.text_before_cursor
        words = text_before_cursor.split()

        if not words:
            return

        current_word = words[-1]
        previous_word = words[-2] if len(words) > 1 else None

        if previous_word in ['-p', '--platforms']:
            for platform in self.command_map.get('search', {}).get('platforms', []):
                if platform.startswith(current_word):
                    yield Completion(platform, start_position=-len(current_word))
            return

        if previous_word in ['-r', '--regions']:
            for region in self.command_map.get('search', {}).get('regions', []):
                if region.startswith(current_word):
                    yield Completion(region, start_position=-len(current_word))
            return

        # Sugerir comandos principais
        if len(words) == 1:
            for command in self.main_commands:
                if command.startswith(current_word):
                    yield Completion(command, start_position=-len(current_word))