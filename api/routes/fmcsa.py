import httpx
from fastapi import APIRouter, Depends

from api.auth import verify_api_key
from api.config import settings
from api.schemas import FMCSAResult

router = APIRouter(prefix="/api/fmcsa", tags=["FMCSA"])

FMCSA_BASE_URL = "https://mobile.fmcsa.dot.gov/qc/services/carriers"


@router.get("/verify/{mc_number}", response_model=FMCSAResult)
async def verify_carrier(
    mc_number: str,
    _: str = Depends(verify_api_key),
) -> FMCSAResult:
    """Verify a carrier's MC number against the FMCSA database."""
    clean_mc = mc_number.replace("MC-", "").replace("MC", "").strip()

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{FMCSA_BASE_URL}/docket-number/{clean_mc}",
                params={"webKey": settings.fmcsa_api_key},
                headers={"Accept": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()

        content = data.get("content", [])
        if not content:
            return FMCSAResult(
                mc_number=mc_number,
                is_authorized=False,
                reason="No carrier found with this MC number.",
            )

        carrier = content[0].get("carrier", {})
        legal_name = carrier.get("legalName", "")
        dot_number = str(carrier.get("dotNumber", ""))
        allowed_to_operate = carrier.get("allowedToOperate", "N")
        operating_status = carrier.get("operatingStatus", "")
        out_of_service = carrier.get("outOfServiceFlag", "N") == "Y"

        is_authorized = allowed_to_operate == "Y" and not out_of_service

        reason = None
        if not is_authorized:
            if out_of_service:
                reason = "Carrier is currently out of service."
            elif allowed_to_operate != "Y":
                reason = f"Carrier is not authorized to operate. Status: {operating_status}"

        return FMCSAResult(
            mc_number=mc_number,
            legal_name=legal_name,
            dot_number=dot_number,
            is_authorized=is_authorized,
            operating_status=operating_status,
            out_of_service=out_of_service,
            reason=reason,
        )

    except httpx.HTTPStatusError as e:
        return FMCSAResult(
            mc_number=mc_number,
            is_authorized=False,
            reason=f"FMCSA API error: {e.response.status_code}",
        )
    except httpx.RequestError as e:
        return FMCSAResult(
            mc_number=mc_number,
            is_authorized=False,
            reason=f"Could not reach FMCSA API: {str(e)}",
        )
