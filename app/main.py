"""
HR 工具箱 - 应用入口
"""
import sys
import ctypes
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from qfluentwidgets import setTheme, Theme

from app.view.main_window import MainWindow
from app.common.logger import logger


# 单实例标识
LOCAL_SERVER_NAME = "hr-tools-single-instance-server"
MUTEX_NAME = "Global\\hr-tools-single-instance-mutex"


def create_mutex():
    """创建 Windows 互斥体"""
    try:
        # 尝试创建命名互斥体
        # ERROR_ALREADY_EXISTS = 183
        mutex = ctypes.windll.kernel32.CreateMutexW(None, False, MUTEX_NAME)
        last_error = ctypes.windll.kernel32.GetLastError()
        if last_error == 183:  # ERROR_ALREADY_EXISTS
            return None
        return mutex
    except Exception as e:
        logger.warning(f"创建互斥体失败: {e}")
        return -1  # 返回 -1 表示不支持，允许启动


def release_mutex(mutex):
    """释放互斥体"""
    if mutex and mutex != -1:
        try:
            ctypes.windll.kernel32.ReleaseMutex(mutex)
            ctypes.windll.kernel32.CloseHandle(mutex)
        except Exception:
            pass


class SingleApplication(QApplication):
    """单实例应用程序"""

    def __init__(self, argv):
        super().__init__(argv)
        self._local_server = None
        self._main_window = None
        self._mutex = None

    def set_mutex(self, mutex):
        """设置互斥体"""
        self._mutex = mutex

    def start_server(self, main_window):
        """启动本地服务器，用于接收其他实例的激活请求"""
        self._main_window = main_window
        self._local_server = QLocalServer()
        self._local_server.newConnection.connect(self._on_new_connection)

        # 移除可能残留的服务器文件
        QLocalServer.removeServer(LOCAL_SERVER_NAME)

        if not self._local_server.listen(LOCAL_SERVER_NAME):
            logger.warning(f"本地服务器启动失败: {self._local_server.errorString()}")
            return False

        logger.info("单实例服务器已启动")
        return True

    def _on_new_connection(self):
        """处理新连接（其他实例请求激活）"""
        socket = self._local_server.nextPendingConnection()
        if socket:
            socket.waitForReadyRead(1000)
            data = socket.readAll().data()
            socket.disconnectFromServer()

            logger.info("收到激活请求，显示主窗口")
            if self._main_window:
                self._main_window.show()
                self._main_window.activateWindow()
                self._main_window.raise_()

    def notify_running_instance(self):
        """通知已运行的实例激活窗口"""
        socket = QLocalSocket()
        socket.connectToServer(LOCAL_SERVER_NAME)

        if socket.waitForConnected(1000):
            socket.write(b"activate")
            socket.flush()
            socket.waitForBytesWritten(1000)
            socket.disconnectFromServer()
            logger.info("已通知运行的实例激活窗口")
            return True
        return False

    def cleanup(self):
        """清理资源"""
        if self._local_server:
            self._local_server.close()
        if self._mutex:
            release_mutex(self._mutex)


def main():
    """应用程序入口"""
    logger.info("HR 工具箱启动...")

    # 单实例检测（使用 Windows Mutex）
    mutex = create_mutex()
    if mutex is None:
        # 已有实例在运行
        logger.warning("应用已在运行，尝试激活已存在的窗口")

        # 尝试通知已有实例
        app = QApplication(sys.argv)
        socket = QLocalSocket()
        socket.connectToServer(LOCAL_SERVER_NAME)

        if socket.waitForConnected(1000):
            socket.write(b"activate")
            socket.flush()
            socket.waitForBytesWritten(1000)
            socket.disconnectFromServer()
            print("HR 工具箱已在运行，已激活已存在的窗口")
        else:
            print("HR 工具箱已在运行，请切换到已打开的窗口")

        return 0

    app = SingleApplication(sys.argv)
    app.set_mutex(mutex)

    # 设置主题
    setTheme(Theme.LIGHT)
    logger.info("主题设置完成: LIGHT")

    # 创建主窗口
    window = MainWindow()
    window.show()
    logger.info("主窗口已显示")

    # 启动本地服务器
    app.start_server(window)

    result = app.exec()

    # 清理
    app.cleanup()

    return result


if __name__ == "__main__":
    sys.exit(main())