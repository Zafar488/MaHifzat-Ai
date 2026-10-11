import React from 'react'

interface MaternalHealthIllustrationProps {
  className?: string
}

export const MaternalHealthIllustration: React.FC<MaternalHealthIllustrationProps> = ({ className = '' }) => {
  return (
    <div className={`relative flex items-center justify-center ${className}`}>
      {/* Ambient background glow */}
      <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-teal-200/40 via-sky-100/50 to-rose-100/40 blur-2xl transform -scale-95 pointer-events-none" />

      <svg
        viewBox="0 0 580 420"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-auto max-w-[540px] drop-shadow-md select-none"
        aria-label="Animated illustration of child, doctor, nurse, and parents united in maternal healthcare"
      >
        <defs>
          {/* Gradients */}
          <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#f0fdfa" />
            <stop offset="50%" stopColor="#f0f9ff" />
            <stop offset="100%" stopColor="#fff1f2" />
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
            <feDropShadow dx="0" dy="4" stdDeviation="6" floodColor="#0f766e" floodOpacity="0.1" />
          </filter>
        </defs>

        {/* Backdrop Soft Organic Circle */}
        <circle cx="290" cy="210" r="195" fill="url(#bgGrad)" />
        <circle cx="290" cy="210" r="180" fill="#ffffff" opacity="0.65" />

        {/* Decorative Sun / Warm Heart Backdrop */}
        <circle cx="290" cy="85" r="48" fill="url(#warmSun)" className="animate-pulse-subtle" />

        {/* Pulse / Heartbeat Line Background Motif */}
        <path
          d="M60 230 H140 L155 200 L170 255 L185 215 L200 230 H520"
          stroke="#0f766e"
          strokeOpacity="0.16"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* FLOATING MICRO-ELEMENT 1: Health Shield Badge */}
        <g className="animate-gentle-float" style={{ animationDelay: '0s' }}>
          <rect x="45" y="100" width="56" height="64" rx="16" fill="#ffffff" filter="url(#softShadow)" />
          <path d="M73 115 C73 115 88 118 88 130 C88 142 73 150 73 150 C73 150 58 142 58 130 C58 118 73 115 73 115 Z" fill="url(#tealShield)" />
          <path d="M73 123 V137 M66 130 H80" stroke="#ffffff" strokeWidth="2.5" strokeLinecap="round" />
        </g>

        {/* FLOATING MICRO-ELEMENT 2: Reassuring Floating Heart */}
        <g className="animate-gentle-float" style={{ animationDelay: '1.2s' }}>
          <rect x="475" y="110" width="50" height="50" rx="15" fill="#ffffff" filter="url(#softShadow)" />
          <path d="M500 139 C500 139 512 131 512 124 C512 119 508 116 503.5 116 C501 116 500 118 500 118 C500 118 499 116 496.5 116 C492 116 488 119 488 124 C488 131 500 139 500 139 Z" fill="#e11d48" />
        </g>

        {/* FLOATING MICRO-ELEMENT 3: Care Clipboard Badge */}
        <g className="animate-gentle-float" style={{ animationDelay: '0.6s' }}>
          <rect x="480" y="265" width="52" height="58" rx="12" fill="#ffffff" filter="url(#softShadow)" />
          <rect x="492" y="277" width="28" height="4" rx="2" fill="#0284c7" />
          <rect x="492" y="287" width="22" height="4" rx="2" fill="#94a3b8" />
          <rect x="492" y="297" width="25" height="4" rx="2" fill="#94a3b8" />
          <circle cx="486" cy="279" r="2.5" fill="#0f766e" />
          <circle cx="486" cy="289" r="2.5" fill="#0f766e" />
          <circle cx="486" cy="299" r="2.5" fill="#0f766e" />
        </g>

        {/* --- MAIN CHARACTERS SCENE --- */}

        {/* CHARACTER 1: FATHER / PARENT (Far Left) */}
        <g id="father">
          <path d="M70 360 C70 290 85 250 115 250 C145 250 160 290 160 360 Z" fill="#0284c7" />
          <path d="M105 250 L115 270 L125 250 Z" fill="#ffffff" />
          <circle cx="115" cy="218" r="23" fill="#fed7aa" />
          <path d="M95 215 C95 198 105 192 115 192 C125 192 135 198 135 215 C135 218 132 205 115 205 C98 205 95 218 95 215 Z" fill="#1e293b" />
          <path d="M110 224 Q115 228 120 224" stroke="#451a03" strokeWidth="2" strokeLinecap="round" fill="none" />
          <circle cx="108" cy="217" r="2" fill="#451a03" />
          <circle cx="122" cy="217" r="2" fill="#451a03" />
        </g>

        {/* CHARACTER 2 & 3: MOTHER & CHILD / BABY (Center Left) */}
        <g id="mother-baby">
          {/* Mother Body / Dress */}
          <path d="M165 360 C165 280 185 235 225 235 C265 235 285 280 285 360 Z" fill="#f43f5e" />
          {/* Dupatta / Shawl */}
          <path d="M180 260 C180 240 200 235 225 235 C250 235 270 240 270 260 C270 310 180 310 180 260 Z" fill="#fb7185" opacity="0.85" />
          {/* Mother Head */}
          <circle cx="225" cy="195" r="25" fill="#fde68a" />
          {/* Mother Hair / Dupatta drape */}
          <path d="M200 195 C200 168 210 162 225 162 C240 162 250 168 250 195 C250 220 245 235 225 235 C205 235 200 220 200 195 Z" fill="#e11d48" opacity="0.95" />
          {/* Mother Face Smile */}
          <path d="M219 202 Q225 207 231 202" stroke="#881337" strokeWidth="2" strokeLinecap="round" fill="none" />
          <circle cx="217" cy="194" r="2" fill="#881337" />
          <circle cx="233" cy="194" r="2" fill="#881337" />

          {/* CHILD / SWADDLED NEWBORN BABY */}
          <g id="baby" className="animate-gentle-float" style={{ animationDelay: '0.4s' }}>
            <ellipse cx="225" cy="300" rx="28" ry="36" transform="rotate(-12 225 300)" fill="#67e8f9" />
            <path d="M207 280 Q225 295 243 280" stroke="#ffffff" strokeWidth="2.5" fill="none" />
            <circle cx="215" cy="275" r="14" fill="#fde68a" />
            <path d="M201 275 C201 263 207 260 215 260 C223 260 229 263 229 275 Z" fill="#38bdf8" />
            <path d="M209 276 Q212 279 215 276" stroke="#78350f" strokeWidth="1.5" strokeLinecap="round" fill="none" />
            <path d="M217 276 Q220 279 223 276" stroke="#78350f" strokeWidth="1.5" strokeLinecap="round" fill="none" />
          </g>

          {/* Mother's Arms Holding Baby */}
          <path d="M190 285 C190 315 260 315 260 285" stroke="#fda4af" strokeWidth="11" strokeLinecap="round" fill="none" />
        </g>

        {/* CHARACTER 4: NURSE / LHW (Center Right) */}
        <g id="nurse">
          {/* Body / Teal Uniform */}
          <path d="M295 360 C295 290 310 250 340 250 C370 250 385 290 385 360 Z" fill="#0d9488" />
          {/* Inner Collar */}
          <path d="M330 250 L340 272 L350 250 Z" fill="#ffffff" />
          {/* Nursing ID Badge */}
          <rect x="328" y="278" width="14" height="18" rx="3" fill="#ffffff" filter="url(#softShadow)" />
          <rect x="331" y="282" width="8" height="3" fill="#0284c7" />
          <line x1="335" y1="272" x2="335" y2="278" stroke="#94a3b8" strokeWidth="1.5" />
          {/* Head */}
          <circle cx="340" cy="218" r="23" fill="#fed7aa" />
          {/* Hair & Nursing Cap */}
          <path d="M318 215 C318 198 328 192 340 192 C352 192 362 198 362 215 C362 230 358 240 340 240 C322 240 318 230 318 215 Z" fill="#0f766e" />
          {/* White Nursing Cap Emblem */}
          <path d="M326 195 C326 186 332 182 340 182 C348 182 354 186 354 195 Z" fill="#ffffff" />
          <path d="M340 185 V191 M337 188 H343" stroke="#e11d48" strokeWidth="2" strokeLinecap="round" />
          {/* Reassuring Smile */}
          <path d="M335 224 Q340 228 345 224" stroke="#451a03" strokeWidth="2" strokeLinecap="round" fill="none" />
          <circle cx="333" cy="217" r="2" fill="#451a03" />
          <circle cx="347" cy="217" r="2" fill="#451a03" />
        </g>

        {/* CHARACTER 5: DOCTOR / SENIOR CLINICIAN (Far Right) */}
        <g id="doctor">
          {/* Body / White Lab Coat */}
          <path d="M395 360 C395 295 410 255 440 255 C470 255 485 295 485 360 Z" fill="#0f766e" />
          {/* White Coat Lapel Overlay */}
          <path d="M420 255 L440 330 L460 255 Z" fill="#ffffff" />
          {/* Inner Tie / Shirt */}
          <path d="M437 255 L440 280 L443 255 Z" fill="#0284c7" />
          {/* Stethoscope */}
          <path d="M425 262 C425 284 455 284 455 262" stroke="#0284c7" strokeWidth="3.5" strokeLinecap="round" fill="none" />
          <circle cx="440" cy="286" r="4.5" fill="#0284c7" />
          {/* Head */}
          <circle cx="440" cy="225" r="24" fill="#fbcfe8" />
          {/* Doctor Headscarf / Cap */}
          <path d="M416 225 C416 202 425 195 440 195 C455 195 464 202 464 225 C464 248 460 258 440 258 C420 258 416 248 416 225 Z" fill="#0369a1" opacity="0.9" />
          {/* Smile */}
          <path d="M435 230 Q440 234 445 230" stroke="#881337" strokeWidth="2" strokeLinecap="round" fill="none" />
          <circle cx="433" cy="223" r="2" fill="#881337" />
          <circle cx="447" cy="223" r="2" fill="#441337" />
        </g>

        {/* Foreground Ground Curve */}
        <path d="M30 365 Q290 385 550 365 V420 H30 Z" fill="#f0fdfa" opacity="0.85" />
      </svg>
    </div>
  )
}
