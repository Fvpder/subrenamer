import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter import ttk
from pathlib import Path


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    if hasattr(sys, "_MEIPASS"):
        # Use getattr to avoid static analysis errors for PyInstaller's dynamic attribute
        return os.path.join(getattr(sys, "_MEIPASS"), relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def sync_subtitle_names(video_root, sub_root, dry_run=True, log_callback=print):
    """
    根据视频文件名批量重命名字幕文件。
    采用按名称排序后的顺序进行一一对应。
    """
    video_root = Path(video_root)
    sub_root = Path(sub_root)

    # 常见的视频和字幕扩展名
    video_exts = {".mp4", ".mkv", ".avi", ".ts"}
    sub_exts = {".srt", ".ass", ".ssa", ".sub"}

    log_callback("=" * 60)
    if dry_run:
        log_callback(
            "🔍 当前为【预览模式】，不会实际修改文件。\n请检查下方的重命名计划是否正确。"
        )
    else:
        log_callback("🚀 当前为【执行模式】，正在重命名文件...")
    log_callback("=" * 60)

    try:
        if not video_root.exists() or not video_root.is_dir():
            log_callback("❌ 视频目录不存在！")
            return
        if not sub_root.exists() or not sub_root.is_dir():
            log_callback("❌ 字幕目录不存在！")
            return

        # 遍历视频根目录下的所有季数文件夹 (如 Season 1, Season 2...)
        has_seasons = False
        for video_season_dir in video_root.iterdir():
            if not video_season_dir.is_dir():
                continue

            has_seasons = True
            season_name = video_season_dir.name
            sub_season_dir = sub_root / season_name

            if not sub_season_dir.exists():
                log_callback(f"⚠️ 找不到对应的字幕文件夹，已跳过: {season_name}")
                continue

            # 获取视频和字幕文件，并按字母顺序排序
            videos = sorted(
                [
                    f
                    for f in video_season_dir.iterdir()
                    if f.suffix.lower() in video_exts
                ]
            )
            subs = sorted(
                [f for f in sub_season_dir.iterdir() if f.suffix.lower() in sub_exts]
            )

            if not videos and not subs:
                continue

            # 安全检查：如果集数对不上，跳过该季
            if len(videos) != len(subs):
                log_callback(
                    f"\n⚠️ 数量不匹配！[{season_name}] 有 {len(videos)} 个视频，但有 {len(subs)} 个字幕。为了安全，已跳过该季。"
                )
                continue

            log_callback(f"\n📂 正在处理: {season_name}")
            for v_file, s_file in zip(videos, subs):
                # 新的字幕名称 = 视频的纯文件名 + .zh-cn + 原字幕的后缀名
                new_sub_name = v_file.stem + ".zh-cn" + s_file.suffix
                new_sub_path = s_file.parent / new_sub_name

                # 如果新的名字和老的名字一样，跳过
                if s_file.name == new_sub_name:
                    continue

                if dry_run:
                    log_callback(f"  [预览] {s_file.name}  -->  {new_sub_name}")
                else:
                    s_file.rename(new_sub_path)
                    log_callback(f"  [成功] 重命名为 -> {new_sub_name}")

        if not has_seasons:
            log_callback(
                "\n⚠️ 视频目录下没有找到子文件夹（例如 Season 1 等）。此脚本默认处理按季分文件夹的结构。"
            )

        log_callback("\n✅ 处理完成！")
    except Exception as e:
        log_callback(f"\n❌ 发生错误: {str(e)}")


class SubtitleRenamerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("字幕批量重命名工具")
        self.root.geometry("850x650")

        # 居中窗口
        self.root.eval("tk::PlaceWindow . center")

        # 设置窗口图标（兼容打包后的exe路径）
        try:
            self.root.iconbitmap(get_resource_path("logo.ico"))
        except Exception:
            pass  # 如果没找到图标或者报错则忽略，使用默认图标

        # 设置主题和样式
        self.style = ttk.Style()
        # 尽量使用系统原生主题
        available_themes = self.style.theme_names()
        if "vista" in available_themes:
            self.style.theme_use("vista")
        elif "windows" in available_themes:
            self.style.theme_use("windows")
        elif "clam" in available_themes:
            self.style.theme_use("clam")

        # 配置全局字体
        normal_font = ("Microsoft YaHei", 10)
        bold_font = ("Microsoft YaHei", 10, "bold")

        self.style.configure("TLabel", font=normal_font)
        self.style.configure("TButton", font=normal_font, padding=5)
        self.style.configure("TLabelframe.Label", font=bold_font, foreground="#333333")
        self.style.configure(
            "Action.TButton", font=("Microsoft YaHei", 11, "bold"), padding=8
        )

        # 主框架容器，带内边距
        main_frame = ttk.Frame(root, padding=(20, 20, 20, 20))
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ---------------- 目录设置区域 ----------------
        dir_frame = ttk.LabelFrame(main_frame, text=" 📁 目录设置 ", padding=(15, 15))
        dir_frame.pack(fill=tk.X, pady=(0, 20))

        # 视频目录
        ttk.Label(dir_frame, text="视频主目录:").grid(
            row=0, column=0, padx=(0, 10), pady=10, sticky="e"
        )
        self.video_var = tk.StringVar()
        video_entry = ttk.Entry(
            dir_frame, textvariable=self.video_var, width=70, font=("Consolas", 10)
        )
        video_entry.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
        ttk.Button(dir_frame, text="浏览...", command=self.browse_video, width=10).grid(
            row=0, column=2, padx=(10, 0), pady=10
        )

        # 字幕目录
        ttk.Label(dir_frame, text="字幕主目录:").grid(
            row=1, column=0, padx=(0, 10), pady=10, sticky="e"
        )
        self.sub_var = tk.StringVar()
        sub_entry = ttk.Entry(
            dir_frame, textvariable=self.sub_var, width=70, font=("Consolas", 10)
        )
        sub_entry.grid(row=1, column=1, padx=5, pady=10, sticky="ew")
        ttk.Button(dir_frame, text="浏览...", command=self.browse_sub, width=10).grid(
            row=1, column=2, padx=(10, 0), pady=10
        )

        dir_frame.columnconfigure(1, weight=1)

        # ---------------- 操作按钮区域 ----------------
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 20))

        # 让按钮居中
        btn_container = ttk.Frame(btn_frame)
        btn_container.pack(anchor="center")

        ttk.Button(
            btn_container,
            text="🔍 预览重命名 (Dry Run)",
            style="Action.TButton",
            command=self.dry_run,
            width=25,
        ).pack(side=tk.LEFT, padx=15)
        ttk.Button(
            btn_container,
            text="🚀 开始执行重命名",
            style="Action.TButton",
            command=self.execute,
            width=25,
        ).pack(side=tk.LEFT, padx=15)

        # ---------------- 日志输出区域 ----------------
        log_frame = ttk.LabelFrame(main_frame, text=" 📝 运行日志 ", padding=(10, 10))
        log_frame.pack(fill=tk.BOTH, expand=True)

        # 使用一个深色的背景模拟终端效果，看起来更极客和专业
        self.log_area = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white",
            relief=tk.FLAT,
            padx=10,
            pady=10,
        )
        self.log_area.pack(fill=tk.BOTH, expand=True)

        self.log_area.tag_config("highlight", foreground="#4ec9b0")
        self.log_area.tag_config("warning", foreground="#ce9178")

        self.log("✨ 欢迎使用字幕批量重命名工具")
        self.log("-" * 60)
        self.log("使用说明：")
        self.log("1. 请选择【视频主文件夹】和【字幕主文件夹】。")
        self.log("   结构要求：目录下需要按季建立子文件夹（例如 Season 1）。")
        self.log("   视频和字幕文件由于会经过排序，请务必保证集数对应一致。")
        self.log("2. 点击【预览重命名】，可以在此日志区查看将要执行的重命名计划。")
        self.log("3. 确认无误后，点击【开始执行重命名】进行真正的修改。")
        self.log("-" * 60 + "\n")

    def browse_video(self):
        folder = filedialog.askdirectory(title="选择视频主文件夹")
        if folder:
            self.video_var.set(os.path.normpath(folder))

    def browse_sub(self):
        folder = filedialog.askdirectory(title="选择字幕主文件夹")
        if folder:
            self.sub_var.set(os.path.normpath(folder))

    def log(self, msg):
        self.log_area.insert(tk.END, msg + "\n")
        self.log_area.see(tk.END)

    def dry_run(self):
        video_dir = self.video_var.get().strip()
        sub_dir = self.sub_var.get().strip()
        if not video_dir or not sub_dir:
            messagebox.showwarning("提示", "请先选择视频目录和字幕目录！")
            return

        self.log_area.delete(1.0, tk.END)
        self.root.update()
        sync_subtitle_names(video_dir, sub_dir, dry_run=True, log_callback=self.log)

    def execute(self):
        video_dir = self.video_var.get().strip()
        sub_dir = self.sub_var.get().strip()
        if not video_dir or not sub_dir:
            messagebox.showwarning("提示", "请先选择视频目录和字幕目录！")
            return

        if messagebox.askyesno(
            "⚠ 最终确认",
            "确定要执行真实的重命名操作吗？\n由于重命名不可逆，请务必确保已经预览过结果并且完全正确！",
        ):
            self.log_area.delete(1.0, tk.END)
            self.root.update()
            sync_subtitle_names(
                video_dir, sub_dir, dry_run=False, log_callback=self.log
            )


if __name__ == "__main__":
    # 为了解决高DPI下界面模糊的问题
    try:
        from ctypes import windll

        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    root = tk.Tk()
    app = SubtitleRenamerApp(root)
    root.mainloop()
