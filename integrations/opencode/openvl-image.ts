import type { Plugin } from "@opencode-ai/plugin";
import * as fs from "fs";
import * as os from "os";
import * as path from "path";

const plugin: Plugin = {
  "experimental.chat.messages.transform": async (_input, output) => {
    for (const msg of output.messages) {
      const parts = msg.parts;
      if (!parts) continue;
      let imgIndex = 0;
      const newParts: any[] = [];
      for (const part of parts) {
        if (part.type === "image_url" && (part as any).image_url?.url?.startsWith("data:")) {
          imgIndex++;
          const url = (part as any).image_url.url;
          const tmp = path.join(os.tmpdir(), `openvl_img${imgIndex}.png`);
          try {
            const b64 = url.split(",")[1];
            fs.writeFileSync(tmp, Buffer.from(b64, "base64"));
            newParts.push({ type: "text", text: `[Image: ${tmp}]` });
          } catch {
            newParts.push({ type: "text", text: "[Image: paste_error]" });
          }
        } else {
          newParts.push(part);
        }
      }
      if (imgIndex > 0) msg.parts = newParts;
    }
  },
};
export default plugin;
