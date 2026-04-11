"""
执行命令工具
"""
import subprocess
import sys
from langchain_core.tools import tool
from .base import SecurityContext


def create_execute_tools(security: SecurityContext):
    """创建执行命令工具"""

    # 危险命令黑名单
    DANGEROUS_PATTERNS = [
        "rm -rf",
        "del /",
        "format",
        "shutdown",
        "reboot",
        "mkfs",
        "dd if=",
        "> /dev/",
        "chmod 777",
        "chown root",
        "sudo rm",
        "sudo apt",
        "apt-get",
        "yum install",
        "pip install",
        "npm install -g",
    ]

    def is_dangerous_command(command: str) -> tuple[bool, str]:
        """检查命令是否危险"""
        cmd_lower = command.lower()
        for pattern in DANGEROUS_PATTERNS:
            if pattern.lower() in cmd_lower:
                return True, f"检测到危险命令模式: {pattern}"
        return False, ""

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

        Args:
            command: 要执行的命令
            timeout: 超时时间（秒），默认 30 秒

        Returns:
            命令输出或错误信息
        """
        # 安全检查
        is_dangerous, reason = is_dangerous_command(command)
        if is_dangerous:
            return f"错误: {reason}\n不允许执行可能破坏系统的命令"

        # 限制超时时间
        timeout = min(timeout, 60)

        try:
            result = subprocess.run(
                command,
                shell=True,
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
