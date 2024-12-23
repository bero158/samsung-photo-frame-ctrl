import plugins
from nightmode import Nightmode
PLUGIN_NAME = "NIGHTMODE"

def setMode(app):
    mode = app.nightmode.getMode()
    app.nightmode.checkTTModeChange()
    app.nightmode.setMode(mode)
    app.nightmode.lastMode = mode


@plugins.hookimpl
def exit(app) -> None:
    """called when application is about to quit
    Placeholder for plugin cleanup
    """

@plugins.hookimpl 
def imageLoader(app):
    """called when a new image is required
    Returns ImgLoader desc. object.
    """

@plugins.hookimpl
def imageChangeAfter(app) -> None:
    """called after image was successfuly changed on the screen
    Intended for effects etc. Image is in app.image
    """

@plugins.hookimpl
def imageChangeBeforeEffects(app) -> None:
    """called after image was successfuly changed on the screen
    Intended for effects etc. Image is in app.image
    """
    

@plugins.hookimpl
def startup(app) -> None:
    """called after application start
    Placeholder for plugin initialisation
    """
    app.nightmode = Nightmode()
    app.nightmode.srcTable = app.cfg[PLUGIN_NAME].TIMES
    app.nightmode.createTT(app.nightmode.srcTable)
    app.nightmode.app = app
    app.nightmode.nightBrightness = app.cfg[PLUGIN_NAME].NIGHT_BRIGHTNESS
    app.nightmode.lastMode = Nightmode.MODE.DAY

@plugins.hookimpl
def loadCfg(app) -> None:
    """called before startup
    Placeholder for plugin default settings
    Use app.loadCfg(PLUGIN_NAME, dict_with_config)
    """
    defaultConfig = {
        "NIGHT_BRIGHTNESS" : 10,
        "TIMES" : [("07:00", "day"),("22:00", "night")]
    }
    app.loadCfg(PLUGIN_NAME, defaultConfig) #load the real config and merge it with default values

@plugins.hookimpl
def do(app) -> None:
    """called every second when frame is waiting to next frame.
    Intended for showing real time etc.
    """
    app.nightmode.checkTTModeChange()
    if app.nightmode.lastMode != app.nightmode.getMode():
        setMode(app)

@plugins.hookimpl
def showImage(app) -> bool:
    """called when a new image should be shown. Intended use is for display plugins. Returns success or failure.
    """


@plugins.hookimpl
def setRemote(app):
    """For setting web based remote from plugins. Returns list of remi.Widgets"""
    return 'Night Mode', app.nightmode.setRemote()
    