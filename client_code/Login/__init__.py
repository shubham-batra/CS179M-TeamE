from ._anvil_designer import LoginTemplate
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server

class Login(LoginTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Any code you write here will run when the form opens.
    

  def button_1_click(self, **event_args):
    if self.text_box_1.text == "":
      return
    anvil.server.call('update_user_textfile',self.text_box_1.text)
    anvil.server.call('write_log', "Logged in")
    open_form('Home')
    """This method is called when the button is clicked"""
    
    
    pass

