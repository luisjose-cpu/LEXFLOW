from dataclasses import dataclass


@dataclass(frozen=True)
class JudicialAdapterResult:
    source_type: str
    title: str
    summary: str
    captcha_required: bool
    evidence_payload: dict[str, object]


class JudicialAdapterMock:
    source_type = "generic"

    def check(self, *, external_case_number: str) -> JudicialAdapterResult:
        captcha_required = external_case_number.upper().endswith("CAPTCHA")
        return JudicialAdapterResult(
            source_type=self.source_type,
            title=f"{self.source_type.upper()} update for {external_case_number}",
            summary="Mock authorized judicial source response.",
            captcha_required=captcha_required,
            evidence_payload={
                "adapter": self.source_type,
                "external_case_number": external_case_number,
                "mock": True,
                "captcha_required": captcha_required,
            },
        )


class PoderJudicialAdapterMock(JudicialAdapterMock):
    source_type = "poder_judicial"


class CEJAdapterMock(JudicialAdapterMock):
    source_type = "cej"


class SINOEAdapterMock(JudicialAdapterMock):
    source_type = "sinoe"


class MPFNAdapterMock(JudicialAdapterMock):
    source_type = "mpfn"


ADAPTERS = {
    "poder_judicial": PoderJudicialAdapterMock(),
    "cej": CEJAdapterMock(),
    "sinoe": SINOEAdapterMock(),
    "mpfn": MPFNAdapterMock(),
}


def get_adapter(source_type: str) -> JudicialAdapterMock:
    return ADAPTERS.get(source_type, JudicialAdapterMock())
