from enviro import logging
from enviro.constants import UPLOAD_SUCCESS, UPLOAD_FAILED
from enviro.mqttsimple import MQTTClient
import ujson
import config


class UploadDestinationException(BaseException):
  pass


class BaseUploadDestination:  # (ABC):
  # @abstractmethod
  def log_destination(self):
    pass

  # @abstractmethod
  def upload_reading(self, reading):
    pass


class MQTTUploadDestination(BaseUploadDestination):
  _instance = None
  _client_instance: MQTTClient = None
  _is_open = False

  def __new__(cls, *args, **kwargs):
    """ creates a singleton object, if it is not created,
            or else returns the previous singleton object"""
    if not hasattr(cls, 'instance') or cls._instance is None:
      cls._instance = super(BaseUploadDestination, cls).__new__(cls)
    return cls._instance

  def __init__(self, client_id: str = f"{UNIT_ID}_{get_uid()}", server: str = IP_MQTT_BROKER, username: str = USER_MQTT,
               password: str = PW_MQTT, keepalive: int = 60, ca_file: str = None):
    self.client_id = client_id
    self.server = server
    self.username = username
    self.password = password
    self.keepalive = keepalive
    self.ca_file = ca_file

  def log_destination(self):
    logging.info(f"> uploading cached readings to MQTT broker: {self.server}")

  def upload_reading(self, reading: dict, topic: str = None, idx: int = None) -> int:
    if not self._is_open:
      raise ConnectionError('This client is not yet connected ie. opened to communicate with the MQTT broker!')
    pub_msg = ujson.dumps(reading)
    logging.debug(f'Publishing as client: {self.client_id}, topic: {topic} with value: {reading} as: {pub_msg}')
    # if WATCH_DOG_ENABLE:
    #   wd_feed()
    try:
      if idx is None:
        self._client_instance.publish(UNIT_ID + "/" + topic, pub_msg)
      else:
        self._client_instance.publish(UNIT_ID + "/" + topic + "_" + str(idx), pub_msg)
      return UPLOAD_SUCCESS
    except Exception as ex:
      logging.error(f'Failed to upload reading! Reading: {reading} as: {pub_msg} on topic: {topic}', ex)
      return UPLOAD_FAILED

  # Added just so that an instance of this class without a 'with' statement can be used too!
  def open(self):
    return self.__enter__()

  # Added so that if needed somehow one can use an instance of this class like:
  # with contextlib.closing(instance_of_mqttuploaddestination) as it:
  #  ...
  #  ...
  def close(self) -> bool:
    return self.__exit__(None, None, None)

  def _init_client(self):
    if self._client_instance is None:
      try:
        if self.ca_file:
          logging.debug(f'Use SSL for MQTT client with cert: {self.ca_file}')
          # Using SSL
          with open(self.ca_file) as f:
            ssl_data = f.read()
          self._client_instance = MQTTClient(self.client_id, self.server, user=self.username, password=self.password,
                                             keepalive=self.keepalive, ssl=True, ssl_params={'cert': ssl_data})
        else:
          logging.debug(
            f'Create client instance with args: {(self.client_id, self.server, self.username, self.password, self.keepalive)}')
          # Not using SSL
          self._client_instance = MQTTClient(self.client_id, self.server, user=self.username, password=self.password,
                                             keepalive=self.keepalive)
      except Exception as ex:
        logging.error(f'Failed to create MQTT client!', ex)
        raise ex
    else:
      logging.debug(f'A client was already instantiated! {self._client_instance}')

  def __enter__(self):
    logging.debug(f"Enter {self.__class__}")
    if not self._is_open:
      try:
        self._init_client()
        # Now continue with connection and upload
        self._client_instance.connect(clean_session=True)
        self._is_open = True
        return self
      except Exception as ex:
        logging.error(f'Failed to connect a clean session for MQTT client!', ex)
        raise ex
    else:
      logging.debug(f'The client instance ({self._client_instance}) was already connected / open.')

  def __exit__(self, *args) -> bool:
    logging.debug(f"Exit {self.__class__} with arguments: {args}")
    if self._client_instance and self._is_open:
      try:
        self._client_instance.disconnect()
        logging.debug(f'Disconnected mqtt client instance.')
        return True
      except (OSError, Exception) as osex:
        logging.debug(f'Failed to disconnect the mqtt client instance!', osex)
        raise osex
      finally:
        self._client_instance = None
        self._is_open = False
        return False


def log_destination():
  logging.info(f"> uploading cached readings to MQTT broker: {config.mqtt_broker_address}")

def upload_reading(reading):
  server = config.mqtt_broker_address
  username = config.mqtt_broker_username
  password = config.mqtt_broker_password
  nickname = reading["nickname"]
  
  # check if ca file paramter is set, if not set it to not use SSL by setting to None
  try:
    config.mqtt_broker_ca_file
  except AttributeError: 
    config.mqtt_broker_ca_file = None
  
  try:
    if config.mqtt_broker_ca_file:
    # Using SSL
      f = open("ca.crt")
      ssl_data = f.read()
      f.close()
      mqtt_client = MQTTClient(reading["uid"], server, user=username, password=password, keepalive=60,
                               ssl=True, ssl_params={'cert': ssl_data})
    else:
    # Not using SSL
      mqtt_client = MQTTClient(reading["uid"], server, user=username, password=password, keepalive=60)
    # Now continue with connection and upload
    mqtt_client.connect()
    mqtt_client.publish(f"enviro/{nickname}", ujson.dumps(reading), retain=True)
    mqtt_client.disconnect()
    return UPLOAD_SUCCESS

  # Try disconneting to see if it prevents hangs on this typew of errors recevied so far
  except (OSError, IndexError) as exc:
    try:
      import sys, io
      buf = io.StringIO()
      sys.print_exception(exc, buf)
      logging.debug(f"  - an exception occurred when uploading.", buf.getvalue())
      mqtt_client.disconnect()
    except Exception as exc:
      import sys, io
      buf = io.StringIO()
      sys.print_exception(exc, buf)
      logging.debug(f"  - an exception occurred when disconnecting mqtt client.", buf.getvalue())

  except Exception as exc:
    import sys, io
    buf = io.StringIO()
    sys.print_exception(exc, buf)
    logging.debug(f"  - an exception occurred when uploading.", buf.getvalue())

  return UPLOAD_FAILED
