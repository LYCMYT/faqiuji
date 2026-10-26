# 第三方与来源

本次未导入第三方机械CAD模型、图片或供应商几何。原设计数据由用户提供；来源索引保留于 data/sources.json，不代表本次重新验证了其机械或性能结论。

- CadQuery 2.8.0：Apache-2.0；原生实体和STEP生成。官方文档 https://cadquery.readthedocs.io/en/latest/importexport.html 。参数历史由Python+JSON保留，STEP不保存完整参数历史。
- OpenCascade/OCCT：LGPL-2.1 with exception；通过cadquery-ocp使用。
- Blender 4.5.9 LTS：GPL；官方便携版本来自 https://download.blender.org/release/Blender4.5/blender-4.5.9-windows-x64.zip 。工具程序不包含在交付ZIP。
- Three.js 0.180.0：MIT。浏览器所需源码本地打包；许可全文见 three-LICENSE.txt。原始包来自 https://unpkg.com/three@0.180.0/ 。GLTFLoader仅修改本地导入路径。
- ReportLab、Pillow、PyMuPDF：运行环境依赖；版本见 requirements-lock.txt。字体使用本机Microsoft YaHei；未分发字体文件。
- FFmpeg：本机GPL构建用于生成H.264视频；未分发程序。

glTF规范：https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html 。本项目通过实际标定块和轴杆往返检查单位与方向，记录在 output/calibration/。
