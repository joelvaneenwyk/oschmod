# -*- coding: utf-8 -*-
# pylint: disable=too-many-lines
"""oschmod module.

Module for working with file permissions that are consistent across Windows,
macOS, and Linux.

These bitwise permissions from the stat module can be used with this module:
    stat.S_IRWXU   # Mask for file owner permissions
    stat.S_IREAD   # Owner has read permission
    stat.S_IRUSR   # Owner has read permission
    stat.S_IWRITE  # Owner has write permission
    stat.S_IWUSR   # Owner has write permission
    stat.S_IEXEC   # Owner has execute permission
    stat.S_IXUSR   # Owner has execute permission

    stat.S_IRWXG   # Mask for group permissions
    stat.S_IRGRP   # Group has read permission
    stat.S_IWGRP   # Group has write permission
    stat.S_IXGRP   # Group has execute permission

    stat.S_IRWXO   # Mask for permissions for others (not in group)
    stat.S_IROTH   # Others have read permission
    stat.S_IWOTH   # Others have write permission
    stat.S_IXOTH   # Others have execute permission

"""
# cspell:ignore DACL dacl Dacl DELET DIREX DIRRD DIRWR FADFL FADSD FDLCH FGNEX
# cspell:ignore FGNRD FGNWR FILEX FILRD FILWR FLDIR FRDAT FRDEA FTRAV FWRAT FWREA
# cspell:ignore GENEX GENRD GENWR getgrgid OPER oper RDCON topdown ugoa WRDAC WROWN

import os
import pathlib
import platform
import random
import re
import stat
import string
from enum import IntEnum, auto
from typing import (
    TYPE_CHECKING,
    Any,
    Final,
    Generic,
    List,
    Mapping,
    NewType,
    Optional,
    Tuple,
    TypeVar,
    Union,
)

__version__: str = "0.3.12"

IS_WINDOWS: Final[bool] = platform.system() == "Windows"

ModePathInput = Union[pathlib.Path, str]  # pylint: disable=unsubscriptable-object
ModePathInternal = NewType("ModePathInternal", str)
ModeInputValue = Union[int, str]
ModeValue = int
ModeSidObject = Union[Tuple[str, str, Any], str]
PyACE = Tuple[Tuple[int, int], int, "PySID"]
PySidValue = Tuple[str, str, Any]
PySidDefault: PySidValue = ("", "", 0)

try:
    from pywintypes import error  # type: ignore[import-untyped]
except ImportError:
    if TYPE_CHECKING:
        raise

    class error(Exception):  # type: ignore[no-redef]  # pylint: disable=invalid-name
        """Placeholder error class."""


if TYPE_CHECKING:
    try:
        from _win32typing import (  # type: ignore[reportMissingModuleSource,import-not-found]
            PyACL,
            PySECURITY_DESCRIPTOR,
            PySID,
        )
    except ImportError as import_error:
        raise ImportError("Failed to import win32typing from pywin32 library.") from import_error
else:
    #
    # If we are not type checking, then still create placeholder classes.
    #

    class PySID:  # type: ignore  # pylint: disable=too-few-public-methods
        """Placeholder class on import error."""

        def GetAceCount(self) -> int:  # pylint: disable=invalid-name
            """Get ACE count."""
            return 0

    class PyACL:  # type: ignore  # pylint: disable=too-few-public-methods,invalid-name
        """Placeholder class on import error."""

        def GetAce(self, index: int) -> "PyACE":  # pylint: disable=unused-argument
            """Get details."""
            return (0, 0), 0, PySID()

        def GetAclRevision(self) -> int:  # pylint: disable=invalid-name
            """Get revision."""
            return 0

        def AddAccessAllowedAceEx(  # pylint: disable=invalid-name
            self, __revision: int, __aceflags: int, __access: int, __sid: PySID
        ) -> None:
            """Add access."""

    class PySECURITY_DESCRIPTOR:  # type: ignore  # pylint: disable=invalid-name
        """Placeholder class on import error."""

        def SetSecurityDescriptorDacl(self, *args: Any, **kwargs: Any) -> None:
            """Set security description."""

        def GetSecurityDescriptorDacl(self) -> PySID:
            """Return security descriptor."""
            return _get_default_descriptor()

        def GetSecurityDescriptorOwner(self) -> PySID:
            """Return security owner."""
            return _get_default_descriptor()

        def GetSecurityDescriptorGroup(self) -> PySID:
            """Return security group."""
            return _get_default_descriptor()


def _get_default_descriptor() -> PySID:
    return PySID()


