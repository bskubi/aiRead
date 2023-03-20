import random, time, os, nltk, re, openai, multiprocessing, timeit

openai_key = open("openai_key.txt").read()
openai.api_key = openai_key

chat_response = "a"

class airController:
    def __init__(self):
        nltk.download('punkt', quiet=True)  # Download the punkt tokenizer if not already downloaded
        self.set = {}
        self.tokens = []
        self.loc = None;
        self.setDefaults()

    def setDefaults(self):
        self.set = {
            "tokenize":True,
            "forward":True,
            "token_count":1,
            "typewriter":False,
            "typewriter_min":.1,
            "typewriter_a":.05,
            "typewriter_b":.3,
            "typewriter_c":.2,
            "typewriter_speed":.05,
            "typewriter_speed_n":10,
            "typewriter_control":2,
            "overlap_moves":False,
            "columns":80,
            "pcls":False,
            "display_loc":True,
            "openai_api_key":openai_key,
            "cheap_model":"gpt-3.5-turbo-0301",
            "fancy_model":"gpt-4"
        }
        

    def move(self, distance = None):
        if distance is None:
            distance = self.set["token_count"]
        if len(self.tokens) == 0:
            self.loc = None
            return
        direction = (self.set["forward"] - (not self.set["forward"]))

        if self.set["overlap_moves"]:
            self.loc += 1
        else:
            self.loc += distance*direction
        self.loc = max(0, self.loc)
        self.loc = min(len(self.tokens)-1, self.loc)

    def display(self, force_text = None, apply_tabs = True):
        if self.loc is None and force_text is None:
            return

        to_display = ""
        if force_text is None:
            if self.set["display_loc"]:
                to_display = str(self.loc) + "\t" + self.currentDisplay()
            else:
                to_display = self.currentDisplay()
        else:
            to_display = force_text

        lines = self._format_lines(to_display)

        if self.set["pcls"]:
            os.system("cls")
        i = 0
        for i in range(len(lines)):
            spacer = "\t" if (force_text is None or apply_tabs) else ""
            if self.set["display_loc"] and i == 0 and force_text is None:
                spacer = ""
            line = spacer + lines[i]
            self._print(line)

    def currentDisplay(self):
        return ' '.join(self.tokens[self.loc:self.loc+self.set["token_count"]])

    def tokenize(self, text):
        self.tokens = nltk.sent_tokenize(text)
        for i in range(len(self.tokens)):
            self.tokens[i] = self.tokens[i].replace('\n', ' ')
        self.loc = 0 if len(self.tokens) > 0 else None

    def _print(self, to_display):
        if self.set["typewriter"]:
            self._typewriter(to_display)
        else:
            print(to_display)
            

    def _typewriter(self, to_display):
        n = 0
        for c in range(len(to_display)):
            if n == 0:
                speed = random.random() < self.set["typewriter_speed"]
                n = self.set["typewriter_speed_n"]*speed

            print(to_display[c], end="", flush=True)
            sec = .04 if n > 0 else 1/self.set["typewriter_control"]*max(.01, self.set["typewriter_a"] + self.set["typewriter_b"]*(.51-random.random()) + self.set["typewriter_c"]*random.random()*random.random())
            time.sleep(sec)
            n = max(n - 1, 0)
        print()

    def _format_lines(self, to_display):
        lines = []
        i = 0
        to_display = to_display.strip()
        remainder = to_display
        while i < len(to_display):
            #Find the next stopping point: a newline, the maximum column length, or the end of the input text. 
            remainder = to_display[i:]
            next_newline = remainder.find('\n')
            text_end = len(remainder)
            col_len = self.set["columns"]
            next_newline = next_newline if next_newline >= 0 else col_len
            stop = min(next_newline, text_end, col_len)

            if stop == 0:
                lines.append('')
                i += 1
                continue

            #Extract the text between the current position and next stopping point
            line = remainder[:stop].strip()
            deleted = stop - len(line)

            #Break that text into words
            line_tok = line.split(' ')

            #If there is only a single word that's the entire maximum column length, break it up into line-length columns until the last piece
            #is shorter than the length of a line.
            if len(line_tok) == 1 and len(line_tok[0]) > col_len:
                line = line_tok[0]
                while len(line) > col_len:
                    lines.append(line[0:col_len])
                    i += col_len
                    line = line[col_len:].strip()
            elif stop == col_len and len(line_tok) > 1:
                #If the remaining text is exactly the maximum column length, move the final word to the next line
                add = ' '.join(line_tok[0:len(line_tok)-1])
                lines.append(add)
                i += len(add) + deleted
            else:
                #Set all the remaining words as the current line and advance the position.
                add = ' '.join(line_tok)
                lines.append(add)
                i += len(add) + deleted
        return lines


