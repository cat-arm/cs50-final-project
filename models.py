import uuid
from sqlalchemy import Column, DateTime, String, ForeignKey, UUID, JSON
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timezone

# Define status constants
ACTIVE = "Active"
INACTIVE = "Inactive"
BANNED = "Ban"

# Define your models (tables)
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    bio = Column(String)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role_id = Column(UUID(as_uuid=True), ForeignKey('roles.id'))

    role = relationship("Role", back_populates="users")
    content = relationship("Content", back_populates="creator")

class Role(Base):
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)
    name = Column(String, unique=True)
    permissions = Column(JSON)

    users = relationship("User", back_populates="role")

class Content(Base):
    __tablename__ = "content"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)
    quote = Column(String)
    status = Column(String, default=ACTIVE)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc))

    creator = relationship("User", back_populates="content")