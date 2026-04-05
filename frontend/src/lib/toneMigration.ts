const LEGACY_TONE_MAP: Record<string, string> = {
  spring_warm_mute: "spring_warm_light",
  autumn_warm_bright: "autumn_warm_strong",
  winter_cool_bright: "winter_cool_vivid",
  winter_cool_light: "winter_cool_strong",
};

export function migrateLegacyTones(): void {
  if (typeof window === "undefined") return;
  for (const key of ["colorfit_tone", "colorfit_tone_id"]) {
    const current = localStorage.getItem(key);
    if (current && LEGACY_TONE_MAP[current]) {
      localStorage.setItem(key, LEGACY_TONE_MAP[current]);
    }
  }
}
