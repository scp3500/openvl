/**
 * OpenVL - OpenCode 图片插件
 *
 * 用户粘贴图片到聊天框时，OpenCode 把图片转成 data:image/...;base64,...
 * 放在消息里。非视觉模型无法处理这种格式。
 *
 * 这个插件拦截消息，把 image_url 转成 [Image: data:...] 纯文本，
 * AI 看到后就会自动调 openvl --base64 读取图片并描述。
 *
 * 安装：
 *   1. 把本文件放到 ~/.config/opencode/plugin/openvl-image.ts
 *   2. 在 ~/.config/opencode/opencode.json 添加：
 *        "plugin": ["./plugin/openvl-image.ts"]
 *   3. 重启 OpenCode
 */
import type { Plugin } from "@opencode-ai/plugin";
export default (async () => {
  return {
    "experimental.chat.messages.transform": async (messages) => {
      for (const msg of messages) {
        if (msg.role !== "user") continue;
        const content = msg.content;
        if (typeof content === "string") continue;
        if (!Array.isArray(content)) continue;

        const hasImage = content.some(
          (part) => part.type === "image_url" && part.image_url?.url?.startsWith("data:")
        );
        if (!hasImage) continue;

        const newParts = [];
        for (const part of content) {
          if (part.type === "image_url" && part.image_url?.url?.startsWith("data:")) {
            newParts.push({
              type: "text",
              text: `[Image: ${part.image_url.url.substring(0, 50)}...]`,
            });
          } else {
            newParts.push(part);
          }
        }
        msg.content = newParts;
      }
      return messages;
    },
  };
}) satisfies Plugin;
