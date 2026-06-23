"""自定义异常和错误码"""

from enum import Enum
from typing import Optional


class ErrorCode(Enum):
    """错误码枚举"""
    
    SUCCESS = (0, "ok")
    
    # 通用错误
    PARAMS_ERROR = (40000, "请求参数错误")
    NOT_LOGIN_ERROR = (40100, "未登录")
    NO_AUTH_ERROR = (40101, "无权限")
    NOT_FOUND_ERROR = (40400, "请求数据不存在")
    FORBIDDEN_ERROR = (40300, "禁止访问")
    SYSTEM_ERROR = (50000, "系统内部异常")
    OPERATION_ERROR = (50001, "操作失败")
    
    # 业务错误
    USER_NOT_EXIST = (40401, "用户不存在")
    USER_ALREADY_EXIST = (40402, "用户已存在")
    PASSWORD_ERROR = (40103, "密码错误")
    
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message


class BusinessException(Exception):
    """业务异常"""
    
    def __init__(
        self,
        error_code: ErrorCode,
        message: Optional[str] = None,
        status_code: Optional[int] = None,
    ):
        self.error_code = error_code
        self.message = message or error_code.message
        self.status_code = status_code or _default_http_status(error_code)
        super().__init__(self.message)


def _default_http_status(error_code: ErrorCode) -> int:
    """将业务错误码映射到 HTTP 状态码。"""
    mapping = {
        ErrorCode.PARAMS_ERROR: 400,
        ErrorCode.NOT_LOGIN_ERROR: 401,
        ErrorCode.NO_AUTH_ERROR: 403,
        ErrorCode.NOT_FOUND_ERROR: 404,
        ErrorCode.FORBIDDEN_ERROR: 403,
        ErrorCode.SYSTEM_ERROR: 500,
        ErrorCode.OPERATION_ERROR: 409,
        ErrorCode.USER_NOT_EXIST: 404,
        ErrorCode.USER_ALREADY_EXIST: 409,
        ErrorCode.PASSWORD_ERROR: 401,
    }
    return mapping.get(error_code, 400)


def throw_if(condition: bool, error_code: ErrorCode, message: Optional[str] = None):
    """条件为真时抛出异常"""
    if condition:
        raise BusinessException(error_code, message)


def throw_if_not(condition: bool, error_code: ErrorCode, message: Optional[str] = None):
    """条件为假时抛出异常"""
    if not condition:
        raise BusinessException(error_code, message)
