from pandas.core.interchange.dataframe_protocol import Column
from sqlalchemy.orm import Mapped, mapped_column,relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import String, Boolean, DateTime, Integer, func, ForeignKey, Interval, Text
from .database import Base
from datetime import datetime, timedelta, timezone

class Users(Base):

    __tablename__= "users"

    id:Mapped[int]=mapped_column(primary_key=True)
    username:Mapped[str]=mapped_column(String(100),unique=True)
    email:Mapped[str]=mapped_column(String(255),unique=True)
    password: Mapped[str] = mapped_column(String(255),nullable=False)

    phone:Mapped[str]=mapped_column(String(12))
    is_active:Mapped[bool]=mapped_column(Boolean,default=True)
    created_at:Mapped[datetime]= mapped_column(DateTime,server_default=func.now())

    applications = relationship(
        "DWGApplication",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    settings= relationship("UserSettings",
                           back_populates="user",
                           uselist=False,
                           cascade="all,delete-orphan")

class DWGApplication(Base):

    __tablename__= "dwg_application_report"

    application_id:Mapped[int]= mapped_column(primary_key=True,autoincrement=True)

    user_id:Mapped[int]= mapped_column((ForeignKey("users.id")))

    applicant_name:Mapped[str]= mapped_column(String(200))

    ref_id: Mapped[str] = mapped_column(String(50), unique=True)

    file_name:Mapped[str]= mapped_column(String(255))

    report_status:Mapped[str]= mapped_column(String(30),default="pending")

    report_exec_time:Mapped[timedelta|None]= mapped_column(Interval, nullable=True)

    report_error_msg:Mapped[str|None]= mapped_column(Text,nullable=True)

    view_report:Mapped[dict| None]= mapped_column(JSONB, nullable=True)

    pdf_status: Mapped[str] = mapped_column(String(30), default="pending")

    pdf_exec_time: Mapped[timedelta | None] = mapped_column(Interval, nullable=True)

    pdf_error_msg: Mapped[str | None] = mapped_column(Text, nullable=True)

    pdf_path: Mapped[str|None]= mapped_column(Text, nullable=True)

    scrutiny_status: Mapped[str] = mapped_column(String(30), default="pending")

    total_time: Mapped[timedelta | None]= mapped_column(Interval, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now()
    )

    updated_at:Mapped[datetime] = mapped_column(DateTime,
                                                server_default=func.now(),
                                                onupdate=func.now())

    user = relationship("Users", back_populates="applications")


class UserSettings(Base):
    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        unique=True
    )

    dark_mode: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    email_notification: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    sms_notification: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    user = relationship(
        "Users",
        back_populates="settings"
    )



class PasswordResetOtp(Base):

    __tablename__ = "password_reset_otp"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )

    otp: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )