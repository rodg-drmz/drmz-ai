from datetime import datetime
from typing import Dict, Any, Optional, Literal
import os
import re
import time
from pydantic import BaseModel, Field
from openai import OpenAI

# ── Chat Stages ───────────────────────────────────────────────
Stage = Literal[
    "chat", "intro", "confirmName", "walletIntro",
    "secureKeywords", "awaitingWallet", "stakingEducation",
    "governanceEducation", "complete"
]

# ── User and Chat State Models ───────────────────────────────
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

# ── Onboarding Logic ──────────────────────────────────────────
class OnboardingLogic:
    def __init__(self):
        self.name_pattern = re.compile(r"^[a-zA-Z0-9_-]{2,}$")
        self.addr_pattern = re.compile(r"addr1[0-9a-z]{20,}", re.I)

    def process_onboarding_message(self, message: str, user_data: UserData) -> tuple[str, UserData, Dict[str, Any]]:
        m = message.strip()
        stage = user_data.stage
        captured = {}

        if stage == "intro":
            user_data.stage = "confirmName"
            return ("What name shall I use to address you?", user_data, {})

        elif stage == "confirmName":
            if self.name_pattern.match(m):
                user_data.name = m
                user_data.stage = "walletIntro"
                return (
                    f"Nice to meet you, {m}. Let's begin with wallets. Do you already have a Cardano wallet, or shall I guide you?",
                    user_data,
                    {"name": m}
                )
            else:
                return ("That name doesn’t seem valid. Try using only letters, numbers, or dashes.", user_data, {})

        elif stage == "walletIntro":
            user_data.stage = "secureKeywords"
            return (
                "🔐 Remember: never share your recovery phrase.\n\nWhen you’re ready, type or paste your wallet address here.",
                user_data,
                {}
            )

        elif stage == "secureKeywords":
            if self.addr_pattern.search(m):
                user_data.wallet_address = m
                user_data.stage = "stakingEducation"
                return (
                    "✅ Wallet received. Let’s talk about staking next. Staking is how you support the Cardano network and earn rewards.",
                    user_data,
                    {"wallet": m}
                )
            else:
                return ("Hmm, that doesn't look like a valid Cardano address. Try again.", user_data, {})

        elif stage == "stakingEducation":
            user_data.stage = "governanceEducation"
            return (
                "🗳️ Now, let’s talk about governance. Cardano allows its community to vote on important proposals. This is called on-chain governance.",
                user_data,
                {}
            )

        elif stage == "governanceEducation":
            user_data.stage = "complete"
            return (
                "🎉 You’ve completed the DRMZ onboarding. You now understand wallets, staking, and governance on Cardano.",
                user_data,
                {}
            )

        return ("I'm not sure how to respond. Please follow the prompts.", user_data, {})

# ── Morpheus Controller ──────────────────────────────────────
class MorpheusController:
    def __init__(self):
        self.onboarding = OnboardingLogic()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.assistant_id = os.getenv("OPENAI_ASSISTANT_ID", "asst_5AyAw1WHxg7eOL847byMYcpr")

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
            # === Run Assistant API ===
            thread = self.client.beta.threads.create()
            self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=m
            )
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self.assistant_id
            )
            while True:
                status = self.client.beta.threads.runs.retrieve(run.id, thread_id=thread.id)
                if status.status == "completed":
                    break
                time.sleep(1)
            messages = self.client.beta.threads.messages.list(thread_id=thread.id)
            response_text = messages.data[0].content[0].text.value
            state.response = response_text

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
