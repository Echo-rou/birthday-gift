# Birthday Gift · 时光放映

现有生日网站的内容与视觉更新。网址仍为 https://echo-rou.github.io/birthday-gift/ 。

流程：封面 → 有声开场视频 → 时光放映序幕 → 问候 → 12张照片（第12张为月亮尾声）→ 信件。

## 本轮更新

- 接入用户提供的15秒开场视频，720×1280 / 30fps / H.264 / AAC / faststart。保留原AAC音轨字节，不默认静音。
- 移除旧“今年的这一章”结尾视频及初始化、UI、资源请求。旧视频已在本地备份，不再随网站发布。
- 序幕暖金环境光与文字分句显现约2.6秒；视频遮罩完全退出后才开始。可立即下滑，尊重减少动态效果设置。
- 替换数组第9和11张照片，使用真实本地素材，其他10项、信件和章节顺序不变。
- 修整小屏相纸章节、封面文字、安全区域及跳过按钮；保持按需加载和图片重试机制。

详情见 [本轮验收报告](docs/当前报告5.md)，前一轮记录见 [报告4](docs/当前报告4.md)。

## 预览与修改

在本目录运行 `python -m http.server 8765`，打开 http://localhost:8765/ 。

所有故事内容集中在 index.html 的 CONFIG。openingVideo 留空可关闭开场视频；修改文件时保持用户点击后同步调用play，以保留有声播放权限。

替换JPEG后运行（需要Pillow）：

```powershell
python tools/prepare_images.py --manifest ../ref/image-manifest.json --embed
```

脚本只更新当前CONFIG里的12张照片及封面，保留原JPEG回退。已退役的照片留存，不会被页面加载。

## 验证

真实Windows Chrome GUI完成四种视口：390×844、375×667、320×568、1440×900。视频实际播放、自然结束、跳过/重播、12章、信件和错误恢复等13项场景通过，保留截图。

iPhone Safari、Android Chrome、微信仅做Chrome中的视口/UA模拟，未测试真机或真实WebKit/微信内核；不能把UA模拟视为这些浏览器的兼容性认证。

测试脚本及基线已随仓库提交。在Windows上安装Playwright后，运行 `python tools/test_gui.py`，使用默认安装位置的Chrome；结果写到已忽略的test-artifacts/round2目录。
