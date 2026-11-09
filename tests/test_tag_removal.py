import store


def test_reader_removal_marks_an_in_card_out_without_charging(tmp_path):
    store.use_database(tmp_path / "removal.db")
    store.init()
    store.save_card("AA BB CC DD", "Jane", "0712345678", 10)
    store.add_money("AA BB CC DD", 20, "TOPUP_CASH")
    entered = store.tap("AA BB CC DD")
    assert entered["direction"] == "IN"

    removed = store.remove_card("AA BB CC DD")
    assert removed and removed["direction"] == "OUT"
    assert store.get_card("AA BB CC DD")["status"] == "OUT"
    assert store.recent_transactions(limit=1)[0]["amount"] == -10

    assert store.remove_card("AA BB CC DD") is None
