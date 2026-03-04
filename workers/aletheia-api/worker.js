/* global URL, Headers, Request, fetch */
// Aletheia API CloudFlare Worker
// Routes requests to the appropriate Lambda Function URL.
//
// Agent Lambda: handles POST / (analysis requests)
// Auth Lambda: handles /auth/*, /admin/*, /metrics, /my-data, /redeem-coupon,
//              /upgrade-*, /create-checkout-session, /stripe-webhook, /subscription-status
//
// Issue #433: Added /admin/* and /auth/github/* routing to Auth Lambda.

const AGENT_LAMBDA = "vq2uf4fnxgpqpmhqsmsqe5osma0htrgs.lambda-url.us-east-1.on.aws";
const AUTH_LAMBDA = "sk33bz56yi5qlbrrwzqnprmeuy0xwhzn.lambda-url.us-east-1.on.aws";

const AUTH_PREFIXES = ["/auth/", "/admin/", "/metrics", "/my-data", "/redeem-coupon",
  "/upgrade-", "/create-checkout-session", "/stripe-webhook", "/subscription-status"];

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;

    const isAuthRoute = AUTH_PREFIXES.some(prefix => path.startsWith(prefix));
    url.hostname = isAuthRoute ? AUTH_LAMBDA : AGENT_LAMBDA;

    const newHeaders = new Headers(request.headers);
    newHeaders.set("X-Origin-Secret", env.ORIGIN_SECRET);

    return fetch(new Request(url, {
      method: request.method,
      headers: newHeaders,
      body: request.body,
      redirect: "manual",
    }));
  }
};
