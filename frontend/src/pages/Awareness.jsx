const SCAMS = [
  ["Fake KYC / account block", "Messages saying your bank KYC, PAN or Aadhaar will expire and your account will be blocked.", "Banks never ask you to update KYC through a link. Visit the branch or the official app."],
  ["Parcel and customs fee", "A courier or India Post message asking for a small fee to release a held parcel.", "Check the tracking number on the official courier site. Never pay through a link."],
  ["Electricity bill disconnection", "A message that power will be cut tonight unless you pay or call a number.", "Check your bill on the official discom portal or app. Utilities do not threaten same-night cut-offs by SMS."],
  ["Task and job scams", "Part-time work, 'like videos and earn', or a deposit to unlock higher task earnings.", "Genuine employers never ask you to pay to earn. Leave the Telegram or WhatsApp group."],
  ["Fake instant-loan apps", "Apps outside the Play Store that ask for SMS, contacts and gallery access, then harass you.", "Install only RBI-registered lenders' apps. Deny contacts, SMS and call-log permissions."],
  ["Investment, Ponzi and MLM", "Guaranteed or very high returns, referral bonuses and level income.", "No legal investment guarantees high returns. Check SEBI registration before investing."],
  ["Illegal betting platforms", "IPL IDs, colour prediction and casino sites with instant bonuses and UPI deposits.", "Online betting is a crime in most forms. Accounts are often frozen when scammers are traced."],
];
const DO = ["Verify through the official website or app typed by you", "Check the sender and the exact domain spelling", "Report suspicious items on ScamShield and cybercrime.gov.in", "Call 1930 immediately if money is lost"];
const DONT = ["Share OTP, PIN, CVV or passwords with anyone", "Install apps from links or APK files on chat", "Pay a fee to receive a loan, prize, parcel or job", "Trust urgency, threats or claims of police and court action"];
export default function Awareness() {
  return (
    <>
      <h1>Scam awareness</h1>
      <p className="lede">The most common cyber frauds reported in India, how to recognise them and what to do. Share this with family, especially senior citizens.</p>
      <div className="tiles two">{SCAMS.map(([t, s, a]) => <div className="card tilecard" key={t}><h3>{t}</h3><p>{s}</p><p className="act"><b>What to do:</b> {a}</p></div>)}</div>
      <div className="grid2">
        <div className="card good"><h3>Do</h3><ul>{DO.map(x => <li key={x}>{x}</li>)}</ul></div>
        <div className="card bad"><h3>Do not</h3><ul>{DONT.map(x => <li key={x}>{x}</li>)}</ul></div>
      </div>
      <div className="card rule"><h3>Helplines and official channels</h3>
        <table><tbody><tr><th>National Cyber Crime Helpline</th><td><b>1930</b></td></tr><tr><th>Online complaint portal</th><td>cybercrime.gov.in</td></tr><tr><th>Emergency</th><td><b>112</b></td></tr></tbody></table>
      </div>
    </>
  );
}
