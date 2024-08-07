from typing import List, Optional

from sqlalchemy import (
    ARRAY,
    Boolean,
    DateTime,
    Double,
    Enum,
    ForeignKeyConstraint,
    Index,
    Integer,
    LargeBinary,
    PrimaryKeyConstraint,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship
from sqlalchemy.orm.base import Mapped

Base = declarative_base()


class ChromePod(Base):
    __tablename__ = "ChromePod"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="ChromePod_pkey"),
        Index("ChromePod_chromePodId_key", "chromePodId", unique=True),
    )

    id = mapped_column(Text)
    createdAt = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updatedAt = mapped_column(TIMESTAMP(precision=3), nullable=False)
    chromePodId = mapped_column(Text, nullable=False)
    hostname = mapped_column(Text, nullable=False)
    rdpUsername = mapped_column(Text, nullable=False)
    rdpPassword = mapped_column(Text, nullable=False)
    rdpPort = mapped_column(Integer, nullable=False)

    User: Mapped[List["User"]] = relationship(
        "User", uselist=True, back_populates="ChromePod_"
    )


class InterestsClustersSimilarity(Base):
    __tablename__ = "InterestsClustersSimilarity"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="InterestsClustersSimilarity_pkey"),
    )

    id = mapped_column(Text)
    createdAt = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updatedAt = mapped_column(TIMESTAMP(precision=3), nullable=False)
    cosineSimilarity = mapped_column(Double(53), nullable=False)

    InterestsClusterMatch: Mapped[List["InterestsClusterMatch"]] = relationship(
        "InterestsClusterMatch",
        uselist=True,
        back_populates="InterestsClustersSimilarity_",
    )


class UsersOverallSimilarity(Base):
    __tablename__ = "UsersOverallSimilarity"
    __table_args__ = (PrimaryKeyConstraint("id", name="UsersOverallSimilarity_pkey"),)

    id = mapped_column(Text)
    createdAt = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updatedAt = mapped_column(TIMESTAMP(precision=3), nullable=False)
    overallSimilarity = mapped_column(Double(53), nullable=False)

    UserMatch: Mapped[List["UserMatch"]] = relationship(
        "UserMatch", uselist=True, back_populates="UsersOverallSimilarity_"
    )


class PrismaMigrations(Base):
    __tablename__ = "_prisma_migrations"
    __table_args__ = (PrimaryKeyConstraint("id", name="_prisma_migrations_pkey"),)

    id = mapped_column(String(36))
    checksum = mapped_column(String(64), nullable=False)
    migration_name = mapped_column(String(255), nullable=False)
    started_at = mapped_column(
        DateTime(True), nullable=False, server_default=text("now()")
    )
    applied_steps_count = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    finished_at = mapped_column(DateTime(True))
    logs = mapped_column(Text)
    rolled_back_at = mapped_column(DateTime(True))


class User(Base):
    __tablename__ = "User"
    __table_args__ = (
        ForeignKeyConstraint(
            ["chromePodId"],
            ["ChromePod.id"],
            ondelete="SET NULL",
            onupdate="CASCADE",
            name="User_chromePodId_fkey",
        ),
        PrimaryKeyConstraint("id", name="User_pkey"),
        Index("User_chromePodId_key", "chromePodId", unique=True),
        Index("User_displayName_key", "displayName", unique=True),
        Index("User_email_key", "email", unique=True),
    )

    id = mapped_column(Text)
    createdAt = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updatedAt = mapped_column(TIMESTAMP(precision=3), nullable=False)
    email = mapped_column(Text, nullable=False)
    password = mapped_column(Text, nullable=False)
    confirmationCode = mapped_column(Text, nullable=False)
    displayName = mapped_column(Text, nullable=False)
    gender = mapped_column(
        Enum("Male", "Female", "Other", name="Gender"), nullable=False
    )
    geographyLat = mapped_column(Double(53), nullable=False)
    geographyLon = mapped_column(Double(53), nullable=False)
    confirmedAt = mapped_column(TIMESTAMP(precision=3))
    streamChatToken = mapped_column(Text)
    chromePodId = mapped_column(Text)

    ChromePod_: Mapped[Optional["ChromePod"]] = relationship(
        "ChromePod", back_populates="User"
    )
    Session: Mapped[List["Session"]] = relationship(
        "Session", uselist=True, back_populates="User_"
    )
    UserInterests: Mapped[List["UserInterests"]] = relationship(
        "UserInterests", uselist=True, back_populates="User_"
    )
    UserMatch: Mapped[List["UserMatch"]] = relationship(
        "UserMatch", uselist=True, back_populates="User_"
    )
    UserTraits: Mapped[List["UserTraits"]] = relationship(
        "UserTraits", uselist=True, back_populates="User_"
    )