def _get_default_security_descriptor() -> PySECURITY_DESCRIPTOR:
    return PySECURITY_DESCRIPTOR()


def _get_default_security() -> PySidValue:
    return "", "", 0


SystemName = Optional[str]
SYSTEM_NAME_NONE: SystemName = None

win32security: Any = None
try:
    import win32security  # type: ignore[reportMissingModuleSource,import-not-found,no-redef]
    from win32security import (  # type: ignore[reportMissingModuleSource,import-not-found]  # pylint: disable=ungrouped-imports
        ACCESS_ALLOWED_ACE_TYPE,
        DACL_SECURITY_INFORMATION,
        GROUP_SECURITY_INFORMATION,
        NO_INHERITANCE,
        OWNER_SECURITY_INFORMATION,
        SE_FILE_OBJECT,
        ConvertStringSidToSid,  # type: ignore[misc]
        GetFileSecurity,  # type: ignore[misc]
        GetNamedSecurityInfo,  # type: ignore[misc]
        LookupAccountSid,  # type: ignore[misc]
        SetFileSecurity,  # type: ignore[misc]
    )
except ImportError:
    ACCESS_ALLOWED_ACE_TYPE = 0  # type: ignore[assignment]
    ACCESS_DENIED_ACE_TYPE = 0  # type: ignore[assignment]
    DACL_SECURITY_INFORMATION = 0  # type: ignore[assignment]
    GROUP_SECURITY_INFORMATION = 0  # type: ignore[assignment]
    NO_INHERITANCE = 0  # type: ignore[assignment]
    OWNER_SECURITY_INFORMATION = 0  # type: ignore[assignment]
    SE_FILE_OBJECT = 0  # type: ignore[assignment]

    def ConvertStringSidToSid(StringSid: str) -> PySID:  # type: ignore[misc]  # pylint: disable=unused-argument,invalid-name
        """Convert identifier."""
        return _get_default_descriptor()

    def GetFileSecurity(filename: str, info: Any) -> PySECURITY_DESCRIPTOR:  # type: ignore[misc]  # pylint: disable=unused-argument,invalid-name
        """Get file security."""
        return _get_default_security_descriptor()

    def GetNamedSecurityInfo(  # type: ignore[misc]  # pylint: disable=unused-argument,invalid-name
        ObjectName: Any, ObjectType: Any, SecurityInfo: Any
    ) -> PySECURITY_DESCRIPTOR:
        """Get named security."""
        return _get_default_security_descriptor()

    def LookupAccountSid(systemName: SystemName, sid: PySID) -> PySidValue:  # type: ignore[misc]  # pylint: disable=unused-argument,invalid-name
        """Lookup account security."""
        return _get_default_security()

    def SetFileSecurity(  # type: ignore[misc]  # pylint: disable=unused-argument,invalid-name
        filename: str, info: Any, security: PySECURITY_DESCRIPTOR
    ) -> None:
        """Set file-level security."""


def _get_account_sid(systemName: SystemName, sid: PySID) -> PySidValue:  # type: ignore[misc]  # pylint: disable=unused-argument,invalid-name
    """Lookup account security."""
    return LookupAccountSid(systemName, sid)  # type: ignore[arg-type]


ntsecuritycon: Any = None
try:
    from ntsecuritycon import (  # type: ignore
        DELETE,
        FILE_ADD_FILE,
        FILE_ADD_SUBDIRECTORY,
        FILE_DELETE_CHILD,
        FILE_GENERIC_EXECUTE,
        FILE_GENERIC_READ,
        FILE_GENERIC_WRITE,
        FILE_LIST_DIRECTORY,
        FILE_READ_ATTRIBUTES,
        FILE_READ_EA,
        FILE_TRAVERSE,
        FILE_WRITE_ATTRIBUTES,
        FILE_WRITE_EA,
        GENERIC_ALL,
        GENERIC_EXECUTE,
        GENERIC_READ,
        GENERIC_WRITE,
        INHERIT_ONLY_ACE,
        OBJECT_INHERIT_ACE,
        READ_CONTROL,
        SYNCHRONIZE,
        WRITE_DAC,
        WRITE_OWNER,
    )
    import ntsecuritycon  # type: ignore[import-untyped,import-not-found,no-redef]  # isort: skip

    HAS_PYWIN32: Final[bool] = True
