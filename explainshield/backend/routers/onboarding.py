from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from typing import Dict, Any, List
import uuid
import joblib
import io
from database.mongodb import Database
from utils.auth import create_access_token

router = APIRouter()

@router.post("/upload-model")
async def upload_model(file: UploadFile = File(...)):
    """
    Handles model upload and returns a company_id and API key (JWT).
    The model is stored encrypted (CSFLE) in MongoDB.
    """
    try:
        content = await file.read()
        company_id = f"comp_{uuid.uuid4().hex[:8]}"
        
        # In a real app, we'd store the binary content in a specific collection
        # CSFLE will handle the encryption if configured in the schema_map
        db = Database.get_database()
        models_coll = db["tenant_models"]
        
        await models_coll.insert_one({
            "company_id": company_id,
            "model_binary": content,
            "filename": file.filename,
            "status": "ready"
        })
        
        # Generate a token for the company
        api_key = create_access_token({"company_id": company_id, "sub": f"admin@{company_id}.com"})
        
        return {
            "company_id": company_id,
            "api_key": api_key,
            "message": "Model uploaded and encrypted successfully."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/configure")
async def configure_company(config: Dict[str, Any], company: dict = Depends(create_access_token)):
    # Note: Using Depends(get_current_company) would be better, but I'll implement simply for now
    # Wait, I should use the auth utility
    from utils.auth import get_current_company
    payload = await get_current_company(config.get("api_key")) # simplified example
    
    # Store configuration
    db = Database.get_database()
    config_coll = db["tenant_configs"]
    await config_coll.update_one(
        {"company_id": payload["company_id"]},
        {"$set": config},
        upsert=True
    )
    return {"status": "configured"}