class Session(Base):
    __tablename__ = "Session"
    __table_args__ = (
        ForeignKeyConstraint(
            ["userId"],
            ["User.id"],
            ondelete="CASCADE",
            onupdate="CASCADE",
            name="Session_userId_fkey",
        ),
        PrimaryKeyConstraint("id", name="Session_pkey"),
        Index("Session_userId_key", "userId", unique=True),
    )

    id = mapped_column(Text)
    createdAt = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updatedAt = mapped_column(TIMESTAMP(precision=3), nullable=False)
    sessionSecret = mapped_column(LargeBinary, nullable=False)
    userId = mapped_column(Text)

    User_: Mapped[Optional["User"]] = relationship("User", back_populates="Session")


class UserInterests(Base):
    __tablename__ = "UserInterests"
    __table_args__ = (
        ForeignKeyConstraint(
            ["userId"],
            ["User.id"],
            ondelete="CASCADE",
            onupdate="CASCADE",
            name="UserInterests_userId_fkey",
        ),
        PrimaryKeyConstraint("id", name="UserInterests_pkey"),
        Index("UserInterests_userId_key", "userId", unique=True),
    )

    id = mapped_column(Text)
    createdAt = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updatedAt = mapped_column(TIMESTAMP(precision=3), nullable=False)
    userId = mapped_column(Text, nullable=False)

    User_: Mapped["User"] = relationship("User", back_populates="UserInterests")
    InterestsCluster: Mapped[List["InterestsCluster"]] = relationship(
        "InterestsCluster", uselist=True, back_populates="UserInterests_"
    )


class UserMatch(Base):
    __tablename__ = "UserMatch"
    __table_args__ = (
        ForeignKeyConstraint(
            ["userId"],
            ["User.id"],
            ondelete="RESTRICT",
            onupdate="CASCADE",
            name="UserMatch_userId_fkey",
        ),
        ForeignKeyConstraint(
            ["usersOverallSimilarityId"],
            ["UsersOverallSimilarity.id"],
            ondelete="RESTRICT",
            onupdate="CASCADE",
            name="UserMatch_usersOverallSimilarityId_fkey",
        ),
        PrimaryKeyConstraint("id", name="UserMatch_pkey"),
        Index(
            "UserMatch_userId_usersOverallSimilarityId_key",
            "userId",
            "usersOverallSimilarityId",
            unique=True,
        ),
    )

    id = mapped_column(Text)
    createdAt = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updatedAt = mapped_column(TIMESTAMP(precision=3), nullable=False)
    userId = mapped_column(Text, nullable=False)
    usersOverallSimilarityId = mapped_column(Text, nullable=False)

    User_: Mapped["User"] = relationship("User", back_populates="UserMatch")
    UsersOverallSimilarity_: Mapped["UsersOverallSimilarity"] = relationship(
        "UsersOverallSimilarity", back_populates="UserMatch"
    )


