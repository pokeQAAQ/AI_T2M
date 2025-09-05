# -*- coding: utf-8 -*-
"""图片处理工具"""

import os
from PIL import Image


class ImageUtils:
    @staticmethod
    def validate_and_fix_image(image_path):
        try:
            with Image.open(image_path) as img:
                if img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')
                max_size = 2000
                if img.width > max_size or img.height > max_size:
                    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                fixed_path = image_path.replace('.jpg', '_fixed.jpg')
                img.save(fixed_path, 'JPEG', quality=90)
                print(f"✅ 图片已优化: {fixed_path}")
                return fixed_path
        except Exception as e:
            print(f"❌ 图片处理失败: {e}")
            return image_path

    @staticmethod
    def to_png_thumbnail(image_path, max_side=1024):
        try:
            with Image.open(image_path) as im:
                if im.mode not in ('RGB', 'L'):
                    im = im.convert('RGB')
                im.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
                base, _ = os.path.splitext(image_path)
                out_path = f"{base}_fixed.png"
                im.save(out_path, 'PNG', optimize=True)
                print(f"✅ PNG 缩略图已生成: {out_path}")
                return out_path
        except Exception as e:
            print(f"❌ PNG 转换失败: {e}")
            return image_path
