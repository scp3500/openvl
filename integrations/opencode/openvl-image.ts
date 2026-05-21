import type { Plugin } from "@opencode-ai/plugin";
import * as fs from "fs";
import * as path from "path";
const plugin: Plugin = {
  "experimental.chat.messages.transform": (messages) => {
    let imgIndex = 0;
    for (const msg of messages) {
      if (msg.role !== "user") continue;
      const content = msg.content;
      if (typeof content === "string" || !Array.isArray(content)) continue;
      const parts: any[] = [];
      for (const p of content) {
        if (p.type === "image_url" && p.image_url?.url?.startsWith("data:")) {
          imgIndex++;
          const tmp = path.join(
            process.env["TMP"] || "/tmp",
            `openvl_img${imgIndex}.png`
          );
          try {
            const b64 = p.image_url.url.split(",")[1];
            fs.writeFileSync(tmp, Buffer.from(b64, "base64"));
            parts.push({
              type: "text",
              text: `[Image: ${tmp}]`,
            });
          } catch {
            parts.push({ type: "text", text: "[Image: paste_error]" });
          }
        } else {
          parts.push(p);
        }
      }
      if (imgIndex > 0) msg.content = parts;
    }
    return messages;
  },
};
export default plugin;
