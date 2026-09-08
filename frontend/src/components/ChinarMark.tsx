// A small, original line-art mark inspired by a chinar leaf - the one
// recurring brand element, used sparingly (header, login) rather than as
// a big illustration. Deliberately simple and hand-drawn-feeling.
export function ChinarMark({ className = 'w-6 h-6' }: { className?: string }) {
  return (
    <svg viewBox="0 0 48 48" fill="none" className={className} xmlns="http://www.w3.org/2000/svg">
      <path
        d="M24 44V28M24 28C24 28 10 24 8 10C8 10 18 10 24 20C24 10 30 4 40 6C40 6 38 18 28 24C36 22 42 30 40 36C40 36 30 34 26 26C28 32 26 40 24 44Z"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}