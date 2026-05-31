// Aethyro app config — PUBLIC values (safe in the browser). RLS protects data.
// Loaded as a classic script AFTER ./vendor/supabase.js (which defines the
// global `supabase` library). No external CDN at runtime.
(function () {
  var SUPABASE_URL  = "https://uzmdqbtflcpikjdrggqc.supabase.co";
  var SUPABASE_ANON = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV6bWRxYnRmbGNwaWtqZHJnZ3FjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU2ODQxOTgsImV4cCI6MjA5MTI2MDE5OH0.BwNVBJCbw9SG-ge7PfmoIW8q_33k-ZQlqpDHa2HrvHI";
  if (!window.supabase || !window.supabase.createClient) {
    window.AETHYRO_LOADERR = "supabase library failed to load (vendor/supabase.js)";
    return;
  }
  window.AETHYRO = {
    supabase: window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON),
    PLANS: {
      personal: { label: "Personal", price: "$29/mo" },
      research: { label: "Research", price: "$199/mo" },
      dev:      { label: "Dev",      price: "$299/mo" },
      cpa:      { label: "CPA",      price: "$499/mo" },
    },
  };
})();
