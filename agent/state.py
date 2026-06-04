import operator
from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage


class ScoutingState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
