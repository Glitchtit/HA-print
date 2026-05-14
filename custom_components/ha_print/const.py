"""Constants for the ha_print integration."""

DOMAIN = "ha_print"

# Config entry keys
CONF_ADDON_URL = "addon_url"
CONF_STORAGE_URL = "storage_url"
CONF_RECIPES_URL = "recipes_url"

# Supervisor add-on slugs (used for hostname auto-discovery)
ADDON_SLUG_PRINT = "ha_print"
ADDON_SLUG_STORAGE_PATTERN = "ha.storage"
ADDON_SLUG_RECIPES_PATTERN = "recipes"

# Sensible defaults — Supervisor exposes add-ons by slug-as-hostname
DEFAULT_ADDON_URL = "http://core-ha-print:8099"

SERVICE_SHOPPING_LIST = "shopping_list"
SERVICE_RECIPE = "recipe"
