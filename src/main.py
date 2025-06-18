from openai import OpenAI
from smdb_logger import Logger, LEVEL
from data import Settings, Statistics, Model, BASE_PATH, path
from smdb_web_server import HTMLServer, UrlData, Protocol, KnownError
from threading import Thread
import templates, static

class Translator:
    settings: Settings
    statistics: Statistics
    openAiAPI: OpenAI
    logger: Logger
    webServer: HTMLServer
    serverThread: Thread
    ready: bool = False

    def init(self):
        self.logger = Logger("GPT-Translater.log", path.join(BASE_PATH, "logs"), level=LEVEL.INFO, use_caller_name=True)
        self.statistics = Statistics.load()

        try:
            self.settings = Settings.load()
        except Exception as ex:
            self.logger.warning("Loading parsing failed, creating default.")
            self.settings = Settings.create_default()
        
        if (not self.settings.valid()):
            self.logger.warning(f"Settings are not set correctly, please take a look at {path.join(BASE_PATH, 'data')}, and fill in correctly!")
            return
        
        self.openAiAPI = OpenAI(api_key=self.settings.api_key)
        self.webServer = HTMLServer(self.settings.host, self.settings.port, path.join(BASE_PATH, "webui"), self.logger, self.settings.webUIName)
        self.init_ui()
        self.ready = True

    def init_ui(self):
        self.webServer.add_url_rule("/", self.index)
        self.webServer.add_url_rule("/stats", self.stats)
        self.webServer.add_url_rule("/translate", self.send_translate, protocol=Protocol.Post)

    def send_translate(self, urlData: UrlData) -> str:
        response = self.openAiAPI.responses.create(
            model=self.settings.model.value,
            instructions=f"Translate the following {self.settings.languages[0]} text to {self.settings.languages[1]} or reverse with a raw and direct tone, while preserving the erotic intent. From now on, only return the original (corrected for grammatical errors) and translated text right under each other, nothing else.{self.settings.extra_context}",
            input=urlData.data.decode(),
            temperature=self.settings.temperature,
            max_output_tokens=self.settings.max_tokens
        )
        self.statistics.add_tokens(response.usage.input_tokens, response.usage.output_tokens)
        self.statistics.save()
        return response.output_text
    
    def index(self, _) -> str:
        return self.webServer.render_template_file("index.html", page_title=self.settings.webUIName, stats=self.stats(0))
    
    def stats(self, _) -> str:
        return f"{self.settings.model.value}|in: {self.statistics.in_tokens}, out: {self.statistics.out_tokens}"

    def start(self):
        self.init()
        if (self.ready):
            self.serverThread = self.webServer.serve_forever_threaded(templates=templates.__dict__, static=static.__dict__, thread_name="UI Thread")

    def stop(self):
        if (self.ready):
            self.webServer.stop()
            self.openAiAPI.close()
    
    def degrade_model(self):
        if (self.settings.model == Model.default):
            self.settings.model = Model.default_mini
        elif (self.settings.model == Model.default_mini):
            self.settings.model = Model.mini
        elif (self.settings.model == Model.normal):
            self.settings.model = Model.default_mini
        self.settings.save()

test = Translator()
test.start()
if (test.ready): input()
test.stop()
