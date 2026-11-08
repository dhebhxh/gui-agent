from fastapi import FastAPI, HTTPException
from dispatcher import ActionDispatcher
import base64
from pydantic import BaseModel
from typing import Dict, Any

app = FastAPI()
dispatcher = ActionDispatcher()

class ActionRequest(BaseModel):
    action: Dict[str, Any]

@app.get("/screenshot")
def get_screenshot():
    try:
        result = dispatcher.dispatch({"type": "screenshot"})
        if result.get("type") == "image":
            img_base64 = base64.b64encode(result["data"]).decode("utf-8")
            return {"status": "success", "image_base64": img_base64}
        else:
            raise ValueError("Unexpected return type from dispatcher")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/execute")
def execute_action(req: ActionRequest):
    try:
        result = dispatcher.dispatch(req.action)
        return {"status": "success", "result": result}
    except TypeError as e:
        raise HTTPException(status_code=400, detail=f"invalid type: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"invalid value: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"execution error: {str(e)}")