class UserTraits(Base):
    __tablename__ = "UserTraits"
    __table_args__ = (
        ForeignKeyConstraint(
            ["userId"],
            ["User.id"],
            ondelete="CASCADE",
            onupdate="CASCADE",
            name="UserTraits_userId_fkey",
        ),
        PrimaryKeyConstraint("id", name="UserTraits_pkey"),
        Index("UserTraits_userId_key", "userId", unique=True),
    )

    id = mapped_column(Text)
    createdAt = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updatedAt = mapped_column(TIMESTAMP(precision=3), nullable=False)
    userId = mapped_column(Text, nullable=False)

    User_: Mapped["User"] = relationship("User", back_populates="UserTraits")
    BigFive: Mapped[List["BigFive"]] = relationship(
        "BigFive", uselist=True, back_populates="UserTraits_"
    )
    Mbti: Mapped[List["Mbti"]] = relationship(
        "Mbti", uselist=True, back_populates="UserTraits_"
    )
    MoralFoundations: Mapped[List["MoralFoundations"]] = relationship(
        "MoralFoundations", uselist=True, back_populates="UserTraits_"
    )
    PoliticalCompass: Mapped[List["PoliticalCompass"]] = relationship(
        "PoliticalCompass", uselist=True, back_populates="UserTraits_"
    )
    Riasec: Mapped[List["Riasec"]] = relationship(
        "Riasec", uselist=True, back_populates="UserTraits_"
    )
    SixteenPersonalityFactor: Mapped[List["SixteenPersonalityFactor"]] = relationship(
        "SixteenPersonalityFactor", uselist=True, back_populates="UserTraits_"
    )


class BigFive(Base):
    __tablename__ = "BigFive"
    __table_args__ = (
        ForeignKeyConstraint(
            ["userTraitsId"],
            ["UserTraits.id"],
            ondelete="CASCADE",
            onupdate="CASCADE",
            name="BigFive_userTraitsId_fkey",
        ),
        PrimaryKeyConstraint("id", name="BigFive_pkey"),
    )

    id = mapped_column(Text)
    createdAt = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updatedAt = mapped_column(TIMESTAMP(precision=3), nullable=False)
    openness = mapped_column(Double(53), nullable=False)
    conscientiousness = mapped_column(Double(53), nullable=False)
    extraversion = mapped_column(Double(53), nullable=False)
    agreeableness = mapped_column(Double(53), nullable=False)
    neuroticism = mapped_column(Double(53), nullable=False)
    userTraitsId = mapped_column(Text, nullable=False)
    summary = mapped_column(Text)

    UserTraits_: Mapped["UserTraits"] = relationship(
        "UserTraits", back_populates="BigFive"
    )


class InterestsCluster(Base):
    __tablename__ = "InterestsCluster"
    __table_args__ = (
        ForeignKeyConstraint(
            ["userInterestsId"],
            ["UserInterests.id"],
            ondelete="CASCADE",
            onupdate="CASCADE",
            name="InterestsCluster_userInterestsId_fkey",
        ),
        PrimaryKeyConstraint("id", name="InterestsCluster_pkey"),
        Index(
            "InterestsCluster_userInterestsId_pipelineClusterId_clusterT_key",
            "userInterestsId",
            "pipelineClusterId",
            "clusterType",
            unique=True,
        ),
    )

    id = mapped_column(Text)
    createdAt = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updatedAt = mapped_column(TIMESTAMP(precision=3), nullable=False)
    pipelineClusterId = mapped_column(Integer, nullable=False)
    clusterType = mapped_column(Text, nullable=False)
    summary = mapped_column(Text, nullable=False)
    title = mapped_column(Text, nullable=False)
    userInterestsId = mapped_column(Text, nullable=False)
    activityDates = mapped_column(ARRAY(Text()))

    UserInterests_: Mapped["UserInterests"] = relationship(
        "UserInterests", back_populates="InterestsCluster"
    )
    InterestsClusterMatch: Mapped[List["InterestsClusterMatch"]] = relationship(
        "InterestsClusterMatch", uselist=True, back_populates="InterestsCluster_"
    )