except ImportError:
    HAS_PYWIN32: Final[bool] = False  # type: ignore[assignment,misc,no-redef]

    GROUP_SECURITY_INFORMATION = 0  # type: ignore[assignment]
    DELETE = 0  # type: ignore[assignment]
    FILE_ADD_FILE = 0  # type: ignore[assignment]
    FILE_ADD_SUBDIRECTORY = 0  # type: ignore[assignment]
    FILE_DELETE_CHILD = 0  # type: ignore[assignment]
    FILE_GENERIC_EXECUTE = 0  # type: ignore[assignment]
    FILE_GENERIC_READ = 0  # type: ignore[assignment]
    FILE_GENERIC_WRITE = 0  # type: ignore[assignment]
    FILE_LIST_DIRECTORY = 0  # type: ignore[assignment]
    FILE_READ_ATTRIBUTES = 0  # type: ignore[assignment]
    FILE_READ_EA = 0  # type: ignore[assignment]
    FILE_TRAVERSE = 0  # type: ignore[assignment]
    FILE_WRITE_ATTRIBUTES = 0  # type: ignore[assignment]
    FILE_WRITE_EA = 0  # type: ignore[assignment]
    GENERIC_ALL = 0  # type: ignore[assignment]
    GENERIC_EXECUTE = 0  # type: ignore[assignment]
    GENERIC_READ = 0  # type: ignore[assignment]
    GENERIC_WRITE = 0  # type: ignore[assignment]
    INHERIT_ONLY_ACE = 0  # type: ignore[assignment]
    OBJECT_INHERIT_ACE = 0  # type: ignore[assignment]
    READ_CONTROL = 0  # type: ignore[assignment]
    SYNCHRONIZE = 0  # type: ignore[assignment]
    WRITE_DAC = 0  # type: ignore[assignment]
    WRITE_OWNER = 0  # type: ignore[assignment]


try:
    from grp import getgrgid, struct_group  # type: ignore  # noqa: F401
    from pwd import getpwuid, struct_passwd  # type: ignore  # noqa: F401

    HAS_PWD: Final[bool] = True
except ImportError:
    HAS_PWD: Final[bool] = False  # type: ignore[assignment,misc,no-redef]

    try:
        from _typeshed import structseq  # type: ignore
    except ImportError:
        _T_co = TypeVar("_T_co", covariant=True)

        class structseq(Generic[_T_co]):  # type: ignore[no-redef]  # pylint: disable=invalid-name,too-few-public-methods
            """Placeholder class on import error."""

    class struct_passwd(structseq[Any], Tuple[str, str, int, int, str, str, str]):  # type: ignore[no-redef]  # pylint: disable=too-few-public-methods,invalid-name
        """Placeholder class on import error."""

        @property
        def pw_name(self) -> str:
            """Placeholder."""
            return ""

    class struct_group(structseq[Any], Tuple[str, Optional[str], int, List[str]]):  # type: ignore[no-redef]  # pylint: disable=too-few-public-methods,invalid-name
        """Placeholder class on import error."""

        @property
        def gr_name(self) -> str:
            """Placeholder."""
            return ""

        @property
        def gr_passwd(self) -> Optional[str]:
            """Placeholder."""
            return None

        @property
        def gr_gid(self) -> int:
            """Placeholder."""
            return 0

        @property
        def gr_mem(self) -> List[str]:
            """Placeholder."""
            return []

    def getpwuid(__uid: int) -> struct_passwd:  # type: ignore[misc]  # pylint: disable=unused-argument
        """Get user identifier."""
        return struct_passwd([])

    def getgrgid(__uid: int) -> struct_group:  # type: ignore[misc]   # pylint: disable=unused-argument
        """Get group identifier."""
        return struct_group([])


class ModeObjectType(IntEnum):
    """Enum for object type of directory or file."""

    FILE = auto()
    DIRECTORY = auto()


class ModeUserType(IntEnum):
    """Enum for user type."""

    OWNER = auto()
    GROUP = auto()
    OTHER = auto()


class ModeOperationType(IntEnum):
    """Enum for operation type."""

    READ = auto()
    WRITE = auto()
    EXECUTE = auto()

    @staticmethod
    def values() -> List["ModeOperationType"]:
        """Return list of values."""
        return [
            ModeOperationType.READ,
            ModeOperationType.WRITE,
            ModeOperationType.EXECUTE,
        ]


STAT_MODES: Mapping[ModeUserType, Mapping[ModeOperationType, ModeValue]] = {
    ModeUserType.OWNER: {
        ModeOperationType.READ: stat.S_IRUSR,
        ModeOperationType.WRITE: stat.S_IWUSR,
        ModeOperationType.EXECUTE: stat.S_IXUSR,
    },
    ModeUserType.GROUP: {
        ModeOperationType.READ: stat.S_IRGRP,
        ModeOperationType.WRITE: stat.S_IWGRP,
        ModeOperationType.EXECUTE: stat.S_IXGRP,
    },
    ModeUserType.OTHER: {
        ModeOperationType.READ: stat.S_IROTH,
        ModeOperationType.WRITE: stat.S_IWOTH,
        ModeOperationType.EXECUTE: stat.S_IXOTH,
    },
}

STAT_KEYS = (
    "S_IRUSR",
    "S_IWUSR",
    "S_IXUSR",
    "S_IRGRP",
    "S_IWGRP",
    "S_IXGRP",
    "S_IROTH",
    "S_IWOTH",
    "S_IXOTH",
)

# fmt: off
W_FLDIR: Final[ModeValue] = FILE_LIST_DIRECTORY    # =                                 1
W_FADFL: Final[ModeValue] = FILE_ADD_FILE          # =                                10
W_FADSD: Final[ModeValue] = FILE_ADD_SUBDIRECTORY  # =                               100
W_FRDEA: Final[ModeValue] = FILE_READ_EA           # =                              1000
W_FWREA: Final[ModeValue] = FILE_WRITE_EA          # =                             10000
W_FTRAV: Final[ModeValue] = FILE_TRAVERSE          # =                            100000
W_FDLCH: Final[ModeValue] = FILE_DELETE_CHILD      # =                           1000000
W_FRDAT: Final[ModeValue] = FILE_READ_ATTRIBUTES   # =                          10000000
W_FWRAT: Final[ModeValue] = FILE_WRITE_ATTRIBUTES  # =                         100000000
W_DELET: Final[ModeValue] = DELETE                 # =                 10000000000000000
W_RDCON: Final[ModeValue] = READ_CONTROL           # =                100000000000000000
W_WRDAC: Final[ModeValue] = WRITE_DAC              # =               1000000000000000000
W_WROWN: Final[ModeValue] = WRITE_OWNER            # =              10000000000000000000
W_SYNCH: Final[ModeValue] = SYNCHRONIZE            # =             100000000000000000000
W_FGNEX: Final[ModeValue] = FILE_GENERIC_EXECUTE   # =             100100000000010100000
W_FGNRD: Final[ModeValue] = FILE_GENERIC_READ      # =             100100000000010001001
W_FGNWR: Final[ModeValue] = FILE_GENERIC_WRITE     # =             100100000000100010110
W_GENAL: Final[ModeValue] = GENERIC_ALL            # =     10000000000000000000000000000
W_GENEX: Final[ModeValue] = GENERIC_EXECUTE        # =    100000000000000000000000000000
W_GENWR: Final[ModeValue] = GENERIC_WRITE          # =   1000000000000000000000000000000
W_GENRD: Final[ModeValue] = GENERIC_READ           # = -10000000000000000000000000000000
# fmt: on

W_DIRRD: Final[ModeValue] = W_FLDIR | W_FRDEA | W_FRDAT | W_RDCON | W_SYNCH
W_DIRWR: Final[ModeValue] = (
    W_FADFL
    | W_FADSD
    | W_FWREA
    | W_FDLCH
    | W_FWRAT
    | W_DELET
    | W_RDCON
    | W_WRDAC
    | W_WROWN
    | W_SYNCH
)
W_DIREX: Final[ModeValue] = W_FTRAV | W_RDCON | W_SYNCH

W_FILRD: Final[ModeValue] = W_FGNRD
W_FILWR: Final[ModeValue] = W_FDLCH | W_DELET | W_WRDAC | W_WROWN | W_FGNWR
W_FILEX: Final[ModeValue] = W_FGNEX

WIN_RWX_PERMS: Final[Mapping[ModeObjectType, Mapping[ModeOperationType, ModeValue]]] = {
    ModeObjectType.FILE: {
        ModeOperationType.READ: W_FILRD,
        ModeOperationType.WRITE: W_FILWR,
        ModeOperationType.EXECUTE: W_FILEX,
    },
    ModeObjectType.DIRECTORY: {
        ModeOperationType.READ: W_DIRRD,
        ModeOperationType.WRITE: W_DIRWR,
        ModeOperationType.EXECUTE: W_DIREX,
    },
}


class PermissionGroup(Tuple[str]):
    """Permission group."""

    def __new__(cls, *args: str) -> "PermissionGroup":
        """Create new permission group."""
        return super().__new__(cls, iter(args))  # type: ignore

    def __str__(self) -> str:
        """Return string representation."""
        return ",".join(self)


WIN_FILE_PERMISSIONS: Final[PermissionGroup] = PermissionGroup(
    "DELETE",
    "READ_CONTROL",
    "WRITE_DAC",
    "WRITE_OWNER",
    "SYNCHRONIZE",
    "FILE_GENERIC_READ",
    "FILE_GENERIC_WRITE",
    "FILE_GENERIC_EXECUTE",
    "FILE_DELETE_CHILD",
)

WIN_DIR_PERMISSIONS: Final[PermissionGroup] = PermissionGroup(
    "DELETE",
    "READ_CONTROL",
    "WRITE_DAC",
    "WRITE_OWNER",
    "SYNCHRONIZE",
    "FILE_ADD_SUBDIRECTORY",
    "FILE_ADD_FILE",
    "FILE_DELETE_CHILD",
    "FILE_LIST_DIRECTORY",
    "FILE_TRAVERSE",
    "FILE_READ_ATTRIBUTES",
    "FILE_WRITE_ATTRIBUTES",
    "FILE_READ_EA",
    "FILE_WRITE_EA",
)

WIN_DIR_INHERIT_PERMISSIONS: Final[PermissionGroup] = PermissionGroup(
    "DELETE",
    "READ_CONTROL",
    "WRITE_DAC",
    "WRITE_OWNER",
    "SYNCHRONIZE",
    "GENERIC_READ",
    "GENERIC_WRITE",
    "GENERIC_EXECUTE",
    "GENERIC_ALL",
)

WIN_ACE_TYPES: Final[PermissionGroup] = PermissionGroup(
    "ACCESS_ALLOWED_ACE_TYPE",
    "ACCESS_DENIED_ACE_TYPE",
    "SYSTEM_AUDIT_ACE_TYPE",
    "SYSTEM_ALARM_ACE_TYPE",
)

WIN_INHERITANCE_TYPES: Final[PermissionGroup] = PermissionGroup(
    "OBJECT_INHERIT_ACE",
    "CONTAINER_INHERIT_ACE",
    "NO_PROPAGATE_INHERIT_ACE",
    "INHERIT_ONLY_ACE",
    "INHERITED_ACE",
    "SUCCESSFUL_ACCESS_ACE_FLAG",
    "FAILED_ACCESS_ACE_FLAG",
)

SECURITY_NT_AUTHORITY: Final[PySidValue] = ("SYSTEM", "NT AUTHORITY", 5)


def _get_mode(path: ModePathInternal) -> ModeValue:
    """Get bitwise mode (stat) of object (dir or file)."""
    if IS_WINDOWS:
        return win_get_permissions(path)
    return os.stat(path).st_mode & (stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)


def get_mode(path: ModePathInput) -> ModeValue:
    """Get bitwise mode (stat) of object (dir or file)."""
    return _get_mode(_to_path(path))


def _set_mode(path: ModePathInternal, mode: ModeInputValue) -> ModeValue:
    """Set bitwise mode (stat) of object (dir or file).

    Three types of modes can be used:
    1. Decimal mode - an integer representation of set bits (eg, 512)
    2. Octal mode - a string expressing an octal number (eg, "777")
    3. Symbolic representation - a string with modifier symbols (eg, "+x")
    """
    if isinstance(mode, int):
        new_mode = mode
    else:
        str_mode = str(mode)
        if "+" in str_mode or "-" in str_mode or "=" in str_mode:
            new_mode = get_effective_mode(_get_mode(path), str_mode)
        else:
            new_mode = int(mode, 8)

    if IS_WINDOWS:
        _win_set_permissions(path, new_mode, _get_object_type(path))
    else:
        os.chmod(path, new_mode)

    return new_mode


def set_mode(path: ModePathInput, mode: ModeInputValue) -> ModeValue:
    """Set bitwise mode (stat) of object (dir or file).

    Three types of modes can be used:
    1. Decimal mode - an integer representation of set bits (eg, 512)
    2. Octal mode - a string expressing an octal number (eg, "777")
    3. Symbolic representation - a string with modifier symbols (eg, "+x")
    """
    return _set_mode(_to_path(path), mode)


def set_mode_recursive(
    path: ModePathInput, mode: ModeInputValue, dir_mode: Optional[ModeInputValue] = None
) -> ModeValue:
    r"""Set all file and directory permissions at or under path to modes.

    Args:
    ----
    path: (:obj:`str`)
        Object which will have its mode set. If path is a file, only its mode
        is set - no recursion occurs. If path is a directory, its mode and the
        mode of all files and subdirectories below it are set.

    mode: (`int`)
        Mode to be applied to object(s).

    dir_mode: (`int`)
        If provided, this mode is given to all directories only.
    """
    _path = _to_path(path)

    if _get_object_type(_path) == ModeObjectType.FILE:
        return _set_mode(_path, mode)

    if not dir_mode:
        dir_mode = mode

    for root, dirs, files in os.walk(_path, topdown=False):
        for one_file in files:
            _set_mode(ModePathInternal(os.path.join(root, one_file)), mode)

        for one_dir in dirs:
            _set_mode(ModePathInternal(os.path.join(root, one_dir)), dir_mode)

    return _set_mode(_path, dir_mode)


