from luwak import settings as Settings 

class GenerationComponent(object):
    """ Base class for components part of the content processing pipeline """

    def __init__(self, settings):
        """ 

        Attributes: 
            settings: path to a directory containing settings file, or instance of Settings dict data.

        """
        if type(settings) == str:
            settings = Settings.load_project_file(settings)

        self.settings = settings


