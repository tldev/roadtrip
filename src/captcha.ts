export async function verifyCaptcha(token: string | undefined, ip: string): Promise<boolean> {
  const secret = process.env.HCAPTCHA_SECRET;
  if (!secret) {
    if (!warned) {
      console.warn(
        "[hcaptcha] HCAPTCHA_SECRET not set — bypassing captcha verification. DEV ONLY.",
      );
      warned = true;
    }
    return true;
  }
  if (!token) return false;
  const params = new URLSearchParams({ secret, response: token, remoteip: ip });
  try {
    const r = await fetch("https://hcaptcha.com/siteverify", {
      method: "POST",
      body: params,
      headers: { "content-type": "application/x-www-form-urlencoded" },
    });
    const j = (await r.json()) as { success?: boolean };
    return Boolean(j.success);
  } catch (err) {
    console.error("[hcaptcha] verify failed:", err);
    return false;
  }
}

let warned = false;