def _get_effective_mode_multiple(current_mode: ModeValue, modes: ModeInputValue) -> ModeValue:
    """Get octal mode, given current mode and symbolic mode modifiers."""
    new_mode = current_mode
    for mode in str(modes).split(","):
        new_mode = get_effective_mode(new_mode, mode)
    return new_mode


def get_effective_mode(current_mode: ModeValue, symbolic: ModeInputValue) -> ModeValue:
    """Get octal mode, given current mode and symbolic mode modifier."""
    if not isinstance(symbolic, str):
        raise AttributeError("symbolic must be a string")

    if "," in symbolic:
        return _get_effective_mode_multiple(current_mode, symbolic)

    result = re.search(r"^\s*([ugoa]*)([-+=])([rwx]*)\s*$", symbolic)
    if result is None:
        raise AttributeError("bad format of symbolic representation modifier")

    whom = str(result.group(1)) or "ugo"
    operation = str(result.group(2))
    perm = str(result.group(3))

    if "a" in whom:
        whom = "ugo"

    # bitwise magic
    bit_perm = _get_basic_symbol_to_mode(perm)
    mask_mode = (
        (bit_perm << 6 if "u" in whom else 0)
        | (bit_perm << 3 if "g" in whom else 0)
        | (bit_perm << 0 if "o" in whom else 0)
    )

    if operation == "=":
        original = (
            (current_mode & 448 if "u" not in whom else 0)
            | (current_mode & 56 if "g" not in whom else 0)
            | (current_mode & 7 if "o" not in whom else 0)
        )
        return mask_mode | original

    if operation == "+":
        return current_mode | mask_mode

    return current_mode & ~mask_mode


def _get_object_type(path: ModePathInternal) -> ModeObjectType:
    """Get whether object is file or directory."""
    return ModeObjectType.FILE if os.path.isfile(path) else ModeObjectType.DIRECTORY


def get_object_type(path: ModePathInput) -> ModeObjectType:
    """Get whether object is file or directory."""
    return _get_object_type(_to_path(path))


def get_owner(path: ModePathInput) -> ModeSidObject:
    """Get the object owner."""
    if IS_WINDOWS:
        sid = _get_account_sid(SYSTEM_NAME_NONE, win_get_owner_sid(path))
    else:
        sid = getpwuid(os.stat(_to_path(path)).st_uid).pw_name
    return sid


def get_group(path: ModePathInput) -> ModeSidObject:
    """Get the object group."""
    if IS_WINDOWS:
        sid = _get_account_sid(SYSTEM_NAME_NONE, win_get_group_sid(path))
    else:
        sid = getgrgid(os.stat(_to_path(path)).st_gid).gr_name
    return sid


def win_get_owner_sid(path: ModePathInput) -> PySID:
    """Get the file owner."""
    sec_descriptor: PySECURITY_DESCRIPTOR = GetNamedSecurityInfo(
        _to_path(path),
        SE_FILE_OBJECT,
        OWNER_SECURITY_INFORMATION,
    )
    return sec_descriptor.GetSecurityDescriptorOwner()


def win_get_group_sid(path: ModePathInput) -> PySID:
    """Get the file group."""
    sec_descriptor: PySECURITY_DESCRIPTOR = GetNamedSecurityInfo(
        _to_path(path), SE_FILE_OBJECT, GROUP_SECURITY_INFORMATION
    )
    return sec_descriptor.GetSecurityDescriptorGroup()  # type: ignore


def win_get_other_sid() -> PySID:
    """Get the other SID.

    For now this is the Users builtin account. In the future, probably should
    allow account to be passed in and find any non-owner, non-group account
    currently associated with the file. As a default, it could use Users.
    """
    return ConvertStringSidToSid("S-1-5-32-545")


def convert_win_to_stat(
    win_perm: ModeValue, user_type: ModeUserType, object_type: ModeObjectType
) -> ModeValue:
    """Given Win perm and user type, give stat mode."""
    mode = 0

    for oper in ModeOperationType.values():
        if win_perm & WIN_RWX_PERMS[object_type][oper] == WIN_RWX_PERMS[object_type][oper]:
            mode = mode | STAT_MODES[user_type][oper]

    return mode


