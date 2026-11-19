from ptlite.model import ModelAnswer, ModelOutputError, Reply, ask_with_retry


class FakeClient:
    def __init__(self, scripted: list[ModelAnswer | Exception]):
        self.scripted = list(scripted)
        self.calls: list[str] = []

    def ask(self, system, contract, question):
        self.calls.append(question)
        nxt = self.scripted.pop(0)
        if isinstance(nxt, Exception):
            raise nxt
        return Reply(answer=nxt, model="fake-model", cache_read_tokens=0)


def test_bad_output_is_retried_once_then_recorded():
    fake = FakeClient([ModelOutputError("refusal"), ModelOutputError("refusal")])
    result = ask_with_retry(fake, "sys", "contract", "q")
    assert isinstance(result, ModelOutputError)
    assert len(fake.calls) == 2
