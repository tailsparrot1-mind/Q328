import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const enc = new TextEncoder();
const reply = (body: unknown, status = 200) => new Response(JSON.stringify(body), {
  status, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" }
});
const hex = (b: Uint8Array) => [...b].map(x => x.toString(16).padStart(2, "0")).join("");
const b64 = (b: Uint8Array) => {
  let s = ""; for (const x of b) s += String.fromCharCode(x); return btoa(s);
};
const un64 = (s: string) => Uint8Array.from(atob(s), c => c.charCodeAt(0));
const equal = (a: string, b: string) => {
  if (a.length !== b.length) return false;
  let v = 0; for (let i = 0; i < a.length; i++) v |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return v === 0;
};
async function digest(s: string) {
  return hex(new Uint8Array(await crypto.subtle.digest("SHA-256", enc.encode(s))));
}
async function hmac(secret: string, body: string) {
  const k = await crypto.subtle.importKey("raw", enc.encode(secret), { name: "HMAC", hash: "SHA-1" }, false, ["sign"]);
  return hex(new Uint8Array(await crypto.subtle.sign("HMAC", k, enc.encode(body))));
}
async function encrypt(s: string, secret: string) {
  const raw = un64(secret); if (raw.length !== 32) throw new Error("invalid_encryption_key");
  const k = await crypto.subtle.importKey("raw", raw, "AES-GCM", false, ["encrypt"]);
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const data = await crypto.subtle.encrypt({ name: "AES-GCM", iv }, k, enc.encode(s));
  return { ciphertext: b64(new Uint8Array(data)), iv: b64(iv) };
}
async function decrypt(ciphertext: string, iv: string, secret: string) {
  const raw = un64(secret); if (raw.length !== 32) throw new Error("invalid_encryption_key");
  const k = await crypto.subtle.importKey("raw", raw, "AES-GCM", false, ["decrypt"]);
  const data = await crypto.subtle.decrypt({ name: "AES-GCM", iv: un64(iv) }, k, un64(ciphertext));
  return new TextDecoder().decode(data);
}
function makeKey(plan: string) {
  const b = crypto.getRandomValues(new Uint8Array(16));
  const s = hex(b).toUpperCase();
  return "VKUS-" + plan + "-" + s.slice(0,4) + "-" + s.slice(4,8) + "-" + s.slice(8,12) + "-" + s.slice(12,16);
}
function esc(s: string) {
  return s.replace(/[&<>"']/g, c => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;" }[c]!));
}

const baseUrl = Deno.env.get("SUPABASE_URL") || "";
const secretMap = JSON.parse(Deno.env.get("SUPABASE_SECRET_KEYS") || "{}");
const apiKey = secretMap["default"] || Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") || "";
const legacy = !secretMap["default"] && !!Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
async function db(path: string, method = "GET", body?: unknown, prefer?: string) {
  const headers: Record<string,string> = { apikey: apiKey, accept: "application/json" };
  if (legacy) headers.authorization = "Bearer " + apiKey;
  if (body !== undefined) headers["content-type"] = "application/json";
  if (prefer) headers.prefer = prefer;
  const res = await fetch(baseUrl + "/rest/v1/" + path, {
    method, headers, body: body === undefined ? undefined : JSON.stringify(body)
  });
  const txt = await res.text();
  if (!res.ok) throw new Error("db_http_" + res.status);
  return txt ? JSON.parse(txt) : null;
}
async function queueReview(orderRef: string, reason: string, email: string | null, candidates: string[],
  amount: number | null, currency: string | null, raw: string) {
  await db("vkus_payment_review_queue?on_conflict=provider,provider_payment_id", "POST", {
    provider:"taplink", provider_payment_id:orderRef, payer_email:email,
    email_candidates:candidates, amount_rub:amount, currency_code:currency,
    reason_code:reason, payload_digest:await digest(raw), review_status:"pending"
  }, "resolution=ignore-duplicates,return=minimal");
}

async function sendEmail(to: string, key: string, plan: string, token: string, from: string) {
  const res = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: { authorization: "Bearer " + token, "content-type": "application/json" },
    body: JSON.stringify({
      from, to: [to], subject: "Лицензия Vkus " + plan,
      text: "Оплата подтверждена.\n\nВаш ключ Vkus " + plan + ":\n" + key + "\n\nВведите его в окне активации Vkus.",
      html: "<p>Оплата подтверждена.</p><p>Ваш ключ Vkus <b>" + esc(plan) + "</b>:</p><p><strong>" + esc(key) + "</strong></p><p>Введите его в окне активации Vkus.</p>"
    })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error("mail_http_" + res.status);
  return String(data.id || "");
}