def convert_stat_to_win(
    mode: ModeValue, user_type: ModeUserType, object_type: ModeObjectType
) -> ModeValue:
    """Given stat mode, return Win bitwise permissions for user type."""
    win_perm = 0

    for oper in ModeOperationType.values():
        if mode & STAT_MODES[user_type][oper] == STAT_MODES[user_type][oper]:
            win_perm = win_perm | WIN_RWX_PERMS[object_type][oper]

    return win_perm


def win_get_user_type(sid: PySID, sids: Mapping[ModeUserType, PySID]) -> ModeUserType:
    """Given object and SIDs, return user type."""
    if sid == sids[ModeUserType.OWNER]:
        return ModeUserType.OWNER

    if sid == sids[ModeUserType.GROUP]:
        return ModeUserType.GROUP

    return ModeUserType.OTHER


def win_get_object_sids(
    path: ModePathInput,
) -> Mapping[ModeUserType, PySID]:
    """Get the owner, group, other SIDs for an object."""
    return {
        ModeUserType.OWNER: win_get_owner_sid(path),
        ModeUserType.GROUP: win_get_group_sid(path),
        ModeUserType.OTHER: win_get_other_sid(),
    }


def _to_path(path: ModePathInput) -> ModePathInternal:
    """Convert path to string."""
    absolute_resolved_path = str(pathlib.Path(str(path)).resolve().absolute())
    if not os.path.exists(absolute_resolved_path):
        raise FileNotFoundError(f"Path {path} could not be found.")
    return ModePathInternal(absolute_resolved_path)


def win_get_permissions(path: ModePathInput) -> ModeValue:
    """Get the file or dir permissions."""
    return _win_get_permissions(_to_path(path), get_object_type(path))


def _get_basic_symbol_to_mode(symbol: ModeInputValue) -> ModeValue:
    """Calculate numeric value of set of 'rwx'."""
    return (
        ("r" in str(symbol) and 1 << 2)
        | ("w" in str(symbol) and 1 << 1)
        | ("x" in str(symbol) and 1 << 0)
    )


def _win_get_permissions(path: ModePathInternal, object_type: ModeObjectType) -> ModeValue:
    """Get the permissions."""
    sec_des = GetNamedSecurityInfo(path, SE_FILE_OBJECT, DACL_SECURITY_INFORMATION)
    dacl = sec_des.GetSecurityDescriptorDacl()

    sids = win_get_object_sids(path)
    mode = 0

    for index in range(0, dacl.GetAceCount()):
        ace = dacl.GetAce(index)
        if (
            ace[0][0] == ACCESS_ALLOWED_ACE_TYPE
            and _get_account_sid(SYSTEM_NAME_NONE, ace[2]) != SECURITY_NT_AUTHORITY
        ):
            # Not handling ACCESS_DENIED_ACE_TYPE
            mode = mode | convert_win_to_stat(ace[1], win_get_user_type(ace[2], sids), object_type)

    return mode


def win_set_permissions(path: ModePathInput, mode: ModeValue) -> None:
    """Set the file or dir permissions."""
    _win_set_permissions(_to_path(path), mode, get_object_type(path))


def _win_set_permissions(
    path: ModePathInternal, mode: ModeValue, object_type: ModeObjectType
) -> None:
    """Set the permissions."""
    # Overview of Windows inheritance:
    # Get/SetNamedSecurityInfo  = Always includes inheritance
    # Get/SetFileSecurity       = Can exclude/disable inheritance
    # Here we read effective permissions with GetNamedSecurityInfo, i.e.,
    # including inherited permissions. However, we'll set permissions with
    # SetFileSecurity and NO_INHERITANCE, to disable inheritance.
    sec_des: PySECURITY_DESCRIPTOR = GetNamedSecurityInfo(
        path, SE_FILE_OBJECT, DACL_SECURITY_INFORMATION
    )
    dacl: PyACL = sec_des.GetSecurityDescriptorDacl()

    system_ace: Optional[PyACE] = None
    for _ in range(0, dacl.GetAceCount()):
        ace = dacl.GetAce(0)
        _ace, _mode, _sid = ace
        try:
            if (
                _sid
                and _sid.IsValid()
                and _get_account_sid(SYSTEM_NAME_NONE, _sid) == SECURITY_NT_AUTHORITY
            ):
                system_ace = ace
        except error:
            print("Found orphaned SID:", _sid)
        dacl.DeleteAce(0)

    if system_ace:
        dacl.AddAccessAllowedAceEx(
            dacl.GetAclRevision(),  # type: ignore[reportUnknownArgumentType]
            NO_INHERITANCE,
            system_ace[1],
            system_ace[2],
        )

    sids = win_get_object_sids(path)

    for user_type, sid in sids.items():
        win_perm = convert_stat_to_win(mode, user_type, object_type)

        if win_perm > 0:
            dacl.AddAccessAllowedAceEx(
                dacl.GetAclRevision(),  # type: ignore[reportUnknownArgumentType]
                NO_INHERITANCE,
                win_perm,
                sid,
            )

    sec_des.SetSecurityDescriptorDacl(1, dacl, 0)  # type: ignore
    SetFileSecurity(path, DACL_SECURITY_INFORMATION, sec_des)


