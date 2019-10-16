from pydantic import BaseModel


class Config(BaseModel):
    """user defined in ``$BGMI_PATH/bgmi.cfg``"""


class AdvancedConfig(BaseModel):
    """user defined in ``$BGMI_PATH/advanced_config.toml``"""
