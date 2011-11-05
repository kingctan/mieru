"""
Mieru hildon UI (for Maemo 5@N900)
"""

from base_platform import BasePlatform

class Harmattan(BasePlatform):
  def __init__(self, mieru):
    BasePlatform.__init__(self)
    self.mieru = mieru

  def notify(self, message, icon=""):
    self.mieru.gui._notify(message, icon)