class Mbti(Base):
    __tablename__ = "Mbti"
    __table_args__ = (
        ForeignKeyConstraint(
            ["userTraitsId"],
            ["UserTraits.id"],
            ondelete="CASCADE",
            onupdate="CASCADE",
            name="Mbti_userTraitsId_fkey",
        ),
        PrimaryKeyConstraint("id", name="Mbti_pkey"),
    )

    id = mapped_column(Text)
    createdAt = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updatedAt = mapped_column(TIMESTAMP(precision=3), nullable=False)
    extraversion = mapped_column(Boolean, nullable=False)
    sensing = mapped_column(Boolean, nullable=False)
    thinking = mapped_column(Boolean, nullable=False)
    judging = mapped_column(Boolean, nullable=False)
    userTraitsId = mapped_column(Text, nullable=False)
    summary = mapped_column(Text)

    UserTraits_: Mapped["UserTraits"] = relationship(
        "UserTraits", back_populates="Mbti"
    )


class MoralFoundations(Base):
    __tablename__ = "MoralFoundations"
    __table_args__ = (
        ForeignKeyConstraint(
            ["userTraitsId"],
            ["UserTraits.id"],
            ondelete="CASCADE",
            onupdate="CASCADE",
            name="MoralFoundations_userTraitsId_fkey",
        ),
        PrimaryKeyConstraint("id", name="MoralFoundations_pkey"),
    )

    id = mapped_column(Text)
    createdAt = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updatedAt = mapped_column(TIMESTAMP(precision=3), nullable=False)
    careHarm = mapped_column(Double(53), nullable=False)
    fairnessCheating = mapped_column(Double(53), nullable=False)
    loyaltyBetrayal = mapped_column(Double(53), nullable=False)
    authoritySubversion = mapped_column(Double(53), nullable=False)
    sanctityDegradation = mapped_column(Double(53), nullable=False)
    goodCheck = mapped_column(Double(53), nullable=False)
    mathCheck = mapped_column(Double(53), nullable=False)
    userTraitsId = mapped_column(Text, nullable=False)
    summary = mapped_column(Text)

    UserTraits_: Mapped["UserTraits"] = relationship(
        "UserTraits", back_populates="MoralFoundations"
    )


class PoliticalCompass(Base):
    __tablename__ = "PoliticalCompass"
    __table_args__ = (
        ForeignKeyConstraint(
            ["userTraitsId"],
            ["UserTraits.id"],
            ondelete="CASCADE",
            onupdate="CASCADE",
            name="PoliticalCompass_userTraitsId_fkey",
        ),
        PrimaryKeyConstraint("id", name="PoliticalCompass_pkey"),
    )

    id = mapped_column(Text)
    createdAt = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updatedAt = mapped_column(TIMESTAMP(precision=3), nullable=False)
    economic = mapped_column(Double(53), nullable=False)
    social = mapped_column(Double(53), nullable=False)
    userTraitsId = mapped_column(Text, nullable=False)
    summary = mapped_column(Text)

    UserTraits_: Mapped["UserTraits"] = relationship(
        "UserTraits", back_populates="PoliticalCompass"
    )


class Riasec(Base):
    __tablename__ = "Riasec"
    __table_args__ = (
        ForeignKeyConstraint(
            ["userTraitsId"],
            ["UserTraits.id"],
            ondelete="CASCADE",
            onupdate="CASCADE",
            name="Riasec_userTraitsId_fkey",
        ),
        PrimaryKeyConstraint("id", name="Riasec_pkey"),
    )

    id = mapped_column(Text)
    createdAt = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updatedAt = mapped_column(TIMESTAMP(precision=3), nullable=False)
    realistic = mapped_column(Double(53), nullable=False)
    investigative = mapped_column(Double(53), nullable=False)
    artistic = mapped_column(Double(53), nullable=False)
    social = mapped_column(Double(53), nullable=False)
    enterprising = mapped_column(Double(53), nullable=False)
    conventional = mapped_column(Double(53), nullable=False)
    userTraitsId = mapped_column(Text, nullable=False)
    summary = mapped_column(Text)

    UserTraits_: Mapped["UserTraits"] = relationship(
        "UserTraits", back_populates="Riasec"
    )