def print_win_inheritance(flags: int) -> None:
    """Display inheritance flags."""
    print("  -Flags:", hex(flags))
    if flags == NO_INHERITANCE:
        print("    ", "NO_INHERITANCE")
    else:
        for i in WIN_INHERITANCE_TYPES:
            if flags & getattr(win32security, i) == getattr(win32security, i):
                print("    ", i)


def print_mode_permissions(mode: ModeValue) -> None:
    """Print component permissions in a stat mode."""
    print("Mode:", oct(mode), "(Decimal: " + str(mode) + ")")
    for i in STAT_KEYS:
        if mode & getattr(stat, i) == getattr(stat, i):
            print("  stat." + i)


def print_win_ace_type(ace_type: int) -> None:
    """Print ACE type."""
    print("  -Type:")
    for i in WIN_ACE_TYPES:
        if ntsecuritycon is not None and getattr(ntsecuritycon, i) == ace_type:
            print("    ", i)


def print_win_permissions(win_perm: ModeValue, flags: int, object_type: ModeObjectType) -> None:
    """Print permissions from ACE information."""
    print("  -Permissions Mask:", hex(win_perm), "(" + str(win_perm) + ")")

    # files and directories do permissions differently
    if object_type == ModeObjectType.FILE:
        permissions = WIN_FILE_PERMISSIONS
    else:
        permissions = WIN_DIR_PERMISSIONS
        # directories have ACE that is inherited by children within them
        if (
            flags & OBJECT_INHERIT_ACE == OBJECT_INHERIT_ACE
            and flags & INHERIT_ONLY_ACE == INHERIT_ONLY_ACE
        ):
            permissions = WIN_DIR_INHERIT_PERMISSIONS

    calc_mask = 0  # see if we are printing all of the permissions
    for i in permissions:
        if getattr(ntsecuritycon, i) & win_perm == getattr(ntsecuritycon, i):
            calc_mask = calc_mask | getattr(ntsecuritycon, i)
            print("    ", i)
    print("  -Mask calculated from printed permissions:", hex(calc_mask))


def print_obj_info(path: ModePathInput) -> None:
    """Print object security permission info."""
    _path = _to_path(path)

    object_type = get_object_type(_path)

    print("----------------------------------------")
    if object_type == ModeObjectType.FILE:
        print("FILE:", _path)
    else:
        print("DIRECTORY:", _path)

    print_mode_permissions(get_mode(_path))

    print("Owner:", get_owner(_path))
    print("Group:", get_group(_path))

    if IS_WINDOWS:
        _print_win_obj_info(_path)


def _print_win_obj_info(path: ModePathInternal):
    """Print windows object security info."""
    # get ACEs
    sec_descriptor = GetFileSecurity(path, DACL_SECURITY_INFORMATION)
    dacl = sec_descriptor.GetSecurityDescriptorDacl()
    if dacl is None:  # type: ignore
        print("No Discretionary ACL")
        return

    for ace_no in range(0, dacl.GetAceCount()):
        ace = dacl.GetAce(ace_no)
        print("ACE", ace_no)

        print("  -SID:", _get_account_sid(SYSTEM_NAME_NONE, ace[2]))

        print_win_ace_type(ace[0][0])
        print_win_inheritance(ace[0][1])
        print_win_permissions(ace[1], ace[0][1], get_object_type(path))


def perm_test(mode: ModeValue = stat.S_IRUSR | stat.S_IWUSR) -> None:
    """Create test file and modify permissions."""
    path = "".join(random.choice(string.ascii_letters) for _ in range(10)) + ".txt"
    with open(path, "w+", encoding="utf-8") as file_hdl:
        file_hdl.write("new file")
    print("Created test file:", path)

    print("BEFORE Permissions:")
    print_obj_info(path)

    print("Setting permissions:")
    print_mode_permissions(mode)
    set_mode(path, mode)

    print("AFTER Permissions:")
    print_obj_info(path)
