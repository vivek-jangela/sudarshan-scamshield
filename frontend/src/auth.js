// FRONTEND-ONLY mock authentication (localStorage). Replace with server-side login (JWT/session) in the final build.
// Keep the same function names so the UI does not change: signup, login, logout, current.
const USERS = "ss_users", SESSION = "ss_session";
const hash = async s => [...new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode("ss:" + s)))].map(b => b.toString(16).padStart(2, "0")).join("");
const users = () => JSON.parse(localStorage.getItem(USERS) || "[]");
const start = r => { const s = { name: r.name, email: r.email, role: r.role, officerId: r.officerId, district: r.district }; localStorage.setItem(SESSION, JSON.stringify(s)); return s; };
export async function signup({ password, ...u }) {
  u.email = u.email.trim().toLowerCase();
  if (users().some(x => x.email === u.email)) throw new Error("An account with this email already exists. Please log in.");
  const rec = { ...u, pw: await hash(password) };
  localStorage.setItem(USERS, JSON.stringify([...users(), rec])); return start(rec);
}
export async function login(email, password) {
  const r = users().find(x => x.email === email.trim().toLowerCase());
  if (!r || r.pw !== await hash(password)) throw new Error("Invalid email or password.");
  return start(r);
}
export const current = () => JSON.parse(localStorage.getItem(SESSION) || "null");
export const logout = () => localStorage.removeItem(SESSION);
