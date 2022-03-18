from ._anvil_designer import Write_LogTemplate
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables

class Write_Log(Write_LogTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Any code you write here will run when the form opens.

  def click_submit(self, **event_args):
    """This method is called when the button is clicked"""
    if self.text_box_1.text == "":
      return
    anvil.server.call('write_log', "CUSTOM~ " + self.text_box_1.text)
    open_form('Home')
    
  def click_cancel(self, **event_args):
    open_form('Home')


