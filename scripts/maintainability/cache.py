"""Module with a class utility for cache in JSON."""

from os.path import splitext
import json
from pathlib import Path
from zipfile import ZipFile

import bson

class JsonLib:
    def load(self, file_path):
        with open(file_path, 'r') as cache_file:
            return json.load(cache_file)

    def dump(self, data, file_path):
        with open(file_path, 'w') as cache_file:
            json.dump(data, cache_file)

class BsonLib:
    def load(self, file_path):
        with open(file_path, 'r') as cache_file:
            return bson.loads(cache_file)

    def dump(self, data, file_path):
        with open(file_path, 'w') as cache_file:
            cache_file.write(bson.dumps(data))

def change_extension(file_path, extension):
    return Path(file_path).stem + extension

class ZipLib:
    def load(self, file_path):
        json_filename = change_extension(file_path, '.json')
        with ZipFile(file_path, 'r') as myzip:
            with myzip.open(json_filename, 'r') as cache_file:
                return json.load(cache_file)

    def dump(self, data, file_path):
        json_filename = change_extension(file_path, '.json')
        with ZipFile(file_path, 'w') as myzip:
            with myzip.open(json_filename, 'w') as cache_file:
                json.dump(data, cache_file)

class Cache():
    """Cache in json."""
    def __init__(self, storage_path):
        self.storage_path = storage_path
        _, extension = splitext(storage_path)
        if extension == '.zip':
            self._json_lib = ZipLib()
        elif extension == '.bson':
            self._json_lib = BsonLib()
        else:
            self._json_lib = JsonLib()
        self._data = None

    @property
    def data(self):
        """Return dict with all cached data."""
        if self._data is None:
            try:
                self._data = self._json_lib.load(self.storage_path)
            except FileNotFoundError:
                self._data = {}
        return self._data

    def get_value(self, key):
        """Return value for given key."""
        return self.data.get(key)

    def set_value(self, key, value):
        """Set value for given key."""
        self.data[key] = value
        self.save_data()

    def remove_key(self, key):
        """Remove a key from cache."""
        del self.data[key]
        self.save_data()

    def save_data(self):
        """Store data in designated json file."""
        self._json_lib.dump(self.data, self.storage_path)

class BCHCache(Cache):
    """Cache for Better Code Hub results"""
    def get_stored_commit_analysis(self, user, project, commit_sha):
        """Get analysis results of commit that were previously processed."""
        key = BCHCache._get_commit_analysis_storage_key(user, project, commit_sha)
        return self.get_value(key)

    def store_commit_analysis(self, user, project, commit_sha, report):
        """Store better code hub result."""
        key = BCHCache._get_commit_analysis_storage_key(user, project, commit_sha)
        self.set_value(key, report)

    @staticmethod
    def _get_commit_analysis_storage_key(user, project, commit_sha):
        return '/'.join([user, project, commit_sha])