class airInterpreter:
    def __init__(self):
        self.controller = airController()
        self.setDefaults()

    def setDefaults(self):
        self.contok = {
            ("*", 0):(self._notes, None),
            (">", 0):(self._skip, {"forward":True, "typewriter":True}),
            ("<", 0):(self._skip, {"forward":False, "typewriter":True}),
            (">>", 0):(self._skip, {"forward":True, "typewriter":False}),
            ("<<", 0):(self._skip, {"forward":False, "typewriter":False}),
            (".", 0):(self._display, None),
            ("..", 0):(self._reverseTypewriter, None),
            ("cls", 0):(self._cls, None),
            ("pcls", 0):(self._pcls, None),
            ("skip", 0):(self._setskip, None),
            ("explain", 0):(self._explain, None),
            ("flashcards", 0):(self._flashcards, None),
            ("twit", 0):(self._twit, None),
            ("tweetstorm", 0):(self._tweetstorm, None),
            ("poem", 0):(self._poem, None),
            ("quiz", 0):(self._quiz, None),
            ("help", 0):(self._help, None)
        }

    def _help(self, i):
        print("aiRead is like having a conversation with your textbook. It breaks it down into bite size morsels, then brings ChatGPT into the mix.")
        print("First, create a file called aiRead.txt containing the material you want to read.")
        print("Stick aiRead.py in the same folder as aiRead.txt, and it will read the aiRead.txt file when you load it up.")
        print("Then, you can navigate through the sentences.")
        print("Press 'enter' to keep moving in the same direction - by default, one sentence forward.")
        print("You can go forward or backward by entering < and << or > and >>.")
        print("Using > will display the text like a typewriter, >> will display it instantly.")
        print("You can control how many sentences get displayed at a time by following the arrows with a number, like >> 2.")
        print("cls will clear the screen, and typing pcls will toggle whether or not to clear the screen automatically between sentences")
        print("Type 'explain' to get a simplified explanation, with all the jargon terms defined")
        print("Type 'quiz' to generate an interactive quiz with 'teacher' feedback")
        print("Type 'twit' to get a twitter hot take version of the material you're on")
        print("Type 'tweetstorm' to get a whole twitter tweetstorm about it - highly recommended!")
        print("Type 'poem' to rewrite the text in the form of a poem")
        print("Type 'help' to display this again. Enjoy!")

    def _display(self, i):
        self.controller.display()

    def _poem(self, i):
        choice = random.choice(["limerick", "ballad", "folk song", "rap battle", "haiku", "free verse", "religious verse"])
        ac._typewriter("Writing a " + choice + "...")
        
        add_prompt = "Rewrite the following as a " + choice + ", making the same point, and keeping it as information-dense as possible.\n\n"""
        content = add_prompt + self.controller.currentDisplay()
        response = self._getChatbotResponse(content, self.controller.set["cheap_model"])
        self.controller.display(response)

    def _cls(self, i):
        os.system("cls")

    def _pcls(self, i):
        self.controller.set["pcls"] = not self.controller.set["pcls"]

    def _setskip(self, i):
        distance = ''.join(x for x in i if x.isdigit())
        if len(distance) > 0:
            distance = int(distance)
            self.controller.set["token_count"] = distance

    def _twit(self, i):
        ac._typewriter("Preparing a tweetstorm...")
        add_prompt = """Rewrite the following as a sassy but semi-serious Twitter hot take, but keep the same content and make the same point.\n\n"""
        content = add_prompt + self.controller.currentDisplay()
        response = self._getChatbotResponse(content, self.controller.set["cheap_model"])
        self.controller.display(response)

    def _tweetstorm(self, i):
        ac._typewriter("Preparing a tweetstorm...")
        add_prompt = """Rewrite the following as a sassy Twitter tweetstorm as written by a scientific expert communicating with the public, with individually numbered tweets, humor throughout, and /thread at the end."""
        content = add_prompt + self.controller.currentDisplay()
        response = self._getChatbotResponse(content, self.controller.set["cheap_model"])
        self.controller.display(response)

    def _explain(self, i):
        ac._typewriter("Preparing explanation...")
        add_prompt = """Reword the following sentence in the same style and tone. Afterward, list all jargon terms with their definitions.
            Finally, describe what the sentence means in conversational, intuitive language.\n\n"""
        content = add_prompt + self.controller.currentDisplay()
        response = self._getChatbotResponse(content, self.controller.set["cheap_model"])
        self.controller.display(response)

    def _quiz(self, i):
        user_reply = ""
        start = self.controller.loc
        mod = self.controller.set["cheap_model"]
        untested = []
        if len(i) > 0 and i.strip != "":
            if i.strip()[0] == ".":
                untested = [start]
            else:
                args = i.split()
                if len(args) == 1:
                    first = int(''.join(x for x in args[0] if x.isdigit()))
                    untested = list(range(first, start+1))
                else:
                    first = int(''.join(x for x in args[0] if x.isdigit()))
                    last = int(''.join(x for x in args[1] if x.isdigit())) + 1
                    untested = list(range(first, last))
        else:
            untested = list(range(self.controller.loc))
        
        while user_reply != "done" and len(untested) > 0:
            os.system("cls") 
            ac._typewriter("\nPreparing a quiz prompt...\n")
            add_prompt = """Generate a single-sentence short-answer quiz prompt on the following material:\n"""
            self.controller.loc = random.choice(untested)
            del untested[untested.index(self.controller.loc)]
            content = add_prompt + self.controller.currentDisplay()
            response = self._getChatbotResponse(content, mod)
            self.controller.display(response)
            user_reply = input("\n'done' = end quiz, 'skip' = new question, 'view' = check source, anything else = answer> ")
            if user_reply == "done":
                break
            if user_reply == "skip":
                continue
            if user_reply == 'view':
                self.controller.display()
                input()
                continue
            content =   "SOURCE MATERIAL: \n" \
                        + self.controller.currentDisplay() \
                        + "QUIZ QUESTION: \n" \
                        + response \
                        + "STUDENT ANSWER: \n" \
                        + user_reply \
                        + "\nEND OF STUDENT ANSWER" \
                        + "\nGRADER FEEDBACK: \n" \

            response = self._getChatbotResponse(content, mod)

            ac._typewriter("\nFinished...\n")
            self.controller.display(response)
            user_reply = input("'done' = end quiz, 'view' = check source, anything else = next question> ")
            if user_reply == 'view':
                self.controller.display()
                input()
        self.controller.loc = start


    def _flashcards(self, i):
        ac._typewriter("Preparing flashcards...")
        add_prompt = """I want you to create a deck of flashcards from the text.
            Instructions to create a deck of flashcards:
            - Keep the flashcards simple, clear, and focused on the most important information.
            - Make sure the questions are specific and unambiguous.
            - Use simple and direct language to make the cards easy to read and understand.
            - Answers should contain only a single key fact/name/concept/term.

            Text:"""
        content = add_prompt + self.controller.currentDisplay()
        response = self._getChatbotResponse(content, self.controller.set["cheap_model"])
        self.controller.display(response)

    def _getChatbotResponse(self, content, bot_model):
        max_tries = 10
        for i in range(max_tries):
            queue = multiprocessing.Queue()
            p = multiprocessing.Process(target = self._requestChatbotResponse, args=(content, bot_model, queue,))
            p.start()

            if self._limitedWait(15, queue):
                return queue.get()
            else:
                print("Trying again...")
                p.terminate()


    def _limitedWait(self, s, queue):
        start = timeit.default_timer()
        while timeit.default_timer() - start < s and queue.empty():
            continue
        return not queue.empty()
        

    def _requestChatbotResponse(self, content, bot_model, queue):
        response =  openai.ChatCompletion.create(
            model=bot_model,
            messages=[{"role": "user", "content": content}],
            max_tokens=1024,
            n=1,
            temperature=0.5,
        )
        queue.put(response["choices"][0]["message"]["content"])

    def _reverseTypewriter(self, i):
        self.controller.set["typewriter"] = not self.controller.set["typewriter"]

    def _skip(self, i):
        self._setskip(i)
        self.controller.move()
        self.controller.display()

    def _notes(self, i):
        pass

    def prompt(self):
        i = input("> ")
        i = i.strip()
        self.extractSettings(i)

    def extractSettings(self, i):
        if len(i) == 0:
            self.controller.move()
            self.controller.display()
            return
        input_tok = i.split(' ')
        for k in self.contok:
            contok = k[0]
            pos = k[1]
            if input_tok[pos] == contok:
                fun = self.contok[k][0]
                settings = self.contok[k][1]
                if settings is not None:
                    self.controller.set.update(settings)
                if fun is not None:
                    args = i[pos+len(contok):]
                    fun(args)


if __name__ == '__main__':
    ac = airController()
    if ac.set["tokenize"]:
        ac.tokenize(open("aiRead.txt", encoding="utf8").read())
    ac.set["typewriter"] = False

    ic = airInterpreter()
    ic.controller = ac
    ic.controller.display()
    while True:
        ic.prompt()