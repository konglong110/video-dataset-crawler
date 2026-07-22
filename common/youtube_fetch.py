"""
yt-dlp 统一封装：所有数据集脚本下载 YouTube 视频都走这个函数，
不要各自 subprocess 调 yt-dlp，参数/代理/超时不统一后面很难排查问题。
"""
import subprocess

from config import HTTP_PROXY, YTDLP_FORMAT, REQUEST_TIMEOUT_SEC


def download_youtube(url: str, out_path: str, start: str = None, end: str = None) -> tuple[bool, str]:
    """
    下载单个 YouTube 视频（可选按时间戳截取片段，用于类似 HD-VILA-100M
    这种"给整段视频 + clip 时间戳"的数据集）。

    返回 (是否成功, 错误信息或空字符串)。
    """
    cmd = ["yt-dlp", "-f", YTDLP_FORMAT, "-o", out_path, "--no-progress"]

    if HTTP_PROXY:
        cmd += ["--proxy", HTTP_PROXY]

    if start and end:
        # 用 --download-sections 只下载需要的片段，省流量，比整段下完再剪快很多
        cmd += ["--download-sections", f"*{start}-{end}"]

    cmd.append(url)

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=REQUEST_TIMEOUT_SEC * 10
        )
        if result.returncode != 0:
            return False, result.stderr[-2000:]  # 只保留末尾,避免日志过长
        return True, ""
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except FileNotFoundError:
        return False, "yt-dlp 未安装，先 pip install yt-dlp"
