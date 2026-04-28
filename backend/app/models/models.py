import enum
from typing import Optional

from sqlalchemy import String, BigInteger, Text, Enum as SQLEnum, JSON, Boolean, SmallInteger, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class InstitutionStatus(enum.IntEnum):
    """机构审核状态"""
    PENDING = 0       # 待审核
    APPROVED = 1      # 已通过
    REJECTED = 2      # 已拒绝


class UserRole(str, enum.Enum):
    """机构用户角色"""
    PRINCIPAL = "principal"
    TEACHER = "teacher"


class AttendanceType(str, enum.Enum):
    """考勤类型"""
    SIGN_IN = "sign_in"     # 签到
    SIGN_OUT = "sign_out"   # 签离


class AttendanceMethod(str, enum.Enum):
    """考勤方式"""
    FACE = "face"           # 人脸识别
    MANUAL = "manual"       # 手动操作


# ============================================================
# 平台管理员表
# ============================================================
class PlatformAdmin(Base):
    __tablename__ = "platform_admin"

    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="用户名")
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, comment="密码哈希")

    def __repr__(self) -> str:
        return f"<PlatformAdmin(id={self.id}, username='{self.username}')>"


# ============================================================
# 机构表
# ============================================================
class Institution(Base):
    __tablename__ = "institution"

    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="机构名称")
    contact_person: Mapped[Optional[str]] = mapped_column(String(50), comment="联系人")
    contact_phone: Mapped[Optional[str]] = mapped_column(String(20), comment="联系电话")
    address: Mapped[Optional[str]] = mapped_column(String(255), comment="地址")
    status: Mapped[int] = mapped_column(
        SmallInteger, default=InstitutionStatus.PENDING.value,
        comment="状态: 0待审核 1已通过 2已拒绝"
    )
    face_enabled: Mapped[bool] = mapped_column(default=False, comment="人脸打卡功能开关")
    face_expire_date: Mapped[Optional[date]] = mapped_column(Date, comment="人脸功能到期时间")

    # 关联关系
    org_users: Mapped[list["OrgUser"]] = relationship(back_populates="institution", lazy="selectin")
    classes: Mapped[list["Class_"]] = relationship(back_populates="institution", lazy="selectin")
    students: Mapped[list["Student"]] = relationship(back_populates="institution", lazy="selectin")
    attendance_records: Mapped[list["AttendanceRecord"]] = relationship(
        back_populates="institution", lazy="dynamic"
    )

    def __repr__(self) -> str:
        return f"<Institution(id={self.id}, name='{self.name}', status={self.status})>"


# ============================================================
# 机构用户表（校长/老师）
# ============================================================
class OrgUser(Base):
    __tablename__ = "org_user"

    institution_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("institution.id"), nullable=False, index=True, comment="所属机构ID"
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="姓名")
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True, comment="手机号/登录账号")
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, comment="密码哈希")
    role: Mapped[str] = mapped_column(
        SQLEnum(UserRole), default=UserRole.TEACHER,
        comment="角色: principal校长 teacher教师"
    )
    permissions: Mapped[Optional[dict]] = mapped_column(JSON, comment="教师权限配置")

    # 关联关系
    institution: Mapped["Institution"] = relationship(back_populates="org_users")

    def __repr__(self) -> str:
        return f"<OrgUser(id={self.id}, name='{self.name}', role='{self.role}')>"


# ============================================================
# 班级表
# ============================================================
class Class_(Base):
    __tablename__ = "class"

    institution_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("institution.id"), nullable=False, index=True, comment="所属机构ID"
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="班级名称")

    # 关联关系
    institution: Mapped["Institution"] = relationship(back_populates="classes")
    students: Mapped[list["Student"]] = relationship(back_populates="class_", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Class_(id={self.id}, name='{self.name}')>"


# ============================================================
# 学员表
# ============================================================
class Student(Base):
    __tablename__ = "student"

    institution_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("institution.id"), nullable=False, index=True, comment="所属机构ID"
    )
    class_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("class.id"), index=True, comment="班级ID"
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="姓名")
    gender: Mapped[Optional[int]] = mapped_column(SmallInteger, comment="性别: 1男 2女")
    face_image_url: Mapped[Optional[str]] = mapped_column(
        String(255), comment="人脸照片URL(COS存储)"
    )
    parent_phone: Mapped[Optional[str]] = mapped_column(
        String(20), index=True, comment="关联家长手机号"
    )
    status: Mapped[int] = mapped_column(
        SmallInteger, default=1, comment="状态: 1在学 0离校"
    )

    # 关联关系
    institution: Mapped["Institution"] = relationship(back_populates="students")
    class_: Mapped[Optional["Class_"]] = relationship(back_populates="students")
    attendance_records: Mapped[list["AttendanceRecord"]] = relationship(
        back_populates="student", lazy="dynamic"
    )

    def __repr__(self) -> str:
        return f"<Student(id={self.id}, name='{self.name}')>"


# ============================================================
# 考勤记录表
# ============================================================
class AttendanceRecord(Base):
    __tablename__ = "attendance_record"

    student_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("student.id"), nullable=False, index=True, comment="学员ID"
    )
    institution_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("institution.id"), nullable=False, index=True, comment="所属机构ID"
    )
    type: Mapped[str] = mapped_column(
        SQLEnum(AttendanceType), nullable=False, comment="类型: sign_in签到 sign_out签离"
    )
    method: Mapped[str] = mapped_column(
        SQLEnum(AttendanceMethod), nullable=False, comment="方式: face人脸 manual手动"
    )
    face_confidence: Mapped[Optional[float]] = mapped_column(
        comment="人脸置信度(0-100)"
    )

    # 关联关系
    student: Mapped["Student"] = relationship(back_populates="attendance_records")
    institution: Mapped["Institution"] = relationship(back_populates="attendance_records")

    def __repr__(self) -> str:
        return (
            f"<AttendanceRecord(id={self.id}, type='{self.type}', "
            f"method='{self.method}', student_id={self.student_id})>"
        )
