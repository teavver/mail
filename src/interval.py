import threading


class ThreadJob(threading.Thread):
  def __init__(self, callback, event, interval):
    """Runs the callback function after interval seconds.

    :param callback: Callback function to invoke
    :param event: External event for controlling the update operation
    :param interval: Time in seconds after which to fire the callback
    """
    self.callback = callback
    self.event = event
    self.interval = interval
    self.pause_event = threading.Event()
    self.pause_event.set()
    super().__init__()

  def run(self):
    while not self.event.wait(self.interval):
      if self.pause_event.is_set():
        self.callback()

  def pause(self):
    self.pause_event.clear()

  def resume(self):
    self.pause_event.set()
