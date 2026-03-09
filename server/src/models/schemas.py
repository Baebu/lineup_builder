"""
Pydantic request/response models for the API.
"""

from pydantic import BaseModel, Field


class SlotData(BaseModel):
    name: str = ""
    genre: str = ""
    duration: int = 60


class DJInfo(BaseModel):
    name: str = ""
    stream: str = ""
    exact_link: bool = False


class EmbedRequest(BaseModel):
    """Mirrors EventSnapshot — everything needed to build the Discord embed."""
    channel_id: int
    title: str = ""
    vol: str = ""
    timestamp: str = ""  # "YYYY-MM-DD HH:MM"
    genres: list[str] = Field(default_factory=list)
    slots: list[SlotData] = Field(default_factory=list)
    names_only: bool = False
    social_links: dict[str, str] = Field(default_factory=dict)
    image_url: str = ""  # Optional URL for embed image


class ScheduleRequest(BaseModel):
    """Schedule a post for a future time."""
    post_at_utc: str  # ISO 8601 datetime string
    channel_id: int
    title: str = ""
    vol: str = ""
    timestamp: str = ""
    genres: list[str] = Field(default_factory=list)
    slots: list[SlotData] = Field(default_factory=list)
    names_only: bool = False
    social_links: dict[str, str] = Field(default_factory=dict)
    image_url: str = ""


class MessageRequest(BaseModel):
    channel_id: int
    content: str


class DJRegisterRequest(BaseModel):
    name: str
    password: str


class DJLoginRequest(BaseModel):
    name: str
    password: str


class DJDiscordAuthRequest(BaseModel):
    discord_id: str
    name: str


class DJProfileUpdate(BaseModel):
    name: str  # identifies the DJ
    links: dict[str, str] = Field(default_factory=dict)
    logo: str = ""
    genres: list[str] = Field(default_factory=list)
    availability: list[dict] = Field(default_factory=list)


class BookingCreateRequest(BaseModel):
    dj_name: str
    group_name: str = ""
    event_title: str = ""
    event_date: str = ""
    start_time: str = ""
    duration: int = 60
    message: str = ""
    discord_channel_id: int | None = None


class BookingRespondRequest(BaseModel):
    status: str  # "accepted" or "declined"


class UserDataPut(BaseModel):
    value: dict | list


class VRChatGroupVerifyRequest(BaseModel):
    group_id: str
    discord_id: str


class VRChatVerifyBioRequest(BaseModel):
    vrchat_username: str
    verification_code: str
