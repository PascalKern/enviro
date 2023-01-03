from enviro import logging, exception
from enviro.constants import UPLOAD_SUCCESS, UPLOAD_FAILED
from enviro.mqttsimple import MQTTClient
import ujson
import config


_mqtt_client: MQTTClient = None


def log_destination():
  logging.info(f"> uploading cached readings to MQTT broker: {config.mqtt_broker_address}")

def upload_reading(reading):
  server = config.mqtt_broker_address
  username = config.mqtt_broker_username
  password = config.mqtt_broker_password
  nickname = reading["nickname"]
  
  # check if ca file paramter is set, if not set it to not use SSL by setting to None
  if not hasattr(config, 'mqtt_broker_ca_file'):
    config.mqtt_broker_ca_file = None

  mqtt_client = _get_client(f'{nickname}_{reading["uid"]}', server, username, password, config.mqtt_broker_ca_file)

  try:
    logging.debug(f'MQTT connected with status: \'{res}\'')
    mqtt_client.publish(f"enviro/{nickname}", ujson.dumps(reading), retain=True)
    return UPLOAD_SUCCESS

  # Try disconneting to see if it prevents hangs on this typew of errors recevied so far
  except (OSError, IndexError) as exc:
    try:
      exception(exc)
      import sys, io
      buf = io.StringIO()
      sys.print_exception(exc, buf)
      logging.debug(f"  - an exception occurred when uploading.", buf.getvalue())
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


def _get_client(client_id: str, server: str, username: str, password: str, ssl_ca_file: str = None, keepalive: int = 60):
  global _mqtt_client
  logging.debug(f'MQTT client field is: {_mqtt_client}')
  if _mqtt_client is None:
    logging.debug('Init and connect MQTT client')
    con_res = _init_client(client_id, server, username, password, keepalive, ssl_ca_file)
    logging.debug(f'MQTT connection state is: {con_res}')
  return _mqtt_client


def _init_client(client_id, server, username, password, keepalive, ssl_ca_file):
  global _mqtt_client
  try:
    if ssl_ca_file:
      logging.debug(f'Use SSL for MQTT client with cert: {ssl_ca_file}')
      # Using SSL
      f = open(ssl_ca_file)
      ssl_data = f.read()
      f.close()
      _mqtt_client = MQTTClient(client_id, server, user=username, password=password, keepalive=keepalive,
                                ssl=True, ssl_params={'cert': ssl_data})
    else:
      # Not using SSL
      _mqtt_client = MQTTClient(client_id, server, user=username, password=password, keepalive=keepalive)
  except Exception as ex:
    logging.error(f'Failed to create MQTT client!', ex)
    raise ex

  try:
    # Now continue with connection and upload
    return _mqtt_client.connect(clean_session=True)
  except Exception as ex:
    logging.error(f'Failed to connect a clean session for MQTT client!', ex)
    raise ex


def disconnect():
  global _mqtt_client
  if _mqtt_client:
    try:
      _mqtt_client.disconnect()
      logging.debug(f'Disconnected mqtt client instance.')
    except (OSError, Exception) as osex:
      logging.debug(f'Failed to disconnect the mqtt client instance!', osex)
    finally:
      _mqtt_client = None
