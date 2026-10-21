"""결제 흉내(시험용). 실제 결제 회사에 연결하지 않으며 돈이 오가지 않는다."""
from .engine import BookingError

TEST_CARD_OK = "4242424242424242"


def pay_test(db, booking_id, card_number):
    row = db.execute("SELECT status,paid FROM bookings WHERE id=?", (booking_id,)).fetchone()
    if not row: raise BookingError("예약을 찾을 수 없습니다")
    if row[0] != "confirmed": raise BookingError("취소된 예약입니다")
    if row[1]: raise BookingError("이미 결제된 예약입니다")
    if str(card_number).replace(" ", "") != TEST_CARD_OK:
        raise BookingError("시험 결제는 시험용 카드 번호만 받습니다 (실제 카드 번호를 넣지 마세요)")
    with db:
        db.execute("UPDATE bookings SET paid=1 WHERE id=?", (booking_id,))
    return {"mode": "TEST", "paid": True}
