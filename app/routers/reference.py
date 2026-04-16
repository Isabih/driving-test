from fastapi import APIRouter, Depends
from app.core.deps import get_current_user
from app.models.models import User
from app.services.constants import STAGES

router = APIRouter(prefix="/reference", tags=["reference"])


@router.get("/stages")
def stages(_: User = Depends(get_current_user)):
    return [{"key": key, "name": name, "order": order} for key, name, order in STAGES]


@router.get("/event-types")
def event_types(_: User = Depends(get_current_user)):
    return ["line_touch", "wrong_direction", "foot_down_over_1s", "left_indicator_missing", "indicator_not_cancelled_4s", "narrow_under_7s", "started_above_25", "braked_early", "speed_below_25", "did_not_stop", "engine_stall", "skipped_exam", "accident"]


@router.get("/severity-levels")
def severity_levels(_: User = Depends(get_current_user)):
    return ["minor", "major", "critical"]


@router.get("/payment-methods")
def payment_methods(_: User = Depends(get_current_user)):
    return ["cash", "momo", "airtel_money", "visa", "mastercard"]
