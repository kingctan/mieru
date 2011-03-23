#!/usr/bin/env python

import pygtk
pygtk.require('2.0')
import gtk
import gobject
import sys
maemo5 = False
if len (sys.argv) > 1:
  firstParam = sys.argv[1]
  if firstParam == "n900":
    maemo5 = True
if maemo5:
  sys.path.append('temp_clutter')
  import hildon
import cluttergtk
import clutter

import declutter
import manga
import maemo5
import options

class Mieru:

  def destroy(self, widget, data=None):
    self.saveState()
    print "mieru quiting"
    gtk.main_quit()

  def __init__(self):
    # restore persistent options
    self.d = {}
    self.options = options.Options(self)

    # class varibales
    self.fullscreen = False
    self.viewport = (0,0,800,480)
    (x,y,w,h) = self.viewport
#    self.continuousReading = self.get('continuousReading',True)
    self.continuousReading = False
    self.fitMode = self.get('fitMode','original')


    # create a new window
    if maemo5:
      self.window = hildon.StackableWindow()
    else:
      self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)

    self.window.resize(w,h)

    # suthodwn when the main window is destroyed
    self.window.connect("destroy", self.destroy)

    # get the platform module
    self.platform = maemo5.Maemo5(self)

    # get the Clutter embed and add it to the window
    self.embed = cluttergtk.Embed()
    self.window.add(self.embed)

    # we need to realize the widget before we get the stage
    self.embed.realize()
    self.embed.show()
    self.embed.connect('key-press-event', self.on_key_press_event)

    # get the stage
    self.stage = self.embed.get_stage()
    self.stage.realize()
    self.stage.set_color("White")

    # activate clutter based buttons
    self.buttons = clutter.Group()
    self.stage.add(self.buttons)
    self.fsButton = None
    self.fsButtonActive = False
    self.fsButtonTimer = None
    self._activateButtons()
    
    self.activeManga = None

    # restore previously saved state (if available)
    self._restoreState()
    
    self.lastPageMotionXY = (0,0)



    # This packs the button into the window (a GTK container).

    self.embed.show()

    # and the window
    self.window.show()

    gtk.main()

  def on_key_press_event(self, embed, event):
    keyName = gtk.gdk.keyval_name(event.keyval)
    if keyName == 'f':
      self.toggleFullscreen()
    elif keyName == 'o':
      self.setFitMode("original")
    elif keyName == 'i':
      self.setFitMode("width")
    elif keyName == 'u':
      self.setFitMode("height")
    elif keyName == 'z':
      self.setFitMode("screen")
    elif keyName == 'n':
      self.platform.startFolderChooser() # TODO: rewrite this for multiplatform ability and file opening
    elif keyName == 'q':
      self.destroy(self.window)
    elif keyName == 'F8':
      if self.activeManga:
        self.activeManga.previous()
    elif keyName == 'F7':
      if self.activeManga:
        self.activeManga.next()
    else:
      print "key: %s" % keyName

  def on_button_press_event(actor, event):
    print "button press event"

  def toggleFullscreen(self, widget=None):
    if self.fullscreen:
      self.window.unfullscreen()
      self.fullscreen = False
    else:
      self.window.fullscreen()
      self.fullscreen = True

  def notify(self, message, icon=""):
    print "notification: %s" % message
    self.platform.notify(message,icon)

  def setFitMode(self, mode):
    self.set('fitMode',mode)
    self.fitMode = mode

    if self.activeManga:
      self.activeManga.updateFitMode()

  def openManga(self, path, startOnPage=0):
    if self.activeManga:
      print "closing previously open manga"
      self.activeManga.close()

    print "opening %s on page %d" % (path,startOnPage)
    self.activeManga = manga.Manga(self, path, startOnPage)
    self.saveState()

  def loadPreviousManga(self):
    if self.continuousReading:
      path = self.activeManga.getNextMangaPath()
      if path:
        self.openManga(path, startOnPage=-1) # start from the last page of the previous manga

  def loadNextManga(self):
    if self.continuousReading:
      path = self.activeManga.getPrevMangaPath()
      if path:
        self.openManga(path, startOnPage=0) # start from the firstpage of the next manga


  def get(self, key, default):
    return self.d.get(key, default)

  def set(self, key, value):
    self.d[key] = value
    self.options.save()

  def saveState(self):
    print "saving state"
    if self.activeManga: # is some manga actually loaded ?
      state = self.activeManga.getState()
      if state['path'] != None: # no need to save mangas with empty path
        self.set('lastOpenMangaState', state)

  def _restoreState(self):
    lastOpenMangaState = self.get('lastOpenMangaState',None)
    if lastOpenMangaState:
      print "restoring last open manga"
      self.activeManga = manga.fromState(self, lastOpenMangaState)

  def _activateButtons(self):
    fsToggleButton = clutter.Texture('icons/view-fullscreen.png')
    (w,h) = fsToggleButton.get_size()
    fsToggleButton.set_size(2*w,2*h)
    fsToggleButton.set_anchor_point(2*w,2*h)
    fsToggleButton.set_reactive(True)
    fsToggleButton.set_opacity(0)

#    self.stage.add(fsToggleButton)
    self.buttons.add(fsToggleButton)
    fsToggleButton.show()
    fsToggleButton.raise_top()

    (x,y,w1,h1) = self.viewport

    fsToggleButton.set_position(w1,h1)

    fsToggleButton.connect('button-release-event',self.do_button_press_event)

    self.fsButton = fsToggleButton

    declutter.animate(self.fsButton,clutter.LINEAR,300,[('opacity',255)])
    gobject.timeout_add(3000,self._hideFSButton, self.fsButton)

#    self.showButton = declutter.Opacity(self.fsButton,clutter.LINEAR, 1000, 255, 0)
#    print self.showButton
#    self.showButton.start()

#    self.fsButton.set_opacity(0)
#    self.animation = self.fsButton.animate(clutter.LINEAR, 1000, 'x', 200)


  def do_button_press_event (self, button, event):
    print "pressed"
    if self.fsButtonActive:
      print "starting hiding"
      self.toggleFullscreen()
#      self._hideFSButton(button)
      self.fsButtonActive = False
    else:
      self.fsButtonActive = True
      declutter.animate(self.fsButton,clutter.LINEAR,300,[('opacity',255)])
      print "showing"
      timer = gobject.timeout_add(2000,self._hideFSButton, button)

  def _hideFSButton(self, button):
    print "hiding"
    self.fsButtonActive = False
    declutter.animate(button,clutter.LINEAR,300,[('opacity',0)])








#  def do_button_press_event(actor, event):
#    print "button press event"
#
#  def on_button_press(actor,event):
#    print actor,event
#
#  def do_button_press_event(self,widget,event):
#    print widget, event

if __name__ == "__main__":
  mieru = Mieru()
