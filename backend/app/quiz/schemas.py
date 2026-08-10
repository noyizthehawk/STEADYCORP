"""Quiz request/response schemas.

Two response shapes for a question: ``QuizQuestionOut`` (admin, includes the
answer) and ``QuizQuestionPublic`` (buyer, never includes ``correct_index``).
"""

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AdminCreateQuizQuestion(BaseModel):
    "admin creating a question, validotr ensures correct_index is in range"

    prompt: str = Field(min_length=1)
    options: list[str] = Field(
        min_length=2, max_length=6
    )  # available option with a ma x of 6 and min of 2
    correct_index: int = Field(ge=0)  # correct index obviously
    category: str | None = None
    drop_id: int | None = None  # None = global bank

    @model_validator(mode="after")
    def _correct_index_in_range(self):
        if self.correct_index >= len(self.options):
            raise ValueError("correct_index must point at one of the options")
        return self


class AdminQuizQuestionOut(BaseModel):  # quiz question for admin sent by backend
    """Admin-facing, includes the answer."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    prompt: str
    options: list[str]
    correct_index: int
    category: str | None
    drop_id: int | None


class ClientQuizQuestionOut(
    BaseModel
):  # quiz question for buyer, no  correct index, sent by backend
    """same thing as ``AdminQuizQuestionOut`` but without the answer."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    prompt: str
    options: list[str]


class FirstQuizSession(BaseModel):  # first quiz session by buyer
    session_id: int
    question: ClientQuizQuestionOut
    required_correct: int  # K
    total_questions: int  # N
    seconds_per_question: int
    answered: int
    correct: int


class AnswerIn(BaseModel):
    choice_index: int = Field(ge=0)


class AnswerOut(BaseModel):
    result: str  # "next" | "passed" | "failed"
    question: ClientQuizQuestionOut | None = None  # present only when result == "next"
    answered: int
    correct: int
    required_correct: int
    total_questions: int
