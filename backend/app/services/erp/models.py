"""Enterprise ERP Integration Models for SAP S/4HANA (OData) and IBM Maximo (OSLC REST).

Standards-compliant schemas representing industrial maintenance work orders,
procurement clearing entries, and evidence-gated settlement tracking.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def utcnow_str() -> str:
    return datetime.now(timezone.utc).isoformat()


class ERPConnectorMode(str, Enum):
    LIVE_REST = "LIVE_REST"
    ENTERPRISE_SANDBOX = "ENTERPRISE_SANDBOX"
    LOCAL_MOCK = "LOCAL_MOCK"


class SAPOrderType(str, Enum):
    PM01 = "PM01"  # Corrective Plant Maintenance
    PM02 = "PM02"  # Preventive Maintenance
    PM03 = "PM03"  # Emergency Breakdown


class MaximoWorkType(str, Enum):
    CM = "CM"  # Corrective Maintenance
    EM = "EM"  # Emergency Maintenance
    PM = "PM"  # Preventive Maintenance


# ---------------------------------------------------------------------------
# SAP S/4HANA OData v2 / v4 Models (API_MAINTENANCEORDER)
# ---------------------------------------------------------------------------

class SAPMaintenanceOrderRequest(BaseModel):
    equipment_id: str = Field(..., description="SAP Equipment Master Tag (e.g. P-101A)")
    order_type: SAPOrderType = Field(default=SAPOrderType.PM01, description="SAP PM Order Type")
    short_text: str = Field(..., description="Work order description")
    plant: str = Field(default="1000", description="SAP Maintenance Plant Code")
    work_center: str = Field(default="MECH-01", description="Main Work Center")
    cost_center: str = Field(default="CC-MUMBAI-01", description="Controlling Cost Center")
    gl_clearing_account: str = Field(default="2100-PAYPAL-CLEARING", description="Clearing liability GL account")
    vendor_id: str = Field(..., description="SAP Business Partner / Vendor ID")
    vendor_name: str = Field(..., description="Vendor legal entity name")
    estimated_amount: str = Field(..., description="Estimated cost amount in USD")
    currency: str = Field(default="USD", description="Currency code")
    paypal_order_id: Optional[str] = Field(default=None, description="PayPal Orders v2 ID")
    paypal_auth_id: Optional[str] = Field(default=None, description="PayPal Authorization ID (holds committed funds)")
    paypal_capture_id: Optional[str] = Field(default=None, description="PayPal Capture ID (upon evidence verification)")
    evidence_hash: Optional[str] = Field(default=None, description="SHA-256 evidence package hash gating settlement")


class SAPDoubleEntryPosting(BaseModel):
    posting_date: str
    document_type: str = "SA"  # G/L Account Document
    company_code: str = "1000"
    currency: str = "USD"
    debit_account: str = "6100-MAINT-EXPENSE"
    credit_account: str = "2100-PAYPAL-CLEARING"
    amount: str
    reference_key: str
    cleared: bool = False
    clearing_document: Optional[str] = None


class SAPMaintenanceOrderResponse(BaseModel):
    success: bool
    sap_order_id: str = Field(..., description="SAP Maintenance Order Number (e.g. 4001928)")
    sap_notification_id: str = Field(..., description="SAP Maintenance Notification Number (e.g. 1002341)")
    odata_url: str = Field(..., description="OData entity URI")
    status: str = Field(..., description="SAP status: CRTD, REL, TECO, or CLSD")
    equipment_id: str
    vendor_id: str
    gl_clearing_account: str
    accounting_posting: SAPDoubleEntryPosting
    connector_mode: ERPConnectorMode
    sync_timestamp: str = Field(default_factory=utcnow_str)
    odata_payload_preview: Dict[str, Any]


# ---------------------------------------------------------------------------
# IBM Maximo OSLC REST Models (/maximo/oslc/os/mxwo)
# ---------------------------------------------------------------------------

class IBMMaximoWorkOrderRequest(BaseModel):
    wonum: Optional[str] = Field(default=None, description="Maximo Work Order Number")
    site_id: str = Field(default="BEDFORD", description="Maximo Site ID")
    asset_num: str = Field(..., description="Maximo Asset Identifier (e.g. P-101A)")
    work_type: MaximoWorkType = Field(default=MaximoWorkType.CM, description="Maximo Work Type")
    description: str = Field(..., description="Work Order Title / Description")
    vendor_id: str = Field(..., description="Maximo Company / Vendor ID")
    estimated_cost: str = Field(..., description="Estimated cost amount in USD")
    gl_credit_account: str = Field(default="2100-PAYPAL-CLEARING", description="Financial GL credit clearing account")
    paypal_order_id: Optional[str] = Field(default=None)
    paypal_auth_id: Optional[str] = Field(default=None)
    paypal_capture_id: Optional[str] = Field(default=None)
    evidence_hash: Optional[str] = Field(default=None)


class IBMMaximoWorkOrderResponse(BaseModel):
    success: bool
    wonum: str = Field(..., description="Maximo Work Order Number")
    status: str = Field(..., description="Maximo Status: WAPPR, APPR, INPRG, COMP, or CLOSE")
    oslc_uri: str = Field(..., description="Maximo OSLC resource URI")
    asset_num: str
    site_id: str
    paypal_auth_ref: Optional[str] = None
    paypal_capture_ref: Optional[str] = None
    evidence_validated: bool
    connector_mode: ERPConnectorMode
    sync_timestamp: str = Field(default_factory=utcnow_str)
    oslc_payload_preview: Dict[str, Any]


# ---------------------------------------------------------------------------
# Aggregated ERP Status
# ---------------------------------------------------------------------------

class ERPStatusResponse(BaseModel):
    sap_s4hana: Dict[str, Any]
    ibm_maximo: Dict[str, Any]
    gl_clearing_account: Dict[str, Any]
    timestamp: str = Field(default_factory=utcnow_str)
