interface TagFilterProps {
  tags: string[]
  selectedTags: string[]
  onToggle: (tag: string) => void
}

export function TagFilter({ tags, selectedTags, onToggle }: TagFilterProps) {
  if (tags.length === 0) return null

  return (
    <div className="tag-filter" role="group" aria-label="태그 필터">
      {tags.map((tag) => {
        const isSelected = selectedTags.includes(tag)
        return (
          <button
            key={tag}
            type="button"
            className={`tag-filter__item${isSelected ? ' tag-filter__item--active' : ''}`}
            aria-pressed={isSelected}
            onClick={() => onToggle(tag)}
          >
            {tag}
          </button>
        )
      })}
    </div>
  )
}
