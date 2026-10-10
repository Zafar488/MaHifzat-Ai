import React from 'react'

interface MaternalHealthIllustrationProps {
  className?: string
}

export const MaternalHealthIllustration: React.FC<MaternalHealthIllustrationProps> = ({ className = '' }) => {
  return (
    <div className={`relative flex items-center justify-center ${className}`}>
      {/* Ambient background glow */}
      <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-teal-200/40 via-sky-100/50 to-teal-100/30 blur-2xl transform -scale-95 pointer-events-none" />

      <svg
        viewBox="0 0 520 420"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-auto max-w-[480px] drop-shadow-sm select-none"
        aria-label="Illustration of a maternal health team supporting a mother and child"
      >
        <defs>
          {/* Gradients */}
          <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#f0fdfa" />
            <stop offset="100%" stopColor="#e0f2fe" />
          </linearGradient>
          <linearGradient id="tealShield" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#0f766e" />
            <stop offset="100%" stopColor="#0d9488" />
          </linearGradient>
          <linearGradient id="blueAccent" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#0284c7" />
            <stop offset="100%" stopColor="#38bdf8" />
          </linearGradient>
          <linearGradient id="warmSun" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#fef3c7" />
            <stop offset="100%" stopColor="#fde68a" />
          </linearGradient>
          <filter id="softShadow" x="-10%" y="-10%" width="120%" height="120%">
            <feDropShadow dx="0" dy="4" stdDeviation="6" floodColor="#0f766e" floodOpacity="0.08" />
          </filter>
        </defs>

        {/* Backdrop Soft Organic Circle */}
        <circle cx="260" cy="210" r="185" fill="url(#bgGrad)" />
        <circle cx="260" cy="210" r="170" fill="#ffffff" opacity="0.6" />

        {/* Decorative Sun / Warm Heart Backdrop */}
        <circle cx="260" cy="90" r="45" fill="url(#warmSun)" className="animate-pulse-subtle" />

        {/* Pulse / Heartbeat Line Background Motif */}
        <path
          d="M100 230 H170 L185 200 L200 255 L215 215 L230 230 H420"
          stroke="#0f766e"
          strokeOpacity="0.12"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* FLOATING MICRO-ELEMENT: Health Shield Badge */}
        <g className="animate-gentle-float" style={{ animationDelay: '0s' }}>
          <rect x="75" y="110" width="54" height="62" rx="16" fill="#ffffff" filter="url(#softShadow)" />
          <path d="M102 125 C102 125 117 128 117 140 C117 152 102 160 102 160 C102 160 87 152 87 140 C87 128 102 125 102 125 Z" fill="url(#tealShield)" />
          <path d="M102 133 V147 M95 140 H109" stroke="#ffffff" strokeWidth="2.5" strokeLinecap="round" />
        </g>

        {/* FLOATING MICRO-ELEMENT: Reassuring Heart */}
        <g className="animate-gentle-float" style={{ animationDelay: '1.5s' }}>
          <rect x="390" y="125" width="48" height="48" rx="14" fill="#ffffff" filter="url(#softShadow)" />
          <path d="M414 153 C414 153 426 145 426 138 C426 133 422 130 417.5 130 C415 130 414 132 414 132 C414 132 413 130 410.5 130 C406 130 402 133 402 138 C402 145 414 153 414 153 Z" fill="#e11d48" />
        </g>

        {/* FLOATING MICRO-ELEMENT: Medical Clipboard / Care Badge */}
        <g className="animate-gentle-float" style={{ animationDelay: '0.8s' }}>
          <rect x="395" y="270" width="50" height="56" rx="12" fill="#ffffff" filter="url(#softShadow)" />
          <rect x="407" y="282" width="26" height="4" rx="2" fill="#0284c7" />
          <rect x="407" y="292" width="20" height="4" rx="2" fill="#94a3b8" />
          <rect x="407" y="302" width="24" height="4" rx="2" fill="#94a3b8" />
          <circle cx="401" cy="284" r="2.5" fill="#0f766e" />
          <circle cx="401" cy="294" r="2.5" fill="#0f766e" />
          <circle cx="401" cy="304" r="2.5" fill="#0f766e" />
        </g>

        {/* --- MAIN CHARACTERS --- */}

        {/* CHARACTER 1: Lady Health Worker / Clinician (Right) */}
        <g id="clinician">
          {/* Body / Coat */}
          <path d="M330 360 C330 295 345 255 375 255 C405 255 420 295 420 360 Z" fill="#0f766e" />
          {/* Inner Shirt */}
          <path d="M365 255 L375 285 L385 255 Z" fill="#ffffff" />
          {/* Stethoscope */}
          <path d="M360 262 C360 280 390 280 390 262" stroke="#0284c7" strokeWidth="3.5" strokeLinecap="round" fill="none" />
          <circle cx="375" cy="285" r="4.5" fill="#0284c7" />
          {/* Head */}
          <circle cx="375" cy="225" r="24" fill="#fbcfe8" />
          {/* Hair / Headscarf */}
          <path d="M351 225 C351 202 360 195 375 195 C390 195 399 202 399 225 C399 248 395 258 375 258 C355 258 351 248 351 225 Z" fill="#0d9488" opacity="0.9" />
          {/* Face Reassuring Smile */}
          <path d="M370 230 Q375 234 380 230" stroke="#881337" strokeWidth="2" strokeLinecap="round" fill="none" />
          <circle cx="368" cy="223" r="2" fill="#881337" />
          <circle cx="382" cy="223" r="2" fill="#881337" />
        </g>

        {/* CHARACTER 2: Father / Partner (Left) */}
        <g id="father">
          {/* Body / Shirt */}
          <path d="M100 360 C100 290 115 250 145 250 C175 250 190 290 190 360 Z" fill="#0284c7" />
          {/* Collar */}
          <path d="M135 250 L145 270 L155 250 Z" fill="#ffffff" />
          {/* Head */}
          <circle cx="145" cy="218" r="23" fill="#fed7aa" />
          {/* Hair */}
          <path d="M125 215 C125 198 135 192 145 192 C155 192 165 198 165 215 C165 218 162 205 145 205 C128 205 125 218 125 215 Z" fill="#1e293b" />
          {/* Reassuring Smile */}
          <path d="M140 224 Q145 228 150 224" stroke="#451a03" strokeWidth="2" strokeLinecap="round" fill="none" />
          <circle cx="138" cy="217" r="2" fill="#451a03" />
          <circle cx="152" cy="217" r="2" fill="#451a03" />
        </g>

        {/* CHARACTER 3 & 4: Mother & Baby (Center) */}
        <g id="mother-baby">
          {/* Mother Body / Dress */}
          <path d="M200 360 C200 280 220 235 260 235 C300 235 320 280 320 360 Z" fill="#f43f5e" />
          {/* Dupatta / Shawl */}
          <path d="M215 260 C215 240 235 235 260 235 C285 235 305 240 305 260 C305 310 215 310 215 260 Z" fill="#fb7185" opacity="0.85" />
          {/* Mother Head */}
          <circle cx="260" cy="195" r="25" fill="#fde68a" />
          {/* Mother Hair / Dupatta drape */}
          <path d="M235 195 C235 168 245 162 260 162 C275 162 285 168 285 195 C285 220 280 235 260 235 C240 235 235 220 235 195 Z" fill="#e11d48" opacity="0.95" />
          {/* Mother Face Smile */}
          <path d="M254 202 Q260 207 266 202" stroke="#881337" strokeWidth="2" strokeLinecap="round" fill="none" />
          <circle cx="252" cy="194" r="2" fill="#881337" />
          <circle cx="268" cy="194" r="2" fill="#881337" />

          {/* Baby in Arms */}
          <g id="baby">
            {/* Swaddle Blanket */}
            <ellipse cx="260" cy="300" rx="28" ry="36" transform="rotate(-15 260 300)" fill="#67e8f9" />
            <path d="M242 280 Q260 295 278 280" stroke="#ffffff" strokeWidth="2.5" fill="none" />
            {/* Baby Head */}
            <circle cx="250" cy="275" r="14" fill="#fde68a" />
            {/* Baby Cap */}
            <path d="M236 275 C236 263 242 260 250 260 C258 260 264 263 264 275 Z" fill="#38bdf8" />
            {/* Sleeping eyes */}
            <path d="M244 276 Q247 279 250 276" stroke="#78350f" strokeWidth="1.5" strokeLinecap="round" fill="none" />
            <path d="M252 276 Q255 279 258 276" stroke="#78350f" strokeWidth="1.5" strokeLinecap="round" fill="none" />
          </g>

          {/* Mother's Arms Holding Baby */}
          <path d="M225 285 C225 315 295 315 295 285" stroke="#fda4af" strokeWidth="12" strokeLinecap="round" fill="none" />
        </g>

        {/* Foreground Ground Curve */}
        <path d="M40 360 Q260 380 480 360 V420 H40 Z" fill="#f0fdfa" opacity="0.8" />
      </svg>
    </div>
  )
}
