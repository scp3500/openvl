import type { Plugin } from "@opencode-ai/plugin";
const plugin: Plugin = {
  "experimental.chat.messages.transform": (messages) => {
    for (const msg of messages) {
      if (msg.role !== "user") continue;
      const content = msg.content;
      if (typeof content === "string" || !Array.isArray(content)) continue;
      const hasImage = content.some(
        (p) => p.type === "image_url" && p.image_url?.url?.startsWith("data:")
      );
      if (!hasImage) continue;
      msg.content = content.map((p) =>
        p.type === "image_url" && p.image_url?.url?.startsWith("data:")
          ? { type: "text", text: `[Image: ${p.image_url.url.substring(0, 40)}...]` }
          : p
      );
    }
    return messages;
  },
};
export default plugin;
