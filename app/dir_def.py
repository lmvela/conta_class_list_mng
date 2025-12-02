import os
import json

# Load MongoDB config from ./config/config.json
with open(os.path.join(os.path.dirname(__file__), '..', 'config', 'config.json')) as f:
    config = json.load(f)
mongodb_cfg = config.get('mongodb', {})

# Get DB URLand name from config
MONGO_URL = mongodb_cfg.get('url', 'mongodb://localhost:27017')
DB_NAME = mongodb_cfg.get('db', 'conta_db')