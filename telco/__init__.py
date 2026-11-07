"""Configured provider factories. Set SMS_PROVIDER and USSD_PROVIDER in .env."""
import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"), override=False)


def _provider(name):
    return os.getenv(name, "none").strip().lower()


def get_sms():
    provider = _provider("SMS_PROVIDER")
    if provider == "thrivevas":
        from .thrivevas import ThriveVasSms
        return ThriveVasSms()
    if provider == "africastalking":
        from .africastalking import AfricaTalkingSms
        return AfricaTalkingSms()
    from .null import NullSms
    return NullSms()


def get_ussd():
    provider = _provider("USSD_PROVIDER")
    if provider == "thrivevas":
        from .thrivevas import ThriveVasUssd
        return ThriveVasUssd()
    if provider == "africastalking":
        from .africastalking import AfricaTalkingUssd
        return AfricaTalkingUssd()
    from .null import NullUssd
    return NullUssd()
