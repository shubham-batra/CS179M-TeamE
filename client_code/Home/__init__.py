from ._anvil_designer import HomeTemplate
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
import anvil.media
from anvil.tables import app_tables
import anvil.server

class Home(HomeTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    
    self.user_label.text = "USER: " + anvil.server.call('load_user_textfile')
    self.manifest_label.text = anvil.server.call('load_input_manifest_path')

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
    anvil.server.call('write_log',"Started balancing " + anvil.server.call('load_input_manifest_path'))
    open_form('Balance_Slide')

  def write_log_button_click(self, **event_args):
    open_form('Write_Log')

  def file_loader_1_change(self, file, **event_args):
    """This method is called when a new file is loaded into this FileLoader"""
    # For balance function
    result = anvil.server.call('get_file_from_client', file)
    self.manifest_label.text = anvil.server.call('load_input_manifest_path')
    anvil.server.call('write_log', "Uploaded " + anvil.server.call('load_input_manifest_path') + " manifest file")

  def load_unload_button_click(self, **event_args):
    """This method is called when the button is clicked"""
    anvil.server.call('write_log',"Started load/unload process for " + anvil.server.call('load_input_manifest_path'))
    open_form('Unload_Page')

  def click_login(self, **event_args):
    """This method is called when the button is clicked"""
    open_form('Login')
  
  def click_download_manifest(self, **event_args):
    manifest_media = anvil.server.call('load_output_manifest_media')
    manifest_path = anvil.server.call('load_output_manifest_path')
    anvil.server.call('write_log',"Downloaded " + manifest_path + " manifest file")
    anvil.media.download(manifest_media)

  def click_download_log(self, **event_args):
    log = anvil.server.call('load_log_media')
    anvil.server.call('write_log', "Downloaded log file")
    anvil.media.download(log)












