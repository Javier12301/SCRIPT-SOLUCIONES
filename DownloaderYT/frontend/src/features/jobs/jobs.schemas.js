import { z } from "zod";
import { splitUrls } from "../../utils/jobs.js";

const urlSchema = z.string().trim().url("Ingresa una URL valida");

export const downloadSchema = z
  .object({
    mode: z.enum(["single", "multi"]),
    url: z.string().trim().optional(),
    urlsText: z.string().optional(),
    outputProfile: z.enum(["video_mp4", "audio_mp3"]),
    quality: z.string().optional(),
    cookiesPath: z.string().trim().optional(),
    extraOptions: z.string().trim().optional(),
  })
  .superRefine((data, ctx) => {
    if (data.mode === "single") {
      const result = urlSchema.safeParse(data.url || "");
      if (!result.success) ctx.addIssue({ code: "custom", path: ["url"], message: "Ingresa una URL valida" });
    }
    if (data.mode === "multi") {
      const urls = splitUrls(data.urlsText || "");
      if (!urls.length) ctx.addIssue({ code: "custom", path: ["urlsText"], message: "Ingresa al menos una URL" });
      urls.forEach((url, index) => {
        if (!urlSchema.safeParse(url).success) ctx.addIssue({ code: "custom", path: ["urlsText"], message: `URL invalida en linea ${index + 1}` });
      });
    }
  });
