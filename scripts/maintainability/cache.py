"""Module with a class utility for cache in JSON."""

import json

class Cache():
    """Cache in json."""
    def __init__(self, storage_path):
        self.storage_path = storage_path
        self._data = None

    @property
    def data(self):
        """Return dict with all cached data."""
        if self._data is None:
            try:
                with open(self.storage_path, 'r') as cache_file:
                    self._data = json.load(cache_file)
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
        with open(self.storage_path, 'w') as cache_file:
            json.dump(self.data, cache_file)

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
