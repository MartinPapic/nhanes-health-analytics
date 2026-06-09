"""Project settings. There is no need to edit this file unless you want to change values
from the Kedro defaults. For further information, including these default values, see
https://kedro.readthedocs.io/en/stable/kedro_project_setup/settings.html."""

# Instantiated project hooks.
# from nhanes_pipeline.hooks import ProjectHooks
# HOOKS = (ProjectHooks(),)

# Installed plugins for which to disable hook auto-registration.
# DISABLE_HOOKS_FOR_PLUGINS = ("kedro-viz",)

# Class that manages how configuration is loaded.
from kedro.config import OmegaConfigLoader  # noqa: import-outside-toplevel

CONFIG_LOADER_CLASS = OmegaConfigLoader
# Keyword arguments to pass to the `CONFIG_LOADER_CLASS` constructor.
# CONFIG_LOADER_ARGS = {
#       "base_env": "base",
#       "default_run_env": "local",
#       "config_patterns": {
#           "spark" : ["spark*/"],
#           "parameters": ["parameters*", "parameters*/**", "**/parameters*"],
#       }
# }

# Class that manages the Data Catalog.
# from kedro.io import DataCatalog
# DATA_CATALOG_CLASS = DataCatalog
