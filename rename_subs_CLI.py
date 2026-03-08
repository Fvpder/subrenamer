import os
import sys
import argparse
from pathlib import Path


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


def main():
    parser = argparse.ArgumentParser(description="字幕批量重命名工具 CLI 版")
    parser.add_argument(
        "video_dir", help="视频主目录，目录下需要有类似 Season 1 的子目录"
    )
    parser.add_argument(
        "sub_dir", help="字幕主目录，目录下需要有类似 Season 1 的子目录"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="实际执行重命名操作，若不带此参数默认是预览模式 (dry-run)",
    )

    args = parser.parse_args()

    sync_subtitle_names(args.video_dir, args.sub_dir, dry_run=not args.execute)


if __name__ == "__main__":
    main()
