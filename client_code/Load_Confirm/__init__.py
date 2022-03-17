from ._anvil_designer import Load_ConfirmTemplate
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables

class Load_Confirm(Load_ConfirmTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Any code you write here will run when the form opens.\
    
    label1 = Label(text = "Unload", align="center", bold=True, background = "rgb(180,180,180)", foreground="rgb(0,0,0)")
    label2 = Label(text = "Load", align="center", bold=True, background="rgb(180,180,180)", foreground = "rgb(0,0,0)")
    row = DataRowPanel()
    row.add_component(label1, column=0)
    row.add_component(label2, column=1)
    self.add_component(row)
    
    load_list = anvil.server.call('load_load_textfile')
    unload_list = anvil.server.call('load_unload_textfile')
    
    for row in range(max(len(load_list), len(unload_list))):
      label1_text = ""
      if row < len(unload_list):
        label1_text = unload_list[row]
      label2_text = ""
      if row < len(load_list):
        label2_text = load_list[row]
      
      label1 = Label(text = label1_text, align="center", foreground="rgb(0,0,255)")
      label2 = Label(text = label2_text, align="center", foreground="rgb(0,0,255)")
      row = DataRowPanel()
      row.add_component(label1, column=0)
      row.add_component(label2, column=1)
      self.add_component(row)
    
    confirm_load_button = Button(text="Confirm", bold=True, background="rgb(0,255,0)", foreground="rgb(255,255,255)")
    confirm_load_button.set_event_handler('click', self.click_load)
    cancel_button = Button(text="Cancel", bold=True, background="rgb(255,0,0)", foreground="rgb(255,255,255)")
    cancel_button.set_event_handler('click', self.click_cancel)
    button_row = FlowPanel(align="center", spacing="small")
    button_row.add_component(confirm_load_button, width=100)
    button_row.add_component(cancel_button, width=100)
    self.add_component(button_row)
    
  def click_load(self, **event_args):
    print("hellllo")
    anvil.server.call('load_unload')
  
  
  def click_cancel(self, **event_args):
    open_form('Home')
    
    
5