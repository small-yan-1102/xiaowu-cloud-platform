# -*- coding: utf-8 -*-
"""
云效 Testhub 同步工具 - CLI 入口

支持命令行参数控制同步行为：
  --config    指定配置文件路径
  --module    限定同步模块
  --dry-run   模拟模式（不实际调用 API）
  --force     忽略去重，强制同步
  --list-modules  列出可用模块
  --verbose   详细日志输出
"""

import sys
import os
import argparse
import logging

# 路径设置：将 lib/yunxiao 目录加入 sys.path，使 scripts 可作为包导入
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LIB_DIR = os.path.dirname(SCRIPT_DIR)
PROJECT_ROOT = os.path.dirname(os.path.dirname(LIB_DIR))

sys.path.insert(0, LIB_DIR)

from scripts.config import load_config, validate_config, AppConfig
from scripts.md_parser import parse_all_md_files, list_available_modules
from scripts.sync_engine import run_sync, print_report


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器

    Returns:
        argparse.ArgumentParser: 参数解析器
    """
    parser = argparse.ArgumentParser(
        prog='yunxiao-sync',
        description='将 Markdown 测试用例同步到阿里云效 Testhub',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 模拟同步企业认证模块
  python main.py --module enterprise_cert --dry-run --verbose

  # 同步所有模块
  python main.py --config config.yaml

  # 列出可用模块
  python main.py --list-modules

  # 强制重新同步（忽略已同步状态）
  python main.py --module login --force
        """,
    )

    parser.add_argument(
        '--config', '-c',
        default=os.path.join(LIB_DIR, 'config.yaml'),
        help='配置文件路径 (默认: config.yaml)',
    )
    parser.add_argument(
        '--module', '-m',
        action='append',
        dest='modules',
        help='限定同步模块 (可多次指定，如 --module enterprise_cert --module login)',
    )
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        default=False,
        help='模拟模式：解析并映射用例，但不实际调用云效 API',
    )
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        default=False,
        help='强制同步：忽略本地同步状态，重新创建所有用例',
    )
    parser.add_argument(
        '--list-modules', '-l',
        action='store_true',
        default=False,
        help='列出所有可用模块及用例数量',
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        default=False,
        help='输出详细日志（DEBUG 级别）',
    )

    return parser


def setup_logging(verbose: bool = False):
    """配置日志输出

    Args:
        verbose: 是否输出 DEBUG 级别日志
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )


def handle_list_modules(config: AppConfig):
    """处理 --list-modules 命令

    Args:
        config: 应用配置
    """
    md_dir = os.path.join(config.project_root, config.sync.md_case_dir)
    print(f"\n用例目录: {md_dir}")
    print("-" * 50)

    modules = list_available_modules(md_dir)
    if not modules:
        print("未找到任何模块文件")
        return

    total = 0
    for key, info in sorted(modules.items()):
        print(f"  {key:20s}  {info['file']:40s}  {info['count']:3d} 条用例")
        total += info['count']

    print("-" * 50)
    print(f"  {'合计':20s}  {'':40s}  {total:3d} 条用例")
    print(f"\n使用方式: python main.py --module <模块名>")


def main():
    """CLI 主入口函数"""
    parser = build_parser()
    args = parser.parse_args()

    # 配置日志
    setup_logging(args.verbose)

    print("=" * 60)
    print("云效 Testhub 同步工具")
    print("=" * 60)

    # 加载配置
    config_path = os.path.abspath(args.config)
    print(f"\n配置文件: {config_path}")

    config = load_config(config_path, PROJECT_ROOT)

    # 处理 --list-modules
    if args.list_modules:
        handle_list_modules(config)
        return 0

    # 合并命令行参数到配置
    if args.dry_run:
        config.sync.dry_run = True
        print("[模式] DRY-RUN 模拟模式")

    if args.modules:
        config.sync.modules = args.modules
        print(f"[过滤] 仅同步模块: {', '.join(args.modules)}")

    if args.force:
        # 清空状态文件以实现强制同步
        state_path = os.path.join(config.project_root, config.mapping.state_file)
        if os.path.exists(state_path):
            os.remove(state_path)
            print("[强制] 已清除本地同步状态")

    # 校验配置（dry-run 模式下跳过 AK/SK 校验）
    if not config.sync.dry_run:
        errors = validate_config(config)
        if errors:
            print("\n[错误] 配置校验失败:")
            for err in errors:
                print(f"  - {err}")
            return 1
    else:
        # dry-run 模式仅校验用例目录
        md_dir = os.path.join(config.project_root, config.sync.md_case_dir)
        if not os.path.isdir(md_dir):
            print(f"\n[错误] 用例目录不存在: {md_dir}")
            return 1

    # 执行同步
    try:
        report = run_sync(config, config_path, force_update=args.force)
        print_report(report)

        if report.failed > 0:
            return 2
        return 0
    except KeyboardInterrupt:
        print("\n[中断] 用户取消同步")
        return 130
    except Exception as e:
        logging.getLogger(__name__).exception("同步过程发生异常")
        print(f"\n[异常] {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
