from ._anvil_designer import Input_LoadTemplate
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables

load_list = []

class Input_Load(Input_LoadTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Any code you write here will run when the form opens.

    # Add button
    next_load_button = Button(text="Next", bold=True, background="rgb(180,180,180)", foreground="rgb(255,255,255)")
    next_load_button.set_event_handler('click', self.click_next)
    confirm_load_button = Button(text="Confirm", bold=True, background="rgb(0,255,0)", foreground="rgb(255,255,255)")
    confirm_load_button.set_event_handler('click', self.click_load)
    cancel_button = Button(text="Cancel", bold=True, background="rgb(255,0,0)", foreground="rgb(255,255,255)")
    cancel_button.set_event_handler('click', self.click_cancel)
    button_row = FlowPanel(align="center", spacing="small")
    button_row.add_component(next_load_button, width=100)
    button_row.add_component(confirm_load_button, width=100)
    button_row.add_component(cancel_button, width=100)
    self.add_component(button_row)

  def click_next(self, **event_args):
    global load_list
    
    load_list.append(self.text_box_1.text)
    anvil.server.call('write_load_containers', load_list)
    self.text_box_1.text = ""

  def click_load(self, **event_args):
    global load_list
    
    if not self.text_box_1.text == "":
      load_list.append(self.text_box_1.text)
      
    anvil.server.call('write_load_containers', load_list)
    anvil.server.call('write_log', "Selected " + str(len(anvil.server.call('load_load_textfile_containers'))) + " containers to load")
    load_list = []
    open_form('Load_Confirm')
  
  
  def click_cancel(self, **event_args):
    open_form('Home')