# 生日网站 · 加载优化版

基于提交 `07592c86004549c53985d576248b61b17ade5e80`，保留原来的12张照片、排版、文案和视频。本版本用于发布到现有 GitHub Pages，部署状态以仓库 Actions 和线上页面为准。详细进展见 [当前报告4](docs/当前报告4.md)。

## 预览

双击 index.html，或在本目录运行 `python -m http.server 8765` 后打开 http://localhost:8765/。

## 优化内容

- 封面优先加载，WebP失败回退JPEG。
- 内嵌小预览先显示，清晰照片就绪后淡入。
- 封面完成后预热第一张；开启故事先加载两张，随后准备当前及后两张，最多同时下载两张。
- 桌面虚化背景复用已下载照片，视频海报到附近才加载，视频点击播放才下载。
- 开场视频尚未上传，默认直接进入故事，避免不存在文件造成黑屏等待。
- 图片失败可重试，联网后恢复；挂起12秒释放下载位置。开场视频等待8秒后退出，重播清理旧计时器。

## 更新

文字仍在 index.html 的 CONFIG 中修改。上传 opening.mp4 后，把 CONFIG.openingVideo 改为 `"opening.mp4"` 启用开场视频。

替换JPEG后运行以下命令，更新WebP、内嵌清单和封面预览（需要Pillow）：

```powershell
python tools/prepare_images.py --manifest ../ref/image-manifest.json --embed
```

保留JPEG回退文件。个别JPEG更小，会直接使用原JPEG。

## 发布

现有仓库为 Echo-rou/birthday-gift。先核对远端是否出现新提交，再更新根目录的 index.html、assets/、photos/ 和需要更新的 video.mp4。不要套一层 website 目录，也不要上传 ref 测试输出。

沿用现有Pages设置，二维码/NFC地址仍是 https://echo-rou.github.io/birthday-gift/ 。旧工作区未修改。

## 验证范围

Chrome手机尺寸390×844、桌面1440×1000，冷缓存模拟1.6Mbps/150ms。12张照片、JPEG回退、失败恢复、视频播放、重播、照片及开场超时均通过。

这不是手机真机或微信内置浏览器实测，也不包含GitHub Pages实际连接耗时；发布后需在目标手机扫码验收。详细结果和截图位于 ../ref/website-performance/。