const plans: Record<string,{code:string,amount:number}> = {
  "79900": { code:"BASE", amount:79900 },
  "174000": { code:"STANDARD", amount:174000 },
  "238000": { code:"PREMIUM", amount:238000 }
};

Deno.serve(async (req: Request) => {
  if (req.method !== "POST") return reply({error:"method_not_allowed"},405);
  const tapSecret = Deno.env.get("TAPLINK_WEBHOOK_SECRET") || "";
  const encryptionSecret = Deno.env.get("LICENSE_ENCRYPTION_KEY") || "";
  const resend = Deno.env.get("RESEND_API_KEY") || "";
  const from = Deno.env.get("LICENSE_EMAIL_FROM") || "";
  if (!baseUrl || !apiKey || !tapSecret || !encryptionSecret || !resend || !from)
    return reply({error:"billing_secrets_not_configured"},503);

  const raw = await req.text();
  if (raw.length > 65536) return reply({error:"payload_too_large"},413);
  const supplied = (req.headers.get("taplink-signature") || "").trim().toLowerCase();
  if (!supplied || !equal(supplied, await hmac(tapSecret,raw))) return reply({error:"invalid_signature"},401);

  let payload: any;
  try { payload = JSON.parse(raw); } catch { return reply({error:"invalid_json"},400); }
  const data = payload?.data || payload;
  const statusId = String(data?.order_status_id || "");
  const orderRef = String(data?.order_id || data?.order_number || "").trim();
  const emailCandidates = [
    data.email,
    ...(Array.isArray(data.records) ? data.records
      .filter((item: any) => String(item?.type || "") === "6" ||
        /email|e-mail|электронн/i.test(String(item?.title || "")))
      .map((item: any) => item?.value) : []),
    ...(Array.isArray(data.records_extended) ? data.records_extended
      .filter((item: any) => /email|e-mail|электронн/i.test(String(item?.name || "")))
      .map((item: any) => item?.value) : [])
  ].map(value => String(value || "").trim().toLowerCase()).filter(Boolean);
  const uniqueEmails = [...new Set(emailCandidates)];
  const email = uniqueEmails.length === 1 ? uniqueEmails[0] : "";

  // A signed Taplink refund event must revoke the matching Vkus license.
  if (statusId === "5") {
    if (!orderRef || orderRef.length > 128 || (email && email.length > 320))
      return reply({error:"refund_data_mismatch"},422);
    try {
      await db("vkus_payment_events?on_conflict=provider,provider_event_id", "POST", {
        provider:"taplink", provider_event_id:orderRef + ":refund",
        order_id:null, event_type:"payment.refunded", payload_digest:await digest(raw)
      }, "resolution=ignore-duplicates,return=minimal");
      const rows = await db("vkus_license_orders?select=id,customer_email,amount_rub,status&provider=eq.taplink&provider_payment_id=eq." +
        encodeURIComponent(orderRef) + "&limit=1");
      const order = rows?.[0];
      if (!order) return reply({accepted:true,processed:true,refund_pending:true},200);
      if ((email && String(order.customer_email).trim().toLowerCase() !== email) ||
          Number(order.amount_rub) !== Number(data.budget))
        return reply({error:"refund_order_mismatch"},409);
      await db("vkus_license_orders?id=eq." + encodeURIComponent(order.id), "PATCH", {
        status:"refunded", updated_at:new Date().toISOString()
      }, "return=minimal");
      await db("vkus_licenses?order_id=eq." + encodeURIComponent(order.id) + "&status=eq.active", "PATCH", {
        status:"revoked", revoked_at:new Date().toISOString()
      }, "return=minimal");
      const licenseRows = await db("vkus_licenses?select=id&order_id=eq." + encodeURIComponent(order.id) + "&limit=1");
      if (licenseRows?.[0]?.id) {
        await db("vkus_license_delivery?license_id=eq." + encodeURIComponent(licenseRows[0].id) +
          "&delivery_status=eq.pending", "PATCH", {
            delivery_status:"failed", last_error_code:"payment_refunded",
            updated_at:new Date().toISOString()
          }, "return=minimal");
      }
      return reply({accepted:true,processed:true,refunded:true},200);
    } catch (e) {
      console.error("taplink_refund_webhook_failed", e instanceof Error ? e.message : "internal_error");
      return reply({error:"refund_processing_failed"},503);
    }
  }

  if (statusId !== "2") return reply({accepted:true,processed:false},200);
  if (!orderRef || orderRef.length > 128)
    return reply({error:"payment_reference_invalid"},422);

  const amount = Number(data.budget);
  const currency = String(data.currency_code || "").trim().toUpperCase();
  const plan = plans[String(Math.round(amount))];
  if (uniqueEmails.length !== 1) {
    try {
      await queueReview(orderRef, uniqueEmails.length ? "email_ambiguous" : "email_missing",
        null, uniqueEmails, Number.isFinite(amount) ? amount : null, currency || null, raw);
      return reply({accepted:true,processed:true,manual_review:true},202);
    } catch { return reply({error:"manual_review_queue_failed"},503); }
  }
  if (!email || email.length > 320 || !Number.isFinite(amount) || !plan ||
      Math.abs(amount-plan.amount) > 0.001 || (currency !== "RUB" && currency !== "643")) {
    try {
      await queueReview(orderRef, "amount_or_currency_mismatch", email || null, uniqueEmails,
        Number.isFinite(amount) ? amount : null, currency || null, raw);
      return reply({accepted:true,processed:true,manual_review:true},202);
    } catch { return reply({error:"manual_review_queue_failed"},503); }
  }

  try {
    const ids = await db("vkus_billing_identities?select=user_id&verified_email=eq." + encodeURIComponent(email) + "&limit=2");
    if (!Array.isArray(ids) || ids.length !== 1) {
      await queueReview(orderRef, "email_not_matched_to_verified_account", email, uniqueEmails,
        amount, currency, raw);
      return reply({accepted:true,processed:true,manual_review:true},202);
    }
    const userId = ids[0].user_id;
    const refundMarkers = await db("vkus_payment_events?select=id&provider=eq.taplink&provider_event_id=eq." +
      encodeURIComponent(orderRef + ":refund") + "&limit=1");
    if (refundMarkers?.length) return reply({error:"payment_already_refunded"},409);

    const query = "vkus_license_orders?select=id,user_id,plan_code,amount_rub,customer_email,status,license_key_hash,license_key_last4,encrypted_license_key,license_key_iv&provider=eq.taplink&provider_payment_id=eq." + encodeURIComponent(orderRef) + "&limit=1";
    let orders = await db(query);
    let order = orders?.[0];

    if (!order) {
      const key = makeKey(plan.code);
      const material = await encrypt(key,encryptionSecret);
      const inserted = await db("vkus_license_orders?on_conflict=provider,provider_payment_id","POST",{
        user_id:userId, plan_code:plan.code, amount_rub:plan.amount, currency_code:"RUB",
        customer_email:email, status:"paid", provider:"taplink", provider_payment_id:orderRef,
        paid_at:new Date().toISOString(), license_key_hash:await digest(key),
        license_key_last4:key.slice(-4), encrypted_license_key:material.ciphertext, license_key_iv:material.iv
      },"resolution=ignore-duplicates,return=representation");
      order = inserted?.[0];
      if (!order) { orders = await db(query); order = orders?.[0]; }
    }
    if (!order || order.user_id !== userId || order.plan_code !== plan.code ||
        Number(order.amount_rub) !== plan.amount || String(order.customer_email).toLowerCase() !== email)
      return reply({error:"order_replay_mismatch"},409);
    if (order.status !== "paid") return reply({error:"order_not_payable"},409);
    if (!order.license_key_hash || !order.encrypted_license_key || !order.license_key_iv)
      throw new Error("license_material_missing");

    await db("vkus_payment_events?on_conflict=provider,provider_event_id","POST",{
      provider:"taplink", provider_event_id:orderRef, order_id:order.id,
      event_type:String(payload.action || "payment.paid").slice(0,80), payload_digest:await digest(raw)
    },"resolution=ignore-duplicates,return=minimal");

    await db("vkus_licenses?on_conflict=order_id","POST",{
      order_id:order.id,user_id:userId,plan_code:plan.code,
      key_hash:order.license_key_hash,key_last4:order.license_key_last4,status:"active"
    },"resolution=ignore-duplicates,return=minimal");

    const licenses = await db("vkus_licenses?select=id,key_hash,status&order_id=eq." + encodeURIComponent(order.id) + "&limit=1");
    const license = licenses?.[0];
    if (!license || license.key_hash !== order.license_key_hash || license.status !== "active")
      throw new Error("license_persist_failed");
    const lateRefund = await db("vkus_payment_events?select=id&provider=eq.taplink&provider_event_id=eq." +
      encodeURIComponent(orderRef + ":refund") + "&limit=1");
    if (lateRefund?.length) {
      await db("vkus_license_orders?id=eq." + encodeURIComponent(order.id), "PATCH",
        {status:"refunded",updated_at:new Date().toISOString()}, "return=minimal");
      await db("vkus_licenses?order_id=eq." + encodeURIComponent(order.id) + "&status=eq.active", "PATCH",
        {status:"revoked",revoked_at:new Date().toISOString()}, "return=minimal");
      return reply({accepted:true,processed:true,refunded:true},200);
    }

    await db("vkus_license_delivery?on_conflict=license_id","POST",{
      license_id:license.id,encrypted_key:order.encrypted_license_key,
      encryption_iv:order.license_key_iv,delivery_status:"pending"
    },"resolution=ignore-duplicates,return=minimal");

    const deliveries = await db("vkus_license_delivery?select=id,delivery_status,attempts&license_id=eq." + encodeURIComponent(license.id) + "&limit=1");
    const delivery = deliveries?.[0];
    if (!delivery) throw new Error("delivery_queue_failed");
    if (delivery.delivery_status === "sent") return reply({accepted:true,processed:true,delivered:true},200);
    const preSendRefund = await db("vkus_payment_events?select=id&provider=eq.taplink&provider_event_id=eq." +
      encodeURIComponent(orderRef + ":refund") + "&limit=1");
    if (preSendRefund?.length) {
      await db("vkus_licenses?order_id=eq." + encodeURIComponent(order.id) + "&status=eq.active", "PATCH",
        {status:"revoked",revoked_at:new Date().toISOString()}, "return=minimal");
      await db("vkus_license_orders?id=eq." + encodeURIComponent(order.id), "PATCH",
        {status:"refunded",updated_at:new Date().toISOString()}, "return=minimal");
      return reply({accepted:true,processed:true,refunded:true},200);
    }

    // Atomically claim the delivery row. Concurrent webhook retries cannot send a second email.
    const staleBefore = encodeURIComponent(new Date(Date.now() - 15 * 60 * 1000).toISOString());
    const claim = await db("vkus_license_delivery?id=eq." + encodeURIComponent(delivery.id) +
      "&or=(delivery_status.eq.pending,delivery_status.eq.failed,and(delivery_status.eq.sending,last_attempt_at.lt." +
      staleBefore + "))", "PATCH", {
        delivery_status:"sending",
        attempts:Number(delivery.attempts || 0)+1,
        last_attempt_at:new Date().toISOString(),
        updated_at:new Date().toISOString()
      }, "return=representation");
    if (!Array.isArray(claim) || claim.length !== 1)
      return reply({accepted:true,processed:true,delivery_in_progress:true},202);

    try {
      const key = await decrypt(order.encrypted_license_key,order.license_key_iv,encryptionSecret);
      const messageId = await sendEmail(email,key,plan.code,resend,from);
      await db("vkus_license_delivery?id=eq." + encodeURIComponent(delivery.id) +
        "&delivery_status=eq.sending","PATCH",{
          delivery_status:"sent",provider_message_id:messageId || null,
          sent_at:new Date().toISOString(),last_error_code:null,updated_at:new Date().toISOString()
        },"return=minimal");
      return reply({accepted:true,processed:true,delivered:true},200);
    } catch (mailError) {
      await db("vkus_license_delivery?id=eq." + encodeURIComponent(delivery.id) +
        "&delivery_status=eq.sending","PATCH",{
          delivery_status:"failed",
          last_error_code:"email_delivery_failed",
          updated_at:new Date().toISOString()
        },"return=minimal").catch(() => null);
      throw mailError;
    }
  } catch (e) {
    console.error("taplink_payment_webhook_failed", e instanceof Error ? e.message : "internal_error");
    return reply({error:"processing_failed"},503);
  }
});