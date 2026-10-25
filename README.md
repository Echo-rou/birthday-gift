# 生日礼物网页 · 部署与修改说明

网址原理：二维码和 NFC 里只写一个**永远不变**的网址，内容都在这个网页里，以后随时改。

## 首次上线（GitHub Pages，约 10 分钟）

1. 注册/登录 [github.com](https://github.com)，右上角 `+` → `New repository`，
   名字填 `birthday-gift`，选 **Public**，创建。
2. 进入仓库页面 → `Add file` → `Upload files`，把本文件夹里的
   `index.html` 和 `video.mp4` 一起拖进去 → 点 `Commit changes`。
3. 仓库顶部 `Settings` → 左侧 `Pages` → `Branch` 选 `main` → `Save`。
4. 等约 1 分钟，页面顶部出现网址：
   `https://你的用户名.github.io/birthday-gift/`
   **这个网址就是最终要写进二维码和 NFC 的地址**。

## 以后怎么改内容（不用碰电脑上的文件）

- **改文字**：GitHub 网页上点开 `index.html` → 右上铅笔图标编辑 →
  只改文件中部 `CONFIG` 里引号内的文字 → `Commit changes`。约 1 分钟生效。
- **换视频**：点开 `video.mp4` → `Replace` 上传新文件（保持同名，代码不用动）。
- **改成跳转别的网站**：编辑 `index.html`，把 `CONFIG` 那段换成一行
  `location.replace("https://新网址");`

## 本地预览

直接双击 `index.html` 用浏览器打开即可（视频和文字都会正常显示）。
