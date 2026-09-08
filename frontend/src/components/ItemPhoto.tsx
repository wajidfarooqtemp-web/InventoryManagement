export function ItemPhoto({ name, imageUrl }: { name: string; imageUrl: string | null }) {
  if (imageUrl) {
    return <img src={imageUrl} alt={name} className="w-full h-32 object-cover rounded-t-lg" />
  }
  return (
    <div className="w-full h-32 rounded-t-lg bg-cream-dark flex items-center justify-center">
      <span className="font-heading text-3xl text-ink-soft">{name.charAt(0).toUpperCase()}</span>
    </div>
  )
}