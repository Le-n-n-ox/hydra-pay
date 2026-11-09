import announcer


def test_counter_voice_formats_a_payment_without_starting_audio(monkeypatch):
    queued = []
    monkeypatch.setattr(announcer, "_enabled", lambda: True)
    monkeypatch.setattr(announcer, "_started", True)
    monkeypatch.setattr(announcer._messages, "put", queued.append)
    announcer.speak_payment_received("  Jeridah   Wanjiku ", 50)
    assert queued == ["Payment received from Jeridah Wanjiku. 50 shillings."]
