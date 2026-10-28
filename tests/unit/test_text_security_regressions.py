"""Keep hostile long text and punctuation handling bounded and unambiguous."""
from app.api.routers.mobile_acp import _trim_recovery_locator_token
from app.services.home_chat import pretty_model, scrub_model_reply
from app.services.payment_text_parse import parse_payment_text


def test_long_model_output_preserves_answers_and_removes_only_classifier_lines():
    text = "Assistant" + " " * 50000 + "Safety: safe\nAnswer: two words stay"
    assert scrub_model_reply(text) == "Answer: two words stay"
    assert scrub_model_reply("User Safety: two words") == "User Safety: two words"
    assert pretty_model("vendor/" + "7" * 50000 + "x").endswith("x")


def test_long_payment_whitespace_does_not_invent_amount_or_currency():
    parsed = parse_payment_text("invoice" + " " * 50000 + "!\nnetwork" + " " * 50000 + "?")
    assert parsed.amount is None
    assert parsed.currency is None


def test_recovery_locator_trims_only_outer_wrapper_punctuation():
    assert _trim_recovery_locator_token('  <["https://example.org/a?x=1"],;:.  ') == "https://example.org/a?x=1"
    assert _trim_recovery_locator_token("x" + "." * 100000) == "x"
