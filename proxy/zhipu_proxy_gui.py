# -*- coding: utf-8 -*-
"""Small GUI launcher for the DST Zhipu local proxy."""

from __future__ import annotations

import errno
import json
import os
import platform
import queue
import threading
import tkinter as tk
import urllib.error
import urllib.request
from tkinter import messagebox, scrolledtext, ttk
from typing import Callable

import zhipu_dst_proxy as proxy


HOST = proxy.DEFAULT_HOST
PORT = proxy.DEFAULT_PORT
MODEL = proxy.DEFAULT_MODEL
HEALTH_URL = f"http://{HOST}:{PORT}/health?debug=1"
APP_TITLE = "DST 智谱本地代理"


class ProxyGui:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.server = None
        self.server_thread: threading.Thread | None = None
        self.closed = False
        self.log_queue: queue.Queue[str] = queue.Queue()
        self.ui_queue: queue.Queue[Callable[[], None]] = queue.Queue()

        self.api_key_var = tk.StringVar()
        self.show_key_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="未启动")

        self.root.title(APP_TITLE)
        if platform.system() == "Darwin":
            try:
                self.root.createcommand("tk::mac::Quit", self.close_app)
            except tk.TclError:
                pass
        self.root.geometry("720x520")
        self.root.minsize(640, 460)
        self.root.protocol("WM_DELETE_WINDOW", self.close_app)

        self.build_ui()
        self.set_stopped_state()
        self.root.after(100, self.drain_queues)

    def build_ui(self) -> None:
        main = ttk.Frame(self.root, padding=14)
        main.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(6, weight=1)

        ttk.Label(main, text="智谱 API Key").grid(row=0, column=0, sticky="w", pady=(0, 8))
        self.key_entry = ttk.Entry(main, textvariable=self.api_key_var, show="*")
        self.key_entry.grid(row=0, column=1, sticky="ew", pady=(0, 8))
        self.show_key_check = ttk.Checkbutton(
            main,
            text="显示",
            variable=self.show_key_var,
            command=self.toggle_key_visibility,
        )
        self.show_key_check.grid(row=0, column=2, padx=(8, 0), pady=(0, 8))

        ttk.Label(main, text="模型").grid(row=1, column=0, sticky="w", pady=(0, 8))
        self.model_entry = ttk.Entry(main)
        self.model_entry.grid(row=1, column=1, sticky="ew", pady=(0, 8))
        self.model_entry.insert(0, MODEL)
        self.model_entry.configure(state="readonly")

        ttk.Label(main, text="代理地址").grid(row=2, column=0, sticky="w", pady=(0, 8))
        self.address_entry = ttk.Entry(main)
        self.address_entry.grid(row=2, column=1, sticky="ew", pady=(0, 8))
        self.address_entry.insert(0, f"http://{HOST}:{PORT}")
        self.address_entry.configure(state="readonly")

        ttk.Label(main, text="状态").grid(row=3, column=0, sticky="w", pady=(0, 10))
        ttk.Label(main, textvariable=self.status_var).grid(row=3, column=1, sticky="w", pady=(0, 10))

        button_row = ttk.Frame(main)
        button_row.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        self.start_button = ttk.Button(button_row, text="启动代理", command=self.start_proxy)
        self.start_button.pack(side="left")
        self.stop_button = ttk.Button(button_row, text="停止代理", command=self.stop_proxy)
        self.stop_button.pack(side="left", padx=(8, 0))
        self.test_button = ttk.Button(button_row, text="测试连接", command=self.test_connection)
        self.test_button.pack(side="left", padx=(8, 0))
        ttk.Button(button_row, text="清空日志", command=self.clear_logs).pack(side="left", padx=(8, 0))

        ttk.Label(main, text="日志").grid(row=5, column=0, sticky="w")
        self.log_text = scrolledtext.ScrolledText(main, height=14, wrap="word", state="disabled")
        self.log_text.grid(row=6, column=0, columnspan=3, sticky="nsew")

    def toggle_key_visibility(self) -> None:
        self.key_entry.configure(show="" if self.show_key_var.get() else "*")

    def set_status(self, value: str) -> None:
        self.status_var.set(value)

    def set_running_state(self) -> None:
        self.key_entry.configure(state="disabled")
        self.show_key_check.configure(state="disabled")
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.test_button.configure(state="normal")

    def set_stopped_state(self) -> None:
        self.key_entry.configure(state="normal")
        self.show_key_check.configure(state="normal")
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.test_button.configure(state="disabled")

    def append_log(self, message: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def thread_log(self, message: str) -> None:
        self.log_queue.put(message)

    def call_on_ui(self, callback: Callable[[], None]) -> None:
        self.ui_queue.put(callback)

    def drain_queues(self) -> None:
        while True:
            try:
                message = self.log_queue.get_nowait()
            except queue.Empty:
                break
            self.append_log(message)

        while True:
            try:
                callback = self.ui_queue.get_nowait()
            except queue.Empty:
                break
            callback()

        if not self.closed:
            self.root.after(100, self.drain_queues)

    def clear_logs(self) -> None:
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def start_proxy(self) -> None:
        api_key = self.api_key_var.get().strip()
        if not api_key:
            self.set_status("缺少 API Key")
            self.append_log("启动失败：请输入智谱 API Key。")
            messagebox.showwarning("缺少 API Key", "请输入智谱 API Key 后再启动代理。")
            return

        if self.server is not None:
            self.append_log("代理已经在运行。")
            return

        os.environ["ZHIPU_API_KEY"] = api_key
        os.environ.pop("ZHIPU_MODEL", None)
        os.environ.pop("DST_AI_ZHIPU_MODEL", None)

        try:
            self.server = proxy.create_server(HOST, PORT)
        except OSError as exc:
            os.environ.pop("ZHIPU_API_KEY", None)
            message = self.format_start_error(exc)
            self.set_status("启动失败")
            self.append_log(message)
            messagebox.showerror("启动失败", message)
            return

        self.server_thread = threading.Thread(target=self.serve_forever, name="DST-Zhipu-Proxy", daemon=True)
        self.server_thread.start()
        self.set_status(f"运行中：{HOST}:{PORT}")
        self.set_running_state()
        self.append_log(f"代理已启动：{HEALTH_URL}")
        self.append_log(f"模型固定为：{MODEL}")

    def serve_forever(self) -> None:
        server = self.server
        if server is None:
            return

        try:
            server.serve_forever(poll_interval=0.2)
        except Exception as exc:
            self.thread_log(f"代理异常停止：{type(exc).__name__}: {exc}")
            if not self.closed:
                self.call_on_ui(self.handle_server_crash)

    def handle_server_crash(self) -> None:
        if self.server is not None:
            try:
                self.server.server_close()
            finally:
                self.server = None
        self.server_thread = None
        os.environ.pop("ZHIPU_API_KEY", None)
        self.set_status("已停止")
        self.set_stopped_state()

    def stop_proxy(self) -> None:
        if self.server is None:
            self.append_log("代理没有运行。")
            self.set_status("未启动")
            return

        server = self.server
        thread = self.server_thread
        self.stop_button.configure(state="disabled")
        self.set_status("正在停止...")

        try:
            server.shutdown()
        finally:
            server.server_close()
            if thread is not None and thread.is_alive():
                thread.join(timeout=2)
            self.server = None
            self.server_thread = None
            os.environ.pop("ZHIPU_API_KEY", None)

        self.set_status("已停止")
        self.set_stopped_state()
        self.append_log("代理已停止，API Key 已从当前进程清除。")

    def test_connection(self) -> None:
        if self.server is None:
            self.append_log("请先启动代理，再测试连接。")
            return

        self.test_button.configure(state="disabled")
        self.set_status("正在测试连接...")
        threading.Thread(target=self.test_connection_worker, name="DST-Zhipu-Proxy-Test", daemon=True).start()

    def test_connection_worker(self) -> None:
        try:
            with urllib.request.urlopen(HEALTH_URL, timeout=3) as response:
                payload = json.loads(response.read().decode("utf-8"))
            api_key_status = "已加载" if payload.get("has_api_key") else "未加载"
            message = f"测试成功：模型 {payload.get('model')}，API Key {api_key_status}。"
            self.call_on_ui(lambda: self.finish_test(message, True))
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            message = f"测试失败：{type(exc).__name__}: {exc}"
            self.call_on_ui(lambda: self.finish_test(message, False))

    def finish_test(self, message: str, ok: bool) -> None:
        if self.closed:
            return
        self.append_log(message)
        self.set_status("运行中" if ok else "测试失败")
        if self.server is not None:
            self.test_button.configure(state="normal")

    def format_start_error(self, exc: OSError) -> str:
        winerror = getattr(exc, "winerror", None)
        if winerror == 10048 or exc.errno == errno.EADDRINUSE:
            return f"启动失败：端口 {PORT} 已被占用。请先关闭旧代理或占用该端口的软件。"
        return f"启动失败：{type(exc).__name__}: {exc}"

    def close_app(self) -> None:
        self.closed = True
        if self.server is not None:
            self.stop_proxy()
        self.api_key_var.set("")
        os.environ.pop("ZHIPU_API_KEY", None)
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    ProxyGui(root)
    root.mainloop()


if __name__ == "__main__":
    main()
