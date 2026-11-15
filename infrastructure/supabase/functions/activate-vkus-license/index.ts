import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const enc = new TextEncoder();
const reply = (body: unknown, status = 200) => new Response(JSON.stringify(body), {
  status, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" }
});
const hex = (b: Uint8Array) => [...b].map(x => x.toString(16).padStart(2, "0")).join("");
async function sha256(s: string) {
  return hex(new Uint8Array(await crypto.subtle.digest("SHA-256", enc.encode(s))));
}

const baseUrl = Deno.env.get("SUPABASE_URL") || "";
const secretMap = JSON.parse(Deno.env.get("SUPABASE_SECRET_KEYS") || "{}");
const publishableMap = JSON.parse(Deno.env.get("SUPABASE_PUBLISHABLE_KEYS") || "{}");
const secretKey = secretMap["default"] || Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") || "";
const publishableKey = publishableMap["default"] || Deno.env.get("SUPABASE_ANON_KEY") || "";
const legacySecret = !secretMap["default"] && !!Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");

async function adminGet(path: string) {
  const headers: Record<string,string> = { apikey: secretKey, accept: "application/json" };
  if (legacySecret) headers.authorization = "Bearer " + secretKey;
  const res = await fetch(baseUrl + "/rest/v1/" + path, { headers });
  if (!res.ok) throw new Error("license_lookup_failed");
  return await res.json();
}

const modules: Record<string,string[]> = {
  BASE: ["vk"],
  STANDARD: ["vk","telegram","odnoklassniki"],
  PREMIUM: ["vk","telegram","odnoklassniki","google","avito","yahoo"]
};

Deno.serve(async (req: Request) => {
  if (req.method !== "POST") return reply({error:"method_not_allowed"},405);
  if (!baseUrl || !secretKey || !publishableKey) return reply({error:"backend_not_configured"},503);

  const authorization = req.headers.get("authorization") || "";
  const match = authorization.match(/^Bearer\s+(.+)$/i);
  if (!match) return reply({error:"authentication_required"},401);

  const userResponse = await fetch(baseUrl + "/auth/v1/user", {
    headers: { apikey: publishableKey, authorization: "Bearer " + match[1], accept: "application/json" }
  });
  if (!userResponse.ok) return reply({error:"invalid_session"},401);
  const user = await userResponse.json();
  if (!user?.id) return reply({error:"invalid_session"},401);

  let body: any;
  try { body = await req.json(); } catch { return reply({error:"invalid_json"},400); }
  const key = String(body?.license_key || "").trim().toUpperCase();
  if (!/^VKUS-(BASE|STANDARD|PREMIUM)-[A-F0-9]{4}(?:-[A-F0-9]{4}){3}$/.test(key))
    return reply({error:"invalid_license_key"},400);

  try {
    const hash = await sha256(key);
    const rows = await adminGet(
      "vkus_licenses?select=plan_code,status,key_last4&user_id=eq." +
      encodeURIComponent(user.id) + "&key_hash=eq." + encodeURIComponent(hash) +
      "&status=eq.active&limit=1"
    );
    const license = rows?.[0];
    if (!license) return reply({error:"license_not_found_or_not_active"},404);
    return reply({
      activated: true,
      plan: license.plan_code,
      modules: modules[license.plan_code] || [],
      key_last4: license.key_last4
    },200);
  } catch {
    return reply({error:"activation_unavailable"},503);
  }
});