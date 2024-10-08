import logging

from .func_gpt import FuncGPT
from .answer_switcher import AnswerSwitcher
from .user_score import UserScore

from src.user_settings import UserSettings

# Настраиваем логгер
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ### Skill 1: Greeting and Introduction

# When the learner greets you, present the following options:

# - Learning Session: Propose starting a learning session.
# - Text Translation: Offer to translate any text they provide.

# If you don't know the settings, ask the user. And then save the settings by calling SWITCH Save Settings.
# Skill to be practiced: translation from Russian to English


MAIN_INSTRUCTION = """
# Your Role

You are a genius in learning foreign languages.
You are also a cheerful girl named Anna, who prefers informal communication and enjoys making jokes.
Always communicate with the student in their native language, which they use to write to you or from settings.

## Skills

### Skill: Learning Facilitation

Your task is to be sure to greet the user with your first message and offer to practice.


You can practice:

As soon as the user says they want to start a lesson, be sure you have already welcomed the user and offered him practice or translation, you can reschedule the conversation using the SWITCH Session Planner command and transfer the user's settings.

You must respond in two ways:
1. With student - write text as usual.
2. To switch to another assistant - write the command "SWITCH [Assistant Name]" on the first line of response. Write on the next line instructions for this assistant.

Important: Do not mix text for student and command to switch.

### Skill: User Settings

User settings looks like this example (each param on new line):
Native language: Ru
Studied language: En
Student level: intermediate

#### Your Assistants

1. Session Planner - Chooses topics, determines difficulty, and plans sessions. assistant_name="Session Planner"
2. Translator - Assists in translating texts. assistant_name="Translator"

#### Assistants Switching

1. Initiating Learning:
    - When the user expresses a desire to start training, find out if the user’s settings are in the correct format. If it already exists, it automatically switches to the Session Planner without asking for confirmation.    
    - Provide the session planner with information about your native and desired language, as well as your level of language proficiency.
2. Text Translation:
   - When the user requests a text translation, automatically switch this task to the Translator without asking for confirmation.
   - When the user requests a text translation, strictly answer "SWITCH Translator".
   - Provide the Translator with the text to translate and targt language.
   - Critical information: DO NOT translate the text yourself, just switch to the Translator automatically.

## Limitations

- This bot is designed exclusively for language learning purposes.
- All interactions and tasks should be related to the student’s language education.
- The bot does not handle non-educational queries or tasks outside the scope of language learning and teaching.
- Communicate with the student in his native language (Native language). If he is not yet identified, speak to him in Russian.

## Answer Examples

### Greeting and Options

Hello! What language are you learning today? 😊

Hi there! Would you like to start a learning session? 🌟

### Switching to Session Planner

SWITCH Session Planner
Plan session for student with native language "English" and desired language "Russian"
Student level is "intermediate", talk to student in his native language: Russian

In this case we know the student's native language and the language they want to learn.


### Switching to Translator

SWITCH Translator
На английский: Здравствуй!

"""


class AgentMain:
    def __init__(self, message, state, user_id):
        self.gpt = None  # FuncGPT(system=MAIN_INSTRUCTION)
        self.message = message
        self.state = state
        self.user_id = user_id
        self.u_settings = UserSettings(user_id)

    async def run(self, message):
        if self.gpt is None:
            await self.init_gpt()
            await self.show_stats()

        answer = self.gpt.chat(message)

        answ_sw = AnswerSwitcher(self.state, self.message, self.user_id)
        await answ_sw.switch(answer, self.state['agent'])

    def save_settings(self, *args, **kwargs):
        
        logger.info("SAVE SETTINGS CALLED")
        logger.info(args[0]['settings'])

        self.u_settings.save(args[0]['settings'])

        #self.init_settings()

        return "Настройки пользователя сохранены:\n " + args[0]['settings']


    def load_settings(self):
        """
        Reads the contents of a settings file for a given user ID.

        Args:
           user_id: The user ID for whom to read settings.

        Returns:
           A string containing the file contents, or None if the file doesn't exist.
        """
        logger.info(f"LOAD SETTINGS CALLED {self.user_id}")

        return self.u_settings.load()


    async def init_settings(self):
        """
        Initializes the user settings for a given user ID.

        1. Put them to current context as user message
        2. Put them to user state as setting

        """
        if 'settings' not in self.state or not self.state['settings']:
            try:
                settings = self.load_settings()

                if settings:
                    self.gpt.context.append({
                        "role": "user",
                        "content": "My preferences:\n" + settings
                    })
                    # Сохраним настройки в self.state, если они существуют
                    self.state['settings'] = self.settings_as_dict(settings)
                else:
                    logger.info("Настройки не найдены. Используем значения по умолчанию.")
            except ValueError as e:
                logger.error(f"ERROR READING SETTINGS FILE: {e}")
                self.u_settings.delete()
            except FileNotFoundError:
                logger.error("Файл настроек не найден.")

        '''
        try:
            settings = self.load_settings()

            if settings:
                self.gpt.context.append({
                    "role": "user",
                    "content": "My preferences:\n" + settings
                })
                # Сохраним настройки в self.state
                self.state['settings'] = self.settings_as_dict(settings)
                #await self.message.answer("Settings:\n" + settings)
            else:
                pass
                #await self.message.answer("Настройки не найдены. Создадим новые...")

        except ValueError as e:
            logger.error(f"ERROR READING SETTINGS FILE: {e}")
            self.u_settings.delete()
            #await self.message.answer("Файл настроек был поврежден и его пришлось удалить. Сейчас создадим новый...")

        except FileNotFoundError:
            logger.error("Файл настроек не найден.")
            try:
                self.u_settings.delete()
            except Exception as e:
                logger.error(f"Ошибка при удалении файла настроек: {e}")
            #await self.message.answer("Файл настроек не найден. Сейчас создадим новый...")
        '''

    async def show_stats(self):
        stats = ""

        statsdict = UserScore(self.user_id).stats()

        for param in statsdict:
            value = statsdict[param]
            stats += f"{param}: {value}\n"

        await self.message.answer(stats)

        return stats

    async def init_gpt(self):
        self.gpt = FuncGPT(system=MAIN_INSTRUCTION)

        await self.init_settings()

        '''
        self.gpt.add_func(
            {
                "type": "function",
                "function": {
                    "name": "save_settings",
                    "description": "Save user settings for language learning",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "settings": {
                                "type": "string",
                                "description": "Settings for language learning, as 4 strings: Native language, Studied language, Student level",
                            },
                        },
                        "required": ["settings"],
                    }
                }
            },
            self.save_settings
        )
        '''

    def settings_as_dict(self, settings: str) -> dict:
        result = {}

        # Разбиваем текст на строки и обрабатываем каждую строку
        for line in settings.strip().split('\n'):
            if line.strip():
                try:
                    # Разбиваем строку по символу ':'
                    key, value = line.split(':', 1)

                    # Удаляем лишние пробелы и добавляем в словарь
                    result[key.strip()] = value.strip()
                except:
                    raise ValueError(f"Line '{line}' is not in the correct format.")

        return result
