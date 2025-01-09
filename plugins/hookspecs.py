import pluggy

hookspec = pluggy.HookspecMarker("slideshow")


@hookspec
def exit(app) -> None:
    """called when application is about to quit
    Placeholder for plugin cleanup
    """

@hookspec() 
def imageLoader(app):
    """called when a new image is required
    Returns ImgLoader desc. object.
    """

@hookspec
def imageChangeAfter(app) -> None:
    """called after image was successfuly changed on the screen
    Intended for effects etc. Image is in app.image
    """

@hookspec
def imageChangeBefore(app) -> None:
    """called after image was successfuly changed on the screen
    Intended for effects etc. Image is in app.image
    """

@hookspec
def startup(app) -> None:
    """called after application start
    Placeholder for plugin initialisation
    """

@hookspec
def loadCfg(app) -> None:
    """called before startup
    Placeholder for plugin default settings
    Use app.loadCfg(PLUGIN_NAME, dict_with_config)
    """

@hookspec
def saveCfg(app) -> None:
    """called before startup
    Placeholder for plugin settings to be stored.
    Use app.saveCfg(PLUGIN_NAME, dict_with_config)
    """

@hookspec
def do(app) -> None:
    """called every second when frame is waiting to next frame.
    Intended for showing real time etc.
    """

@hookspec
def showImage(app) -> bool:
    """called when a new image should be shown. Intended use is for display plugins. Returns success or failure.
    """

@hookspec
def imageChangeBeforeEffects(app):
    """For post-effects aka NightMode. Called after imageChangeBefore and before showImage. Intended use is for global filters.
    """

@hookspec
def brightnessChangeAfter(app, brightness : int) -> None:
    """called after brightness value was changed. Brightness is 0-255
    Intended as a feedback for remote
    """
@hookspec
def ResizeBefore(app):
    """Called before resize"""

@hookspec
def ResizeAfter(app):
    """Called after resize"""

@hookspec
def setRemote(app):
    """For setting web based remote from plugins. Returns list of remi.Widgets"""

@hookspec
def loadAfter(app):
    """Called after successful load"""

@hookspec
def load(app) -> bytes:
    """Get image data. For loaders."""

@hookspec
def setAPI(app):
    """
    Placeholder for setting plugin specific REST API calls.
    Should contain:
    router = APIRouter()
    @router.get("/api_point")
        def api_point():
            return {"message": "Not implemented yet"}
    app.api.registerRouter(PLUGIN_NAME, router)
    """