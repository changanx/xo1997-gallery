"""
执行命令工具
"""
import subprocess
import sys
import shlex
import platform
from langchain_core.tools import tool
from .base import SecurityContext
from app.common.logger import get_logger

logger = get_logger()


def create_execute_tools(security: SecurityContext):
    """创建执行命令工具"""

    # 安全命令白名单 (命令名 -> 允许的参数)
    # Windows 和 Unix 命令分开处理
    is_windows = platform.system() == "Windows"

    SAFE_COMMAND_WHITELIST = {
        # 通用命令
        "echo": {"allowed_args": [], "safe_mode": True},  # 仅允许简单输出
        "pwd": {"allowed_args": []},
        "whoami": {"allowed_args": []},
        "date": {"allowed_args": []},
        "time": {"allowed_args": []},
    }

    if is_windows:
        # Windows 特定命令
        SAFE_COMMAND_WHITELIST.update({
            "dir": {"allowed_args": []},
            "type": {"allowed_args": [], "file_in_workdir": True},  # 查看文件内容
            "cd": {"allowed_args": []},
            "tree": {"allowed_args": ["/F", "/A"]},
            "find": {"allowed_args": []},
            "where": {"allowed_args": []},
        })
    else:
        # Unix/Linux 特定命令
        SAFE_COMMAND_WHITELIST.update({
            "ls": {"allowed_args": ["-l", "-a", "-h", "-la", "-lah", "-lh"]},
            "cat": {"allowed_args": [], "file_in_workdir": True},
            "head": {"allowed_args": ["-n"], "file_in_workdir": True},
            "tail": {"allowed_args": ["-n", "-f"], "file_in_workdir": True},
            "pwd": {"allowed_args": []},
            "which": {"allowed_args": []},
            "tree": {"allowed_args": ["-L", "-a"]},
            "find": {"allowed_args": ["-name", "-type", "-maxdepth"]},
        })

    def is_safe_command(command: str) -> tuple[bool, str, list]:
        """
        检查命令是否安全（白名单模式）

        Returns:
            (是否安全, 错误信息, 解析后的参数列表)
        """
        try:
            parts = shlex.split(command)
        except ValueError as e:
            return False, f"命令解析失败: {str(e)}", []

        if not parts:
            return False, "空命令", []

        cmd_name = parts[0].lower()

        # 检查白名单
        if cmd_name not in SAFE_COMMAND_WHITELIST:
            allowed = ", ".join(sorted(SAFE_COMMAND_WHITELIST.keys()))
            return False, f"命令 '{cmd_name}' 不在允许列表中。\n允许的命令: {allowed}", []

        cmd_config = SAFE_COMMAND_WHITELIST[cmd_name]
        allowed_args = cmd_config.get("allowed_args", [])

        # 验证参数
        args = parts[1:] if len(parts) > 1 else []
        validated_args = []

        i = 0
        while i < len(args):
            arg = args[i]

            # 检查是否是允许的参数
            if arg.startswith("-"):
                # 对于带值的参数（如 -n 10）
                if arg in ["-n", "-L", "-maxdepth", "-name", "-type"]:
                    if arg in allowed_args:
                        validated_args.append(arg)
                        if i + 1 < len(args) and not args[i + 1].startswith("-"):
                            validated_args.append(args[i + 1])
                            i += 1
                    else:
                        return False, f"参数 '{arg}' 不被允许", []
                elif arg in allowed_args:
                    validated_args.append(arg)
                else:
                    return False, f"参数 '{arg}' 不被允许", []
            else:
                # 非参数（可能是文件路径）
                if cmd_config.get("file_in_workdir"):
                    # 验证文件在工作目录内
                    from pathlib import Path
                    file_path = security.safe_join(arg)
                    if not security.is_safe_path(file_path):
                        return False, f"文件路径不在工作目录内: {arg}", []
                    validated_args.append(arg)
                elif cmd_config.get("safe_mode"):
                    # safe_mode 下只允许简单的非参数值
                    if not any(c in arg for c in ['|', '&', ';', '$', '`', '>', '<', '\n']):
                        validated_args.append(arg)
                    else:
                        return False, f"参数包含不安全字符: {arg}", []
                else:
                    validated_args.append(arg)

            i += 1

        logger.info("命令验证通过", extra={"command": cmd_name, "args": validated_args})
        return True, "", [cmd_name] + validated_args

    @tool
    def run_python(file_path: str, args: str = "") -> str:
        """运行 Python 文件。路径相对于工作目录。

        Args:
            file_path: 相对于工作目录的 Python 文件路径
            args: 传递给脚本的命令行参数 (可选)

        Returns:
            执行输出或错误信息
        """
        full_path = security.safe_join(file_path)
        is_safe, error_msg = security.validate_path(full_path)
        if not is_safe:
            return error_msg

        try:
            if not full_path.exists():
                return f"错误: 文件不存在 - {file_path}"
            if not full_path.suffix.lower() == '.py':
                return f"警告: 文件可能不是 Python 脚本 - {file_path}"

            cmd = [sys.executable, str(full_path)]
            if args:
                cmd.extend(args.split())

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(security.work_directory)
            )

            output_lines = []
            if result.stdout:
                output_lines.append(f"[输出]\n{result.stdout}")
            if result.stderr:
                output_lines.append(f"[错误输出]\n{result.stderr}")
            if result.returncode != 0:
                output_lines.append(f"[退出码: {result.returncode}]")

            return "\n".join(output_lines) if output_lines else "程序执行完成，无输出"
        except subprocess.TimeoutExpired:
            return "错误: 程序执行超时 (60秒限制)"
        except PermissionError:
            return f"错误: 没有权限执行文件 - {file_path}"
        except Exception as e:
            return f"执行失败: {str(e)}"

    @tool
    def run_command(command: str, timeout: int = 30) -> str:
        """在终端中运行命令。命令将在工作目录中执行。

        注意：为安全起见，只允许执行白名单中的命令。
        允许的命令包括：ls/dir, cat/type, pwd, echo, head, tail, tree, find, whoami, date, time, which/where

        Args:
            command: 要执行的命令（必须是白名单中的命令）
            timeout: 超时时间（秒），默认 30 秒

        Returns:
            命令输出或错误信息
        """
        # 白名单安全检查
        is_safe, error_msg, cmd_parts = is_safe_command(command)
        if not is_safe:
            return f"错误: {error_msg}"

        # 限制超时时间
        timeout = min(timeout, 60)

        try:
            # 不使用 shell=True，直接传递参数列表
            result = subprocess.run(
                cmd_parts,
                shell=False,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(security.work_directory)
            )

            output_lines = []
            if result.stdout:
                output_lines.append(f"[输出]\n{result.stdout}")
            if result.stderr:
                output_lines.append(f"[错误输出]\n{result.stderr}")
            if result.returncode != 0:
                output_lines.append(f"[退出码: {result.returncode}]")

            return "\n".join(output_lines) if output_lines else "命令执行完成，无输出"
        except subprocess.TimeoutExpired:
            return f"错误: 命令执行超时 ({timeout}秒限制)"
        except FileNotFoundError:
            return f"错误: 命令 '{cmd_parts[0]}' 未找到"
        except PermissionError:
            return f"错误: 没有权限执行命令"
        except Exception as e:
            return f"执行失败: {str(e)}"

    @tool
    def run_git_command(args: str) -> str:
        """执行 Git 命令。在工作目录中执行 git 操作。

        Args:
            args: git 命令参数，例如 "status" 或 "add ."

        Returns:
            命令输出
        """
        # 检查是否是危险操作
        dangerous_git = ["push --force", "reset --hard", "clean -fd", "checkout --"]
        for danger in dangerous_git:
            if danger in args.lower():
                return f"警告: 命令包含潜在危险操作 '{danger}'，请谨慎使用"

        try:
            result = subprocess.run(
                ["git"] + args.split(),
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(security.work_directory)
            )

            output_lines = []
            if result.stdout:
                output_lines.append(result.stdout)
            if result.stderr:
                output_lines.append(f"[Git 信息]\n{result.stderr}")

            return "\n".join(output_lines) if output_lines else "Git 命令执行完成"
        except subprocess.TimeoutExpired:
            return "错误: Git 命令执行超时"
        except FileNotFoundError:
            return "错误: 未找到 git 命令，请确保已安装 Git"
        except Exception as e:
            return f"执行 Git 命令失败: {str(e)}"

    @tool
    def run_npm_command(args: str) -> str:
        """执行 npm 命令。在工作目录中执行 Node.js 包管理操作。

        Args:
            args: npm 命令参数，例如 "install" 或 "run build"

        Returns:
            命令输出
        """
        try:
            result = subprocess.run(
                ["npm"] + args.split(),
                capture_output=True,
                text=True,
                timeout=120,  # npm 操作可能较慢
                cwd=str(security.work_directory)
            )

            output_lines = []
            if result.stdout:
                output_lines.append(result.stdout)
            if result.stderr:
                output_lines.append(f"[npm 信息]\n{result.stderr}")

            return "\n".join(output_lines) if output_lines else "npm 命令执行完成"
        except subprocess.TimeoutExpired:
            return "错误: npm 命令执行超时 (120秒限制)"
        except FileNotFoundError:
            return "错误: 未找到 npm 命令，请确保已安装 Node.js"
        except Exception as e:
            return f"执行 npm 命令失败: {str(e)}"

    return [run_python, run_command, run_git_command, run_npm_command]
