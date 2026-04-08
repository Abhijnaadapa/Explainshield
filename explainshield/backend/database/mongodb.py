import logging
from motor.motor_asyncio import AsyncIOMotorClient
import hashlib
from config import settings

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    db_name: str = settings.DATABASE_NAME

    @staticmethod
    def get_kms_providers():
        # Derive a 96-byte key from the 32-byte ENCRYPTION_KEY for local KMS
        # In production, this would use AWS KMS, Azure Key Vault, or GCP KMS
        key_bytes = settings.ENCRYPTION_KEY.encode("utf-8")
        # Ensure it's exactly 96 bytes for local provider
        stretched_key = hashlib.sha3_512(key_bytes).digest() + hashlib.sha256(key_bytes).digest()
        # total 64 + 32 = 96 bytes
        return {"local": {"key": stretched_key[:96]}}

    @classmethod
    async def connect_db(cls):
        if cls.client is not None:
            return

        print(f"--- Attempting to connect to MongoDB: {settings.MONGODB_URL.split('@')[-1]} ---")
        
        # Skip CSFLE for Atlas cloud - use direct connection
        try:
            cls.client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=10000,
                uuidRepresentation="standard"
            )
            
            await cls.client.admin.command('ping')
            print("SUCCESS: Connected to MongoDB Atlas.")
            logger.info("Connected to MongoDB Atlas.")
        except Exception as e:
            print(f"WARNING: Failed to connect to MongoDB: {e}")
            print("WARNING: Running in offline/degraded mode. Database features will be unavailable.")
            logger.error(f"Failed to connect to MongoDB: {e}")
            cls.client = None 

    @classmethod
    async def close_db(cls):
        if cls.client is not None:
            cls.client.close()
            cls.client = None
            print("--- MongoDB connection closed. ---")
            logger.info("MongoDB connection closed.")

    @classmethod
    def get_database(cls):
        if cls.client is None:
            raise Exception("Database client not initialized. Call connect_db first.")
        return cls.client[cls.db_name]

    @classmethod
    def get_company_collection(cls, company_id: str, collection_name: str):
        """
        Implements company isolation by prefixing the collection name.
        All data for a specific company is stored in collections named: company_{cid}_{cname}
        """
        db = cls.get_database()
        prefixed_name = f"company_{company_id}_{collection_name}"
        return db[prefixed_name]

# Helper functions for FastAPI startup/shutdown
async def connect_to_mongo():
    await Database.connect_db()

async def close_mongo_connection():
    await Database.close_db()

def get_database():
    return Database.get_database()
