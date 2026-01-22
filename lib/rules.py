from datetime import date, datetime

def parse_date_yyyy_mm_dd(s: str):
    s = (s or "").strip()
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None

def expiry_status(expiry_date_str: str, warn_days: int = 60):
    """
    유효기간 기준 상태:
    - 🔴 만료
    - 🟡 만료 임박 (warn_days 이내)
    - 🟢 유효
    """
    d = parse_date_yyyy_mm_dd(expiry_date_str)
    if d is None:
        return ("⚪", "유효기간 없음")

    today = date.today()
    diff = (d - today).days
    if diff < 0:
        return ("🔴", f"만료 ({abs(diff)}일 지남)")
    if diff <= warn_days:
        return ("🟡", f"만료 임박 ({diff}일 남음)")
    return ("🟢", f"유효 ({diff}일 남음)")

def normalize_fiber_key(selected_fibers: list[str], fiber_order_map: dict[str, int]):
    """
    조성섬유 선택값을 정렬해 fiber_key를 표준화.
    예: ["폴리에스터","면"] -> "면|폴리에스터"
    """
    fibers = [f.strip() for f in selected_fibers if (f or "").strip()]
    fibers = list(dict.fromkeys(fibers))  # 중복 제거

    def sort_key(x):
        if x in fiber_order_map:
            return (0, fiber_order_map[x])
        return (1, x)

    fibers_sorted = sorted(fibers, key=sort_key)
    return "|".join(fibers_sorted)

