export default function BrandMark({ compact = false }) {
  return (
    <span className={`brandmark ${compact ? "compact" : ""}`} aria-hidden="true">
      <svg viewBox="0 0 64 72" role="img" focusable="false">
        <path d="M32 3 57 12v21c0 17-10 28-25 36C17 61 7 50 7 33V12L32 3Z"
          fill="#f7fbff" stroke="#f39a2e" strokeWidth="3.2" strokeLinejoin="round"/>
        <path d="M32 9 51 16v17c0 13-7.5 22.5-19 30-11.5-7.5-19-17-19-30V16L32 9Z"
          fill="#12366b" stroke="#d7e5f6" strokeWidth="1.2"/>
        <path d="M20 27h5l7 8 7-8h5v19h-5V34l-7 8-7-8v12h-5Z" fill="#fff"/>
        <path d="M23 21h18" stroke="#f39a2e" strokeWidth="2.5" strokeLinecap="round"/>
        <circle cx="32" cy="55" r="2.2" fill="#f39a2e"/>
      </svg>
    </span>
  );
}
