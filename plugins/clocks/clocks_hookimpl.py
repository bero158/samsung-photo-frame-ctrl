import plugins
import imgutils
from slideshow import SlideShow

from PIL import Image
import time
import remi.gui as gui

PLUGIN_NAME = "CLOCKS"
class Clocks:
    currentImage : Image
    app : SlideShow
    shownTime : str = ""
    textColor : str = "#F5F5DC"
    fontSize : int = 200
    def getTime(self) -> str:
        text : str = time.strftime('%H:%M' if self.app.cfg.CLOCKS.FORMAT == "24h" else '%l:%M')
        return text
    def showTime(self):
        size = self.app.cfg.FRAME.IMG_SIZE
        text : str = self.getTime()
        self.app.image = imgutils.drawText(text=text, size=size, fontSize=self.fontSize, textColor=self.textColor, align=(imgutils.HAlign.CENTER, imgutils.VAlign.CENTER), bgImage=self.app.image)
        self.shownTime = text
    
    # remote UI
    def setRemote(self):
        self.lblColor = gui.Label('Color:', style={'text-align':'Left'})
        self.remote_colorPicker = gui.ColorPicker(default_value=self.textColor)
        self.lblSize = gui.Label(f'Size: {self.fontSize} px', style={'text-align':'Left'})
        self.remote_fontSize = gui.Slider(self.fontSize, 50, 500, 10, width=200, height=10, margin='1px')
            
        # setting the listener for the onclick event of the button
        self.remote_colorPicker.onchange.do(self.on_remote_colorPicker_changed)
        self.remote_fontSize.onchange.do(self.on_remote_fontSize_changed)
        return [self.lblColor, self.remote_colorPicker, self.lblSize, self.remote_fontSize]
    
    def setSizeText(self):
        if hasattr(self, "lblSize"):
            self.lblSize.set_text(f'Size: {self.fontSize} px')
    
    def on_remote_colorPicker_changed(self, widget, value):
        self.textColor = value
        self.app.setStage(self.app.Stage.RESIZE)
    
    def on_remote_fontSize_changed(self, widget, value):
        self.fontSize = int(value)
        self.app.setStage(self.app.Stage.RESIZE)
        self.setSizeText()


@plugins.hookimpl
def startup(app):
    clocks = Clocks()
    clocks.app = app
    app.clocksPlugin = clocks

@plugins.hookimpl
def exit(app):
    return None

@plugins.hookimpl
def imageChangeBefore(app : SlideShow) -> None:
    app.clocksPlugin.currentImage=app.image
    app.clocksPlugin.showTime()

@plugins.hookimpl
def do(app : SlideShow) -> None:
    clocks : Clocks = app.clocksPlugin
    now = clocks.getTime()
    if now != clocks.shownTime:
        app.setStage(app.Stage.RESIZE)

@plugins.hookimpl
def loadCfg(app) -> None:
    """called before startup
    Placeholder for plugin default settings
    Use app.loadCfg(PLUGIN_NAME, dict_with_config):
    """
    defaultConfig = {
        "FORMAT" : "24h",
        "FILL" : "white"
    }
    app.loadCfg(PLUGIN_NAME, defaultConfig)

@plugins.hookimpl
def setRemote(app):
    """For setting web based remote from plugins. Returns list of remi.Widgets"""
    return 'Clocks',app.clocksPlugin.setRemote()