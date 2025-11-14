from django.db import models
from django.utils.translation import gettext_lazy as _


class ConfigurationMixin(models.Model):
    """
    Mixin that adds a JSON configuration field with utility methods
    to any Django model. Provides a flexible way to store custom
    settings and preferences.
    """

    configuration = models.JSONField(
        default=dict, blank=True, help_text=_("Custom configuration settings in JSON format")
    )

    class Meta:
        abstract = True

    def get_config(self, key, default=None):
        """
        Get a specific configuration value

        Args:
            key (str): Configuration key
            default: Default value if key doesn't exist

        Returns:
            Configuration value or default
        """
        return self.configuration.get(key, default)

    def set_config(self, key, value):
        """
        Set a configuration value

        Args:
            key (str): Configuration key
            value: Value to set
        """
        if self.configuration is None:
            self.configuration = {}
        self.configuration[key] = value

    def update_config(self, config_dict):
        """
        Update multiple configuration values at once

        Args:
            config_dict (dict): Dictionary with configuration updates
        """
        if self.configuration is None:
            self.configuration = {}
        self.configuration.update(config_dict)

    def remove_config(self, key):
        """
        Remove a configuration key

        Args:
            key (str): Configuration key to remove

        Returns:
            bool: True if key was removed, False if it didn't exist
        """
        if self.configuration and key in self.configuration:
            del self.configuration[key]
            return True
        return False

    def has_config(self, key):
        """
        Check if a configuration key exists

        Args:
            key (str): Configuration key to check

        Returns:
            bool: True if key exists, False otherwise
        """
        return bool(self.configuration and key in self.configuration)

    def clear_config(self):
        """
        Clear all configuration values
        """
        self.configuration = {}

    def get_config_keys(self):
        """
        Get all configuration keys
         Returns:
            list: List of configuration keys
        """

        return list(self.configuration.keys()) if self.configuration else []
