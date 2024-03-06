# cache_manager.py
import json
import os
from hashlib import sha256
from config import CACHE_FOLDER

class CacheManager:
    def __init__(self):
        if not os.path.exists(CACHE_FOLDER):
            os.makedirs(CACHE_FOLDER)

    def get_hash(self, messages):
        hash_object = sha256(json.dumps(messages).encode('utf-8')).hexdigest()
        return hash_object

    def get_cached_response(self, messages):
        hash_ = self.get_hash(messages)
        cache_filename = f'{CACHE_FOLDER}/{hash_}.json'
        if os.path.exists(cache_filename):
            with open(cache_filename, 'r') as file:
                return json.load(file)
        return None

    def cache_response(self, messages, response):
        hash_ = self.get_hash(messages)
        cache_filename = f'{CACHE_FOLDER}/{hash_}.json'
        with open(cache_filename, 'w') as file:
            json.dump(response, file, indent=4)
