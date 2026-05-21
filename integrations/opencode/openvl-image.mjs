import fs from "fs";
import path from "path";

const TMP = process.env.TEMP || "C:\Users\33795\AppData\Local\Temp";

// 启动时清理旧缓存
try {
  for (const f of fs.readdirSync(TMP).filter(n => n.startsWith("openvl_img") && n.endsWith(".png"))) {
    fs.rmSync(path.join(TMP, f), { force: true });
  }
} catch {}

const plugin = async () => {
  return {
    "experimental.chat.messages.transform": async (_input, output) => {
      for (const msg of output.messages || []) {
        const parts = msg.parts;
        if (!parts) continue;
        let idx = 0;
        for (let i = 0; i < parts.length; i++) {
          const p = parts[i];
          if (p.type !== "file" || !p.mime?.startsWith("image/")) continue;
          idx++;
          const src = p.url || p.source?.path || "";
          if (!src) continue;
          const tmp = path.join(TMP, `openvl_img${idx}.png`);
          try {
            if (src.startsWith("data:")) {
              fs.writeFileSync(tmp, Buffer.from(src.split(",")[1], "base64"));
            } else if (fs.existsSync(src)) {
              fs.copyFileSync(src, tmp);
            }
            parts[i] = { type: "text", text: `[Image: ${tmp}]` };
          } catch {}
        }
      }
    }
  };
};
export default plugin;
