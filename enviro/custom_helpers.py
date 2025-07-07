import custom_config


def is_custom_config_active(key: str) -> bool:
  return hasattr(custom_config, key) and getattr(custom_config, key, False)

