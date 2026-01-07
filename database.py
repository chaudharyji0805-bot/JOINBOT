from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI

mongo = None
db = None

users = None
group_settings = None
stats = None
group_stats = None

import json
import os

class MockDBInstance:
    def __init__(self, filename="mock_db.json"):
        self.filename = filename
        self.data = self._load()
    
    def _load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save(self):
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"Error saving DB: {e}")

    def get_collection(self, name):
        if name not in self.data:
            self.data[name] = []
        return self.data[name]

_MOCK_INSTANCE = MockDBInstance()

class MockCollection:
    def __init__(self, name):
        self.name = name

    @property
    def data(self):
        return _MOCK_INSTANCE.get_collection(self.name)

    async def find_one(self, query):
        for doc in self.data:
            if all(doc.get(k) == v for k, v in query.items()):
                return doc
        return None

    async def update_one(self, query, update, upsert=False):
        # Find existing
        found_idx = -1
        for i, doc in enumerate(self.data):
             if all(doc.get(k) == v for k, v in query.items()):
                 found_idx = i
                 break
        
        if found_idx != -1:
            doc = self.data[found_idx]
            if "$set" in update:
                doc.update(update["$set"])
            if "$inc" in update:
                for k, v in update["$inc"].items():
                    doc[k] = doc.get(k, 0) + v
            if "$addToSet" in update:
                for k, v in update["$addToSet"].items():
                    if k not in doc: doc[k] = []
                    if isinstance(doc[k], list) and v not in doc[k]:
                        doc[k].append(v)
            if "$pull" in update:
                for k, v in update["$pull"].items():
                     if k in doc and isinstance(doc[k], list) and v in doc[k]:
                         doc[k].remove(v)
            _MOCK_INSTANCE._save()
        elif upsert:
            new_doc = query.copy()
            if "$set" in update:
                new_doc.update(update["$set"])
            if "$inc" in update:
                for k, v in update["$inc"].items():
                    new_doc[k] = v
            if "$addToSet" in update:
                for k, v in update["$addToSet"].items():
                    new_doc[k] = [v]
            self.data.append(new_doc)
            _MOCK_INSTANCE._save()

    async def count_documents(self, query):
        if not query:
            return len(self.data)
        count = 0
        for doc in self.data:
            if all(doc.get(k) == v for k, v in query.items()):
                count += 1
        return count

    async def find(self, query):
        for doc in self.data:
            if not query or all(doc.get(k) == v for k, v in query.items()):
                yield doc

def get_database():
    if MONGO_URI:
        try:
            # Synchronous check first to ensure we can actually connect
            # This prevents Motor from being created but failing later at runtime
            from pymongo import MongoClient, errors
            print("⏳ Checking MongoDB connection...")
            sync_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
            sync_client.server_info() # This blocks until connected or timeout
            
            client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=2000)
            print("✅ Connected to MongoDB")
            return client.forcejoinbot
        except Exception as e:
            print(f"⚠️ Mongo Connection Failed: {e}")
            print("⚠️ Falling back to Local File Mode.")
    
    print("✅ Running in Local File Mode (Database: mock_db.json)")
    class MockDB:
        def __init__(self):
            self.users = MockCollection("users")
            self.group_settings = MockCollection("group_settings")
            self.stats = MockCollection("stats")
            self.group_stats = MockCollection("group_stats")
            self.premium = MockCollection("premium")
            self.channels = MockCollection("channels")
            self.aauth_users = MockCollection("aauth_users")

    return MockDB()

# Initialize
_db = get_database()

class DynamicMockDB:
    def __init__(self):
         self._collections = {}
    
    def __getattr__(self, name):
         if name not in self._collections:
             self._collections[name] = MockCollection(name)
         return self._collections[name]

if not MONGO_URI:
     print("ℹ️ MongoDB not configured. Using Local File Mode.")
     # Ensure we use the same structure
     if not isinstance(_db, AsyncIOMotorClient):
         # It's already the MockDB class from get_database, which has attributes
         pass
     else:
         # Fallback if somehow execution path fails
         _db = DynamicMockDB()
else:
    # ... existing else block ...
    pass

# Map collections
if isinstance(_db, AsyncIOMotorClient):
    users = _db.users
    group_settings = _db.group_settings
    stats = _db.stats
    group_stats = _db.group_stats
    channels = _db.channels
    premium = _db.premium
    aauth_users = _db.aauth_users
else:
    # MockDB has attributes
    users = _db.users
    group_settings = _db.group_settings
    stats = _db.stats
    group_stats = _db.group_stats
    channels = _db.channels
    premium = _db.premium
    aauth_users = _db.aauth_users
