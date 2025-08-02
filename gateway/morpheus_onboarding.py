# morpheus_controller.py

from datetime import datetime
from typing import Dict, Any, Optional, Literal
import re
from pydantic import BaseModel, Field

# ── Data Models ────────────────────────────────────────────────────────────────
Stage = Literal[
    "chat", "intro", "confirmName", "walletIntro",
    "secureKeywords", "awaitingWallet", "stakingEducation",
    "governanceEducation", "complete"
]

class UserData(BaseModel):
    name: Optional[str] = None
    wallet_address: Optional[str] = None
    stage: Stage = "chat"
    onboarding_started: bool = False

class ChatState(BaseModel):
    message: str = ""
    user_data: UserData = Field(default_factory=UserData)
    history: list = Field(default_factory=list)
    response: str = ""
    captured_data: Dict[str, Any] = Field(default_factory=dict)

# ── Hardcoded Onboarding Logic ─────────────────────────────────────────────────
class OnboardingLogic:
    def __init__(self):
        self.name_pattern = re.compile(r"^[a-zA-Z0-9_-]{2,}$")
        self.addr_pattern = re.compile(r"addr1[0-9a-z]{20,}", re.I)

    def process_onboarding_message(self, message: str, user_data: UserData) -> tuple[str, UserData, Dict[str, Any]]:
        # [Your logic block goes here — already implemented in the prior message]
        ...
        return ("I'm not sure how to respond. Please follow the prompts.", user_data, {})

# ── Controller ────────────────────────────────────────────────────────────────
class MorpheusController:
    def __init__(self):
        self.onboarding = OnboardingLogic()

    def process_message(self, state: ChatState) -> ChatState:
        m = state.message.strip()
        ud = state.user_data
        captured = {}

        if m.lower().startswith("drmz initiate") and not ud.onboarding_started:
            ud.onboarding_started = True
            ud.stage = "intro"
            state.response = (
                "🌌 Greetings, seeker of knowledge. I am Morpheus, your guide through the Cardano realm.\n\n"
                "This journey will teach you about wallets, staking, and governance.\n\n"
                "What shall I call you on this adventure?"
            )
        elif ud.onboarding_started and ud.stage != "complete":
            state.response, ud, captured = self.onboarding.process_onboarding_message(m, ud)
        else:
            state.response = "🤖 (OpenAI Assistant logic goes here...)"

        if captured:
            state.captured_data.update(captured)

        if ud.stage == "complete":
            ud.onboarding_started = False
            ud.stage = "chat"

        state.user_data = ud
        state.history.append({
            "user": m,
            "morpheus": state.response,
            "stage": ud.stage,
            "timestamp": datetime.now().isoformat()
        })
        return state
