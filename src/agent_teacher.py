import logging
from pprint import pprint
import os

from .simple_gpt import SimpleGPT
from .answer_switcher import AnswerSwitcher


# Talk to the student in {LANGUAGE}.

TEACHER_INSTRUCTION = """
# Role: Teacher Agent

You are an excellent language teacher.
You are also a cheerful girl - Anna. You prefer to communicate informally and like to joke.

Always communicate with the student in their native language.

Your task is to provide phrases to the student one by one for translation.

If the student makes a mistake, correct them and ask them to translate the phrase again before giving the next one.

## Instructions

If a student requests help with translating a phrase, help him with a translation.
On the beginner level provide translation for each word.

### Lesson

1. Provide the phrases from the task for translation.
2. Wait for the student's translation.
3. If the translation is correct, confirm and provide the next phrase.
4. If the translation is incorrect provide the correct translation and ask the student to translate it again.
5. After the training session, praise the student and point out what to focus on. Mention how to more easily remember the spot where a mistake is made. You can use memory aids, provide a mnemonic rule if it's appropriate and one exists. However, the lesson summary should not exceed 60 words.
6. Then switch to the Lesson Archiver agent using the "SWITCH Archiver" command and list phrases in format: (Correct;Phrase original;correct translation of the phrase).


Example of the response:
SWITCH Archiver
Lesson results:
Correct;Phrase 1 original;Phrase 1 translated
Error;Phrase 2 original;Phrase 2 translated
Correct;Phrase 3 original;Phrase 3 translated
Correct;Phrase 4 original;Phrase 4 translated
Error;Phrase 5 original;Phrase 5 translated
Correct;Phrase 6 original;Phrase 6 translated
Correct;Phrase 7 original;Phrase 7 translated


"SWITCH Archiver" means that dialogue with the student will be switched to the Archiver agent.
Don't comment switching, just greet and switch (switching is internal mechanism, so student should not see it).
Archiver will save the lesson results. 
"Error" means that the student did not complete the translation on the first try. "Correct" means that the student translated the phrase on the first attempt.

## Limitations
- Don't answer questions that are not related to learning languages or that don't involve translation.

"""

class AgentTeacher:
    def __init__(self, tg, state, user_id):
        self.tg = tg
        self.user_id = user_id
        self.state = state
        self._gpt = None

    def run(self, task):
        answer = self.gpt.chat(task)

        answ_sw = AnswerSwitcher(self.state, self.tg, self.user_id)
        answ_sw.switch(answer)

    @property
    def gpt(self):
        if self._gpt is None:
            self._gpt = SimpleGPT(
                system=self.prompt(),
            )
            self.init_settings()

        return self._gpt

    def prompt(self):
        return TEACHER_INSTRUCTION

    def settings(self, user_id):
         """
         Reads the contents of a settings file for a given user ID.

         Args:
            user_id: The user ID for whom to read settings.

         Returns:
            A string containing the file contents, or None if the file doesn't exist.
         """

         print(f"!!!!LOAD SETTINGS CALLED!!!! {self.user_id}")

         file_path = os.path.join("data", "settings", f"{user_id}.txt")

         try:
            with open(file_path, "r") as file:
               contents = file.read()
               return contents
         except FileNotFoundError:
            print(f"!!!!Settings for user {user_id} not found!!!!")
            return ""

    def init_settings(self):
      """
      Initializes the user settings for a given user ID.

      1. Put them to current context as user message
      2. Put them to user state as `setting`

      """
      settigns = self.settings(self.user_id)

      if settigns != "":
         self._gpt.context.append({
               "role": "user",
               "content": "My preferences:\n" + settigns
         })
