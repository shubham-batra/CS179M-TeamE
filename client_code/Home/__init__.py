from ._anvil_designer import HomeTemplate
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server

class Home(HomeTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Any code you write here will run when the form opens.

  def backup_button_click(self, **event_args):
    """This method is called when the button is clicked"""
    pass

  def form_show(self, **event_args):
    """This method is called when the HTML panel is shown on the screen"""
    pass

  def balance_button_click(self, **event_args):
    """This method is called when the button is clicked"""
    # Balance the ship when button is clicked
    anvil.server.call('balance')
    open_form('Balance_Slide')
    pass

  def write_log_button_click(self, **event_args):
    #anvil.server.call('say_hello')
    pass
  

  def button_1_show(self, **event_args):
    """This method is called when the Button is shown on the screen"""
    pass


  def file_loader_1_change(self, file, **event_args):
    """This method is called when a new file is loaded into this FileLoader"""
    # For balance function
    result = anvil.server.call('get_file_from_client', file)
    pass

  def load_unload_button_click(self, **event_args):
    """This method is called when the button is clicked"""
    open_form('Unload_Page')
    pass










