"""
Minimal FastAPI service exposing the maintenance-intake pipeline.

Run: uvicorn src.api:app --reload
Then: POST a tenant message to /maintenance/intake
"""
from fastapi import FastAPI
from pydantic import BaseModel

from .orchestrator import handle_tenant_message

app = FastAPI(title="Property Maintenance Agent")


class TenantMessage(BaseModel):
    case_id: str
    tenant_name: str
    property_id: str
    unit_id: str
    message: str


@app.post("/maintenance/intake")
def intake(payload: TenantMessage):
    case = handle_tenant_message(
        case_id=payload.case_id,
        tenant_name=payload.tenant_name,
        property_id=payload.property_id,
        unit_id=payload.unit_id,
        message=payload.message,
    )
    return case.to_dict()


@app.get("/maintenance/case/{case_id}")
def get_case(case_id: str):
    from . import state_store
    case = state_store.get_case(case_id)
    if case is None:
        return {"error": "case not found"}
    return case.to_dict()


@app.get("/health")
def health():
    return {"status": "ok"}
