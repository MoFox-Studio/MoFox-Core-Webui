"""WebUI 启动地址事件处理器。

在系统 ON_START 事件触发后，读取 HTTPServer 的运行时监听地址，
并构建可访问 WebUI 的 URL 列表输出到日志。
"""

from __future__ import annotations

import ipaddress
import socket
from typing import Any

from src.core.components.base.event_handler import BaseEventHandler
from src.core.components.types import EventType
from src.core.transport.router.http_server import get_http_server
from src.kernel.event import EventDecision
from src.kernel.logger import get_logger

logger = get_logger("startup_url_event_handler", display="WebUI启动地址")


class StartupUrlEventHandler(BaseEventHandler):
    """在系统启动后输出 WebUI 可访问 URL 列表。"""

    handler_name = "startup_url_event_handler"
    handler_description = "系统启动后发现并输出 WebUI 可访问 URL"
    weight = 0
    intercept_message = False
    init_subscribe = [EventType.ON_START]

    async def execute(
        self, event_name: str, params: dict[str, Any]
    ) -> tuple["EventDecision", dict[str, Any]]:
        """处理 ON_START 事件并记录可访问 URL。

        Args:
            event_name: 事件名。
            params: 事件参数。

        Returns:
            tuple[EventDecision, dict[str, Any]]: 事件决策与透传参数。
        """
        try:
            server = get_http_server()
            host = str(server.host).strip()
            port = int(server.port)

            urls = self._build_webui_urls(host=host, port=port)
            if not urls:
                logger.warning(
                    f"ON_START 触发后未发现可访问 WebUI 地址，host={host}, port={port}"
                )
                return EventDecision.PASS, params

            # 分类并输出友好的访问提示
            self._log_accessible_urls(urls, host, port)

            return EventDecision.SUCCESS, params
        except Exception as exc:
            logger.warning(f"构建 WebUI 可访问地址失败: {exc}")
            return EventDecision.PASS, params

    def _build_webui_urls(self, host: str, port: int) -> list[str]:
        """根据监听地址生成 WebUI URL 列表。"""
        address_candidates = self._resolve_accessible_hosts(host)
        urls: list[str] = []
        for candidate in address_candidates:
            host_with_brackets = self._format_host_for_url(candidate)
            urls.append(f"http://{host_with_brackets}:{port}/webui/frontend")
        return self._deduplicate(urls)

    def _log_accessible_urls(self, urls: list[str], host: str, port: int) -> None:
        """以用户友好的方式输出可访问 URL 列表。"""
        # 分类 URL
        local_urls: list[str] = []
        lan_urls: list[str] = []

        for url in urls:
            # 提取主机部分进行分类
            if "localhost" in url or "127.0.0.1" in url or "[::1]" in url:
                local_urls.append(url)
            else:
                lan_urls.append(url)

        # 构建面板内容
        content_lines: list[str] = []
        content_lines.append(f"[dim]监听地址:[/dim] [cyan]{host}:{port}[/cyan]\n")

        # 输出本机访问地址
        if local_urls:
            content_lines.append("[bold yellow]🖥️  本机访问[/bold yellow]")
            content_lines.append("[dim]在本机浏览器中打开以下任一地址:[/dim]")
            for url in local_urls:
                content_lines.append(f"  [green]▶[/green] [link={url}]{url}[/link]")
            content_lines.append("")

        # 输出局域网访问地址并高亮推荐
        if lan_urls:
            content_lines.append("[bold cyan]🌐 局域网访问[/bold cyan]")
            content_lines.append("[dim]在同一局域网的其他设备浏览器中打开:[/dim]")
            for idx, url in enumerate(lan_urls):
                # 优先推荐第一个局域网私有地址（通常是主网卡地址）
                if idx == 0 and self._is_private_ip_url(url):
                    content_lines.append(
                        f"  [green]★[/green] [link={url}]{url}[/link] [bold green]← 推荐[/bold green]"
                    )
                else:
                    content_lines.append(f"  [green]▶[/green] [link={url}]{url}[/link]")
            content_lines.append("")

        # 添加提示信息
        content_lines.append("[dim italic]💡 提示: 如需远程访问，请配置反向代理或使用内网穿透[/dim italic]")

        # 使用 logger.print_panel 输出美观的面板
        logger.print_panel(
            "\n".join(content_lines),
            title="[bold white]✨ WebUI 服务已启动[/bold white]",
            border_style="green",
        )

    def _is_private_ip_url(self, url: str) -> bool:
        """判断 URL 是否包含局域网私有 IP 地址。"""
        try:
            # 提取 host 部分（去掉 http:// 和端口）
            host_part = url.split("://")[1].split(":")[0].split("/")[0]
            # 去掉 IPv6 的方括号
            host_part = host_part.strip("[]")
            ip = ipaddress.ip_address(host_part)
            return ip.is_private
        except (ValueError, IndexError):
            return False

    def _resolve_accessible_hosts(self, host: str) -> list[str]:
        """解析可访问地址列表。

        - 监听在 loopback 时仅返回本地地址。
        - 监听在 wildcard 时返回本机可发现地址集合。
        - 其他情况返回指定 host。
        """
        normalized = host.lower()
        if normalized in {"127.0.0.1", "localhost", "::1"}:
            if normalized == "::1":
                return ["::1"]
            return ["localhost", "127.0.0.1"]

        if normalized in {"0.0.0.0", "::"}:
            addresses = ["localhost", "127.0.0.1", "::1"]
            addresses.extend(self._discover_local_ip_addresses())
            return self._sort_addresses(self._deduplicate(addresses))

        return [host]

    def _discover_local_ip_addresses(self) -> list[str]:
        """发现本机可用 IP 地址。"""
        found: list[str] = []

        # 基于主机名解析
        try:
            _, _, ipv4_list = socket.gethostbyname_ex(socket.gethostname())
            found.extend(ipv4_list)
        except Exception:
            pass

        # getaddrinfo 能覆盖更多网卡与 IPv6 情况
        try:
            infos = socket.getaddrinfo(socket.gethostname(), None, socket.AF_UNSPEC)
            for info in infos:
                sockaddr = info[4]
                if not sockaddr or not isinstance(sockaddr[0], str):
                    continue
                found.append(sockaddr[0])
        except Exception:
            pass

        # 出站探测常用于获取系统实际对外首选地址
        ipv4_probe = self._probe_local_address("8.8.8.8", 80, socket.AF_INET)
        if ipv4_probe:
            found.append(ipv4_probe)

        ipv6_probe = self._probe_local_address(
            "2001:4860:4860::8888", 80, socket.AF_INET6
        )
        if ipv6_probe:
            found.append(ipv6_probe)

        return self._filter_valid_addresses(found)

    def _probe_local_address(self, target: str, port: int, family: int) -> str | None:
        """通过 UDP connect 探测本机首选出站地址。"""
        sock: socket.socket | None = None
        try:
            sock = socket.socket(family, socket.SOCK_DGRAM)
            sock.connect((target, port))
            local = sock.getsockname()[0]
            return str(local)
        except Exception:
            return None
        finally:
            if sock is not None:
                try:
                    sock.close()
                except Exception:
                    pass

    def _filter_valid_addresses(self, addresses: list[str]) -> list[str]:
        """过滤不可用与噪声地址。"""
        valid: list[str] = []
        for raw in addresses:
            candidate = str(raw).strip()
            if not candidate:
                continue
            if candidate in {"0.0.0.0", "::"}:
                continue
            try:
                ip = ipaddress.ip_address(candidate)
            except ValueError:
                continue

            # 过滤常见链路本地噪声地址
            if ip.version == 4 and candidate.startswith("169.254."):
                continue
            if ip.version == 6 and candidate.lower().startswith("fe80:"):
                continue

            valid.append(candidate)
        return self._deduplicate(valid)

    def _sort_addresses(self, addresses: list[str]) -> list[str]:
        """为日志输出提供稳定、可读的排序。"""

        def sort_key(addr: str) -> tuple[int, int, str]:
            if addr == "localhost":
                return (0, 0, addr)
            try:
                ip = ipaddress.ip_address(addr)
            except ValueError:
                return (3, 0, addr)

            if ip.is_loopback:
                return (0, 1, addr)
            if ip.is_private:
                return (1, 0, addr)
            return (2, 0, addr)

        return sorted(addresses, key=sort_key)

    def _format_host_for_url(self, host: str) -> str:
        """将 host 转换为 URL 可用格式（IPv6 需方括号）。"""
        try:
            ip = ipaddress.ip_address(host)
        except ValueError:
            return host

        if ip.version == 6:
            return f"[{host}]"
        return host

    def _deduplicate(self, values: list[str]) -> list[str]:
        """按原顺序去重。"""
        return list(dict.fromkeys(values))
