import dashboard
import store
import wallet


def test_telco_callback_requires_token(monkeypatch, tmp_path):
    store.use_database(tmp_path / "routes.db")
    store.init()
    monkeypatch.setenv("USSD_PROVIDER", "africastalking")
    monkeypatch.setenv("TELCO_CALLBACK_TOKEN", "secret-token")
    with dashboard.app.test_client() as client:
        bad = client.post("/ussd/nope", data={})
        assert bad.status_code == 404
        good = client.post("/ussd/secret-token", data={"sessionId":"r1", "phoneNumber":"0712345678", "text":""})
        assert good.status_code == 200
        assert good.get_data(as_text=True).startswith("CON ")


def test_old_ussd_path_is_not_public():
    with dashboard.app.test_client() as client:
        assert client.post("/ussd").status_code == 404
