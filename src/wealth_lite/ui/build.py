#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WealthLite UI 构建脚本
将src目录的源码构建到dist目录，包括压缩、优化等
"""

import os
import sys
import json
import shutil
import re
from pathlib import Path
from datetime import datetime

class WealthLiteBuilder:
    """WealthLite UI构建器"""
    
    def __init__(self):
        self.src_dir = Path("src")
        self.dist_dir = Path("dist")
        self.assets_dir = self.src_dir / "assets"
        self.build_info = {
            "build_time": datetime.now().isoformat(),
            "version": "1.0.0"
        }
    
    def clean_dist(self):
        """清理dist目录"""
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)
        self.dist_dir.mkdir(exist_ok=True)
        print("🧹 已清理dist目录")
    
    def copy_html_files(self):
        """复制并处理HTML文件"""
        html_files = list(self.src_dir.glob("*.html"))
        for html_file in html_files:
            content = html_file.read_text(encoding='utf-8')
            
            # 更新资源路径
            content = self.update_resource_paths(content)
            
            # 添加构建信息
            content = self.add_build_info(content)
            
            # 压缩HTML（可选）
            if self.should_minify():
                content = self.minify_html(content)
            
            # 写入dist目录
            dist_file = self.dist_dir / html_file.name
            dist_file.write_text(content, encoding='utf-8')
            print(f"📄 已处理: {html_file.name}")
    
    def process_css_files(self):
        """处理CSS文件"""
        css_dir = self.dist_dir / "css"
        css_dir.mkdir(exist_ok=True)
        
        # 合并所有CSS文件
        all_css = []
        css_files = list(self.src_dir.glob("styles/*.css"))
        
        for css_file in css_files:
            content = css_file.read_text(encoding='utf-8')
            
            # 添加文件注释
            all_css.append(f"/* === {css_file.name} === */")
            all_css.append(content)
            all_css.append("")
        
        # 写入合并的CSS文件
        combined_css = "\n".join(all_css)
        
        # 压缩CSS（可选）
        if self.should_minify():
            combined_css = self.minify_css(combined_css)
        
        output_file = css_dir / "main.css"
        output_file.write_text(combined_css, encoding='utf-8')
        print(f"🎨 已合并CSS文件: {len(css_files)}个文件 -> main.css")
    
    def process_js_files(self):
        """处理JavaScript文件"""
        js_dir = self.dist_dir / "js"
        js_dir.mkdir(exist_ok=True)
        
        # 合并所有JS文件
        all_js = []
        js_files = list(self.src_dir.glob("js/*.js"))
        
        for js_file in js_files:
            content = js_file.read_text(encoding='utf-8')
            
            # 添加文件注释
            all_js.append(f"/* === {js_file.name} === */")
            all_js.append(content)
            all_js.append("")
        
        # 写入合并的JS文件
        combined_js = "\n".join(all_js)
        
        # 压缩JS（可选）
        if self.should_minify():
            combined_js = self.minify_js(combined_js)
        
        output_file = js_dir / "main.js"
        output_file.write_text(combined_js, encoding='utf-8')
        print(f"⚡ 已合并JS文件: {len(js_files)}个文件 -> main.js")
    
    def copy_assets(self):
        """复制静态资源"""
        if self.assets_dir.exists():
            dist_assets = self.dist_dir / "assets"
            shutil.copytree(self.assets_dir, dist_assets, dirs_exist_ok=True)
            print(f"📁 已复制静态资源")
    
    def update_resource_paths(self, html_content):
        """更新HTML中的资源路径"""
        # 更新CSS路径
        html_content = re.sub(
            r'<link rel="stylesheet" href="styles/[^"]*">',
            '<link rel="stylesheet" href="css/main.css">',
            html_content
        )
        
        # 更新JS路径
        html_content = re.sub(
            r'<script src="js/[^"]*"></script>',
            '<script src="js/main.js"></script>',
            html_content
        )
        
        # 移除开发工具相关代码（生产环境不需要）
        html_content = re.sub(
            r'<!-- 开发工具.*?</script>',
            '<!-- 开发工具已在生产构建中移除 -->',
            html_content,
            flags=re.DOTALL
        )
        
        return html_content
    
    def add_build_info(self, html_content):
        """添加构建信息到HTML"""
        build_comment = f"""
<!-- 
WealthLite UI - 构建信息
构建时间: {self.build_info['build_time']}
版本: {self.build_info['version']}
-->"""
        
        # 在<head>标签后添加构建信息
        html_content = html_content.replace(
            '<head>',
            f'<head>{build_comment}'
        )
        
        return html_content
    
    def should_minify(self):
        """检查是否应该压缩代码"""
        # 简单实现，可以通过环境变量或配置文件控制
        return os.getenv('MINIFY', 'false').lower() == 'true'
    
    def minify_html(self, html_content):
        """简单的HTML压缩"""
        # 移除多余的空白字符
        html_content = re.sub(r'\s+', ' ', html_content)
        html_content = re.sub(r'>\s+<', '><', html_content)
        return html_content.strip()
    
    def minify_css(self, css_content):
        """简单的CSS压缩"""
        # 移除注释
        css_content = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)
        # 移除多余的空白
        css_content = re.sub(r'\s+', ' ', css_content)
        css_content = re.sub(r';\s*}', '}', css_content)
        css_content = re.sub(r'{\s*', '{', css_content)
        css_content = re.sub(r'}\s*', '}', css_content)
        return css_content.strip()
    
    def minify_js(self, js_content):
        """简单的JavaScript压缩"""
        # 移除单行注释
        js_content = re.sub(r'//.*$', '', js_content, flags=re.MULTILINE)
        # 移除多行注释
        js_content = re.sub(r'/\*.*?\*/', '', js_content, flags=re.DOTALL)
        # 移除多余的空白
        js_content = re.sub(r'\s+', ' ', js_content)
        return js_content.strip()
    
    def generate_build_info(self):
        """生成构建信息文件"""
        build_info_file = self.dist_dir / "build-info.json"
        
        # 计算文件大小
        total_size = 0
        file_list = []
        
        for file_path in self.dist_dir.rglob("*"):
            if file_path.is_file() and file_path.name != "build-info.json":
                size = file_path.stat().st_size
                total_size += size
                file_list.append({
                    "path": str(file_path.relative_to(self.dist_dir)),
                    "size": size
                })
        
        build_info = {
            **self.build_info,
            "total_size": total_size,
            "files": file_list,
            "file_count": len(file_list)
        }
        
        build_info_file.write_text(
            json.dumps(build_info, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
        print(f"📊 构建信息: {len(file_list)}个文件, 总大小: {total_size:,}字节")
    
    def build(self):
        """执行完整构建"""
        print("🏗️ 开始构建 WealthLite UI...")
        print("=" * 50)
        
        try:
            self.clean_dist()
            self.copy_html_files()
            self.process_css_files()
            self.process_js_files()
            self.copy_assets()
            self.generate_build_info()
            
            print("=" * 50)
            print("✅ 构建完成!")
            print(f"📁 输出目录: {self.dist_dir.absolute()}")
            print("💡 运行预览: python -m http.server 8080 --directory dist")
            
        except Exception as e:
            print(f"❌ 构建失败: {e}")
            sys.exit(1)

def main():
    """主函数"""
    # 检查是否在正确的目录
    if not os.path.exists('src'):
        print("❌ 错误: 请在ui目录下运行此脚本")
        print("💡 提示: cd ui && python build.py")
        sys.exit(1)
    
    # 执行构建
    builder = WealthLiteBuilder()
    builder.build()

if __name__ == "__main__":
    main() 