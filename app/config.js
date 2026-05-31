// Aethyro app config — these are PUBLIC values (safe in the browser).
// Row-level security on the database is what actually protects data.
export const SUPABASE_URL  = "https://uzmdqbtflcpikjdrggqc.supabase.co";
export const SUPABASE_ANON  = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV6bWRxYnRmbGNwaWtqZHJnZ3FjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU2ODQxOTgsImV4cCI6MjA5MTI2MDE5OH0.BwNVBJCbw9SG-ge7PfmoIW8q_33k-ZQlqpDHa2HrvHI";

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON);

export const PLANS = {
  personal: { label: "Personal", price: "$29/mo" },
  research: { label: "Research", price: "$199/mo" },
  dev:      { label: "Dev",      price: "$299/mo" },
  cpa:      { label: "CPA",      price: "$499/mo" },
};
