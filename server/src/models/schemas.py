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
    channel_id: str
    content: str = ""
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
    channel_id: str
    content: str = ""
    title: str = ""
    vol: str = ""
    timestamp: str = ""
    genres: list[str] = Field(default_factory=list)
    slots: list[SlotData] = Field(default_factory=list)
    names_only: bool = False
    social_links: dict[str, str] = Field(default_factory=dict)
    image_url: str = ""


class MessageRequest(BaseModel):
    channel_id: str
    content: str


class UpdateScheduleRequest(BaseModel):
    """Partial update for a scheduled post — only supplied fields are changed."""
    post_at_utc: str | None = None
    channel_id: str | None = None
    content: str | None = None
    title: str | None = None
    vol: str | None = None
    timestamp: str | None = None
    genres: list[str] | None = None
    slots: list[SlotData] | None = None
    names_only: bool | None = None
    social_links: dict[str, str] | None = None
    image_url: str | None = None


class ResendRequest(BaseModel):
    """Optional override for resending a previously sent post."""
    channel_id: str | None = None


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
    display_name: str = ""
    links: dict[str, str] = Field(default_factory=dict)
    logo: str = ""
    bio: str = ""
    genres: list[str] = Field(default_factory=list)
    availability: list[dict] = Field(default_factory=list)


class ClubUpdate(BaseModel):
    discord_link: str = ""


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
    vrchat_user_id: str  # from the bio-verification step — used to confirm ownership


class VRChatVerifyBioRequest(BaseModel):
    vrchat_username: str
    verification_code: str
