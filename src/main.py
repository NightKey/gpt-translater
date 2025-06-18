from openai import OpenAI
from smdb_logger import Logger, LEVEL
from data import Settings, Statistics, Model, ApiSettings, BASE_PATH, path
from smdb_web_server import HTMLServer, UrlData, Protocol
from smdb_api import API, Message, Privilege
from threading import Thread
import templates, static

class Translator:
    settings: Settings
    statistics: Statistics
    openAiAPI: OpenAI
    smdbApi: API
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
            self.logger.warning(f"Loading parsing failed, creating default. {ex}")
            self.settings = Settings.create_default()
        
        if (not self.settings.valid()):
            self.logger.warning(f"Settings are not set correctly, please take a look at {path.join(BASE_PATH, 'data')}, and fill in correctly!")
            return
        
        self.openAiAPI = OpenAI(api_key=self.settings.api_key)

        smdb_settings = ApiSettings.load()
        if (smdb_settings.api_key != "SMDB KEY HERE"):
            self.smdbApi = API(smdb_settings.name, smdb_settings.api_key, smdb_settings.ip, smdb_settings.port)
        else: 
            self.smdbApi = None

        self.webServer = HTMLServer(self.settings.host, self.settings.port, path.join(BASE_PATH, "webui"), self.logger, self.settings.webUIName, address_filter=self.address_filter)
        self.init_ui()
        if (self.smdbApi != None):
            self.smdbApi.validate()
        self.ready = True

    def address_filter(self, address: str) -> bool:
        return ".".join(address.split(".")[:-1]) in self.settings.white_list_networks

    def init_ui(self):
        self.webServer.add_url_rule("/", self.index)
        self.webServer.add_url_rule("/stats", self.stats)
        self.webServer.add_url_rule("/translate", self.send_translate, protocol=Protocol.Post)

        if (self.smdbApi != None):
            self.smdbApi.create_function("translate", "Translates the mesage after the command using ChatGPT's different models.\nUSAGE: &translate [message]\nCATEGORY: NETWORK", self.api_translate, privilege=Privilege.OnlyAdmin, needs_arguments=True)
            self.smdbApi.create_function("statistics", "Shows the translator's used model and the token count with an estimated price.\nUSAGE: &statistics\nCATEGORY: NETWORK", self.api_statistics, privilege=Privilege.OnlyAdmin, needs_arguments=False, show_button=True)
    
    def translate(self, input: str) -> str:
        response = self.openAiAPI.responses.create(
            model=self.settings.model.value,
            instructions=f"Translate the following {self.settings.languages[0]} text to {self.settings.languages[1]} or reverse with a raw and direct tone, while preserving the erotic intent. From now on, only return the original (corrected for grammatical errors) and translated text right under each other, nothing else.{self.settings.extra_context}",
            input=input,
            temperature=self.settings.temperature,
            max_output_tokens=self.settings.max_tokens
        )
        self.statistics.add_tokens(response.usage.input_tokens, response.usage.output_tokens)
        self.statistics.save()
        return response.output_text

    def send_translate(self, urlData: UrlData) -> str:
        return self.translate(urlData.data.decode())
    
    def api_translate(self, message: Message) -> None:
        if (message.content == ""):
            self.smdbApi.reply_to_message("A string is required after the command!", message)
            return
        results = self.translate(message.content)
        self.smdbApi.reply_to_message(results, message)
    
    def api_statistics(self, message: Message) -> None:
        self.smdbApi.reply_to_message(self.stats("_"), message)
    
    def index(self, _) -> str:
        return self.webServer.render_template_file("index.html", page_title=self.settings.webUIName, stats=self.stats(0))
    
    def stats(self, _) -> str:
        return f"{self.settings.model.value}|in: {self.statistics.in_tokens}, out: {self.statistics.out_tokens} ~ ${self.statistics.current_cost(self.settings.model)}"

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
