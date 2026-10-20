from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class CLISettings(BaseSettings):
    """Validated CLI options; Pydantic Settings parses argv and rejects invalid values."""

    model_config = SettingsConfigDict(cli_parse_args=True, cli_ignore_unknown_args=False,
                                      cli_kebab_case=True, extra="forbid")

    host: str = Field(default="http://localhost:8000", min_length=1)
    repeat: int = Field(default=1, ge=1, le=10000)
    input: str | None = None
    json: str | None = None
    output: str = "-"

    @model_validator(mode="after")
    def one_input_source(self):
        if self.input is not None and self.json is not None:
            raise ValueError("Use either --input or --json, not both.")
        if self.input is None and self.json is None:
            raise ValueError("Provide an input with --input or --json.")
        return self

    def input_path(self) -> Path | None:
        return None if self.input in (None, "-") else Path(self.input)

    def output_path(self) -> Path | None:
        return None if self.output == "-" else Path(self.output)