class SixteenPersonalityFactor(Base):
    __tablename__ = "SixteenPersonalityFactor"
    __table_args__ = (
        ForeignKeyConstraint(
            ["userTraitsId"],
            ["UserTraits.id"],
            ondelete="CASCADE",
            onupdate="CASCADE",
            name="SixteenPersonalityFactor_userTraitsId_fkey",
        ),
        PrimaryKeyConstraint("id", name="SixteenPersonalityFactor_pkey"),
    )

    id = mapped_column(Text)
    createdAt = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updatedAt = mapped_column(TIMESTAMP(precision=3), nullable=False)
    warmth = mapped_column(Double(53), nullable=False)
    reasoning = mapped_column(Double(53), nullable=False)
    emotionalStability = mapped_column(Double(53), nullable=False)
    dominance = mapped_column(Double(53), nullable=False)
    liveliness = mapped_column(Double(53), nullable=False)
    ruleConsciousness = mapped_column(Double(53), nullable=False)
    socialBoldness = mapped_column(Double(53), nullable=False)
    sensitivity = mapped_column(Double(53), nullable=False)
    vigilance = mapped_column(Double(53), nullable=False)
    abstractedness = mapped_column(Double(53), nullable=False)
    privateness = mapped_column(Double(53), nullable=False)
    apprehension = mapped_column(Double(53), nullable=False)
    opennessToChange = mapped_column(Double(53), nullable=False)
    selfReliance = mapped_column(Double(53), nullable=False)
    perfectionism = mapped_column(Double(53), nullable=False)
    tension = mapped_column(Double(53), nullable=False)
    userTraitsId = mapped_column(Text, nullable=False)
    summary = mapped_column(Text)

    UserTraits_: Mapped["UserTraits"] = relationship(
        "UserTraits", back_populates="SixteenPersonalityFactor"
    )


class InterestsClusterMatch(Base):
    __tablename__ = "InterestsClusterMatch"
    __table_args__ = (
        ForeignKeyConstraint(
            ["interestsClusterId"],
            ["InterestsCluster.id"],
            ondelete="RESTRICT",
            onupdate="CASCADE",
            name="InterestsClusterMatch_interestsClusterId_fkey",
        ),
        ForeignKeyConstraint(
            ["interestsClustersSimilarityId"],
            ["InterestsClustersSimilarity.id"],
            ondelete="RESTRICT",
            onupdate="CASCADE",
            name="InterestsClusterMatch_interestsClustersSimilarityId_fkey",
        ),
        PrimaryKeyConstraint("id", name="InterestsClusterMatch_pkey"),
        Index(
            "InterestsClusterMatch_interestsClusterId_interestsClustersS_key",
            "interestsClusterId",
            "interestsClustersSimilarityId",
            unique=True,
        ),
    )

    id = mapped_column(Text)
    createdAt = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updatedAt = mapped_column(TIMESTAMP(precision=3), nullable=False)
    interestsClusterId = mapped_column(Text, nullable=False)
    interestsClustersSimilarityId = mapped_column(Text, nullable=False)

    InterestsCluster_: Mapped["InterestsCluster"] = relationship(
        "InterestsCluster", back_populates="InterestsClusterMatch"
    )
    InterestsClustersSimilarity_: Mapped["InterestsClustersSimilarity"] = relationship(
        "InterestsClustersSimilarity", back_populates="InterestsClusterMatch"
    )
