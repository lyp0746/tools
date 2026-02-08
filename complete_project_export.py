"""
Project Exporter Pro - 专业项目文件结构导出工具
基于Python开发，支持完整项目结构导出、大文件处理、多格式输出
Version: 1.0.0
github网址： https://github.com/lyp0746
QQ邮箱：1610369302@qq.com
作者：LYP
"""

import os
from pathlib import Path
from datetime import datetime


def get_file_info(file_path, project_root):
    """获取文件基本信息"""
    try:
        stat = file_path.stat()
        return {
            'path': str(file_path.relative_to(project_root)),
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime),
            'readable': os.access(file_path, os.R_OK)
        }
    except:
        return {
            'path': str(file_path.relative_to(project_root)),
            'size': 0,
            'modified': datetime.now(),
            'readable': False
        }


def format_size(size_bytes):
    """格式化文件大小"""
    if size_bytes == 0:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} GB"


def read_complete_file(file_path):
    """读取完整文件内容"""
    try:
        if not os.access(file_path, os.R_OK):
            return "[权限不足，无法读取]"
        
        file_size = file_path.stat().st_size
        
        # 处理大文件
        if file_size > 5 * 1024 * 1024:  # 5MB以上
            return f"[文件过大({format_size(file_size)})，跳过内容预览]"
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # 如果内容过长，适当截断但显示更多内容
        if len(content) > 10000:  # 超过1万字符
            content = content[:10000] + f"\n... (文件内容过长，已截断前10000字符，总长度{len(content)}字符)"
            
        return content
    except PermissionError:
        return "[权限不足，无法读取文件]"
    except UnicodeDecodeError:
        return "[文件编码问题，无法读取内容]"
    except Exception as e:
        return f"[读取文件失败: {str(e)}]"


def should_include(path):
    """判断是否应该包含该路径"""
    exclude = [
        '__pycache__', '.git', '.venv', 'venv', 'env',
        '.idea', '.vscode', '*.pyc', '*.pyo', 'dist', 'build',
        '*.db', '*.sqlite', '*.log'  # 排除数据库和日志文件
    ]
    
    name = path.name
    for pattern in exclude:
        if pattern.startswith('*'):
            if name.endswith(pattern[1:]):
                return False
        elif name == pattern:
            return False
    
    return True


def collect_files(project_root):
    """收集项目文件"""
    files = []
    
    for root, dirs, filenames in os.walk(project_root):
        # 过滤目录
        dirs[:] = [d for d in dirs if should_include(Path(root) / d)]
        
        # 处理文件
        for filename in filenames:
            file_path = Path(root) / filename
            if should_include(file_path):
                files.append(file_path)
    
    # 按文件类型和路径排序
    files.sort(key=lambda x: (x.suffix, str(x)))
    return files


def export_complete_project():
    """导出完整项目结构"""
    project_root = Path(__file__).parent
    output_file = project_root / 'project_complete_export.txt'
    
    print(f"项目路径: {project_root}")
    print("开始收集文件...")
    
    files = collect_files(project_root)
    print(f"找到 {len(files)} 个文件")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # 写入头部
        f.write("=" * 80 + "\n")
        f.write("医疗器械内容生成系统 - 完整项目文件结构\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"项目路径: {project_root}\n")
        f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"文件总数: {len(files)}\n\n")
        
        # 按目录分组显示
        current_dir = None
        
        for i, file_path in enumerate(files, 1):
            file_info = get_file_info(file_path, project_root)
            
            # 显示进度
            if i % 10 == 0:
                print(f"处理进度: {i}/{len(files)} 文件")
            
            # 检查是否是新目录
            file_dir = str(Path(file_info['path']).parent)
            if file_dir != current_dir:
                if current_dir is not None:
                    f.write("\n" + "=" * 60 + "\n\n")
                current_dir = file_dir
                f.write(f"📁 目录: {file_dir if file_dir != '.' else '根目录'}\n")
                f.write("=" * 60 + "\n\n")
            
            # 写入文件信息
            f.write(f"📄 文件: {file_info['path']}\n")
            f.write(f"   大小: {format_size(file_info['size'])}")
            f.write(f" | 修改时间: {file_info['modified'].strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            # 读取并显示完整文件内容
            if file_info['readable']:
                content = read_complete_file(file_path)
                f.write("   内容:\n")
                f.write("   " + "-" * 50 + "\n")
                
                # 逐行写入内容，保持格式
                for line in content.split('\n'):
                    f.write(f"   {line}\n")
                
                f.write("   " + "-" * 50 + "\n")
            else:
                f.write("   状态: [文件不可读]\n")
            
            f.write("\n")
        
        # 写入统计信息
        f.write("=" * 80 + "\n")
        f.write("项目统计信息:\n")
        f.write("-" * 40 + "\n")
        
        # 按文件类型统计
        file_types = {}
        total_size = 0
        
        for file_path in files:
            file_info = get_file_info(file_path, project_root)
            ext = file_path.suffix.lower()
            file_types[ext] = file_types.get(ext, 0) + 1
            total_size += file_info['size']
        
        f.write(f"总大小: {format_size(total_size)}\n")
        f.write(f"总文件数: {len(files)}\n\n")
        
        f.write("按文件类型统计:\n")
        for ext, count in sorted(file_types.items()):
            f.write(f"  {ext if ext else '无扩展名'}: {count} 个文件\n")
        
        f.write("=" * 80 + "\n")
    
    print(f"导出完成！文件已保存到: {output_file}")
    print(f"总共导出了 {len(files)} 个文件")
    print(f"输出文件大小: {format_size(output_file.stat().st_size)}")


if __name__ == "__main__":
    try:
        export_complete_project()
    except Exception as e:
        print(f"导出失败: {e}")
        import traceback
        traceback.print_exc()