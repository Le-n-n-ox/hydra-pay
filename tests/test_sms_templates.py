import sms


def test_payment_sms_is_clear_gsm_safe_and_one_segment():
    message = sms.payment_receipt("Jeridah Wanjiku", 50, "RFP00001", "TGH123ABCD")
    assert message == (
        "Hydra Pay: Payment received. Jeridah Wanjiku paid KSh 50. "
        "Ref RFP00001. M-Pesa TGH123ABCD. Thank you."
    )
    assert len(message) <= 160
    assert sms.plain("Hydra Pay: \U0001f4b3 R\u00e9sum\u00e9") == "Hydra Pay: Resume"


def test_customer_alert_templates_stay_within_one_sms():
    messages = [
        sms.topup_receipt("A customer with an exceptionally long registered name", 2500, 3650, "HP00001"),
        sms.payment_not_completed("A customer with an exceptionally long registered name", 2500),
        sms.low_balance("A customer with an exceptionally long registered name", 5, 50),
        sms.card_blocked("A customer with an exceptionally long registered name"),
    ]
    assert all(len(message) <= 160 for message in messages)
