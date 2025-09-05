#core/plugins/cloud_integration.py
import os
import logging
from abc import ABC, abstractmethod

from core.utils import get_desktop_path


class CloudPlugin(ABC):
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    def sync_folder(self, folder_path):
        pass


class OneDrivePlugin(CloudPlugin):
    def sync_folder(self, folder_path):
        # Реализация синхронизации с OneDrive
        self.logger.info(f"Синхронизация {folder_path} с OneDrive (не реализовано).")
        pass


class GoogleDrivePlugin(CloudPlugin):
    def sync_folder(self, folder_path):
        # Реализация синхронизации с Google Drive
        self.logger.info(f"Синхронизация {folder_path} с Google Drive (не реализовано).")
        pass


class CloudManager:
    def __init__(self):
        self.plugins = {
            "onedrive": OneDrivePlugin(),
            "googledrive": GoogleDrivePlugin()
        }

    def sync_category(self, category_name, cloud_service):
        if cloud_service in self.plugins:
            folder_path = os.path.join(get_desktop_path(), category_name)
            self.plugins[cloud_service].sync_folder(folder_path)