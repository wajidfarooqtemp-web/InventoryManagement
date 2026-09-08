// Product photos come in Phase 10 (secure upload). Until an item has a
// real image_path, this shows a calm placeholder instead of a broken
// image icon - the item's initial, not a generic box icon, so cards
// still feel specific to the actual product.
export function ItemPhoto({ name, imagePath }: { name: string; imagePath: string | null }) {
  if (imagePath) {
    // Phase 10 will resolve this to a real signed URL - structure is
    // ready for it, just not wired up yet.
    return <img src={imagePath} alt={name} className="w-full h-32 object-cover rounded-t-lg" />
  }

  return (
    <div className="w-full h-32 rounded-t-lg bg-cream-dark flex items-center justify-center">
      <span className="font-heading text-3xl text-ink-soft">{name.charAt(0).toUpperCase()}</span>
    </div>
  )
}