import { useState, useRef } from 'react'
import { useLocalStorage, storageKey } from '../../lib/storage'
import { normalizeUrl } from './normalize'
import type { LinkItem, LinkSection } from './types'
import styles from './LinksWidget.module.css'

const KEY = storageKey('links', 'sections')

function newId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

export default function LinksWidget() {
  const [sections, setSections] = useLocalStorage<LinkSection[]>(KEY, [])
  const [toast, setToast] = useState<string | null>(null)
  const toastTimer = useRef<number | null>(null)
  const [sectionInput, setSectionInput] = useState('')
  const [sectionError, setSectionError] = useState<string | null>(null)
  const [linkInputs, setLinkInputs] = useState<Record<string, { title: string; url: string }>>({})
  const [linkErrors, setLinkErrors] = useState<Record<string, string>>({})

  function showToast(msg: string) {
    if (toastTimer.current !== null) {
      clearTimeout(toastTimer.current)
    }
    setToast(msg)
    toastTimer.current = window.setTimeout(() => {
      setToast(null)
      toastTimer.current = null
    }, 3000)
  }

  function addSection(e: React.FormEvent) {
    e.preventDefault()
    const name = sectionInput.trim()
    if (!name) {
      setSectionError('섹션 이름을 입력하세요.')
      return
    }
    setSectionError(null)
    setSections(prev => [...prev, { sectionId: newId(), name, links: [] }])
    setSectionInput('')
  }

  function renameSection(sectionId: string) {
    const newName = window.prompt('새 섹션 이름을 입력하세요.')
    if (newName === null || newName.trim() === '') return
    setSections(prev =>
      prev.map(s => s.sectionId === sectionId ? { ...s, name: newName.trim() } : s)
    )
  }

  function deleteSection(sectionId: string) {
    if (!window.confirm('섹션과 모든 링크를 삭제할까요?')) return
    setSections(prev => prev.filter(s => s.sectionId !== sectionId))
  }

  function getLinkInput(sectionId: string) {
    return linkInputs[sectionId] ?? { title: '', url: '' }
  }

  function setLinkInput(sectionId: string, field: 'title' | 'url', value: string) {
    setLinkInputs(prev => ({
      ...prev,
      [sectionId]: { ...getLinkInput(sectionId), [field]: value },
    }))
  }

  function addLink(e: React.FormEvent, sectionId: string) {
    e.preventDefault()
    const { title, url } = getLinkInput(sectionId)
    const titleTrimmed = title.trim()
    const urlTrimmed = url.trim()

    if (!titleTrimmed) {
      setLinkErrors(prev => ({ ...prev, [sectionId]: '제목을 입력하세요.' }))
      return
    }
    if (!urlTrimmed) {
      setLinkErrors(prev => ({ ...prev, [sectionId]: 'URL을 입력하세요.' }))
      return
    }

    let normalized: string
    try {
      normalized = normalizeUrl(urlTrimmed)
    } catch {
      setLinkErrors(prev => ({ ...prev, [sectionId]: '올바른 URL이 아닙니다.' }))
      return
    }

    const section = sections.find(s => s.sectionId === sectionId)
    if (section && section.links.some((l: LinkItem) => {
      try { return normalizeUrl(l.url) === normalized } catch { return false }
    })) {
      showToast('이미 추가된 링크입니다.')
      return
    }

    setLinkErrors(prev => ({ ...prev, [sectionId]: '' }))
    setSections(prev =>
      prev.map(s =>
        s.sectionId === sectionId
          ? { ...s, links: [...s.links, { id: newId(), title: titleTrimmed, url: urlTrimmed }] }
          : s
      )
    )
    setLinkInputs(prev => ({ ...prev, [sectionId]: { title: '', url: '' } }))
  }

  function editLink(sectionId: string, linkId: string) {
    const section = sections.find(s => s.sectionId === sectionId)
    if (!section) return
    const link = section.links.find((l: LinkItem) => l.id === linkId)
    if (!link) return

    const newTitle = window.prompt('링크 제목:', link.title)
    const newUrl = window.prompt('링크 URL:', link.url)

    let updatedTitle = link.title
    let updatedUrl = link.url

    if (newTitle !== null && newTitle.trim() !== '') {
      updatedTitle = newTitle.trim()
    }

    if (newUrl !== null && newUrl.trim() !== '' && newUrl.trim() !== link.url) {
      const urlTrimmed = newUrl.trim()
      let normalized: string
      try {
        normalized = normalizeUrl(urlTrimmed)
      } catch {
        showToast('올바른 URL이 아닙니다.')
        return
      }
      const isDuplicate = section.links.some((l: LinkItem) => {
        if (l.id === linkId) return false
        try { return normalizeUrl(l.url) === normalized } catch { return false }
      })
      if (isDuplicate) {
        showToast('이미 추가된 링크입니다.')
        return
      }
      updatedUrl = urlTrimmed
    }

    setSections(prev =>
      prev.map(s =>
        s.sectionId === sectionId
          ? {
              ...s,
              links: s.links.map((l: LinkItem) =>
                l.id === linkId ? { ...l, title: updatedTitle, url: updatedUrl } : l
              ),
            }
          : s
      )
    )
  }

  function deleteLink(sectionId: string, linkId: string) {
    setSections(prev =>
      prev.map(s =>
        s.sectionId === sectionId
          ? { ...s, links: s.links.filter((l: LinkItem) => l.id !== linkId) }
          : s
      )
    )
  }

  return (
    <div className={styles.card}>
      <h2 className={styles.title}>링크</h2>
      <form className={styles.form} onSubmit={addSection}>
        <input
          className={styles.input}
          value={sectionInput}
          onChange={e => setSectionInput(e.target.value)}
          placeholder="섹션 이름"
        />
        <button type="submit">추가</button>
      </form>
      {sectionError && <div className={styles.error}>{sectionError}</div>}
      {sections.length === 0 && <div className={styles.empty}>섹션을 추가하세요.</div>}
      {sections.map(section => (
        <section key={section.sectionId} className={styles.section}>
          <header className={styles.sectionHeader}>
            <span className={styles.sectionName}>{section.name}</span>
            <button onClick={() => renameSection(section.sectionId)}>이름변경</button>
            <button onClick={() => deleteSection(section.sectionId)}>삭제</button>
          </header>
          <ul className={styles.list}>
            {section.links.map((link: LinkItem) => (
              <li key={link.id} className={styles.item}>
                <a href={link.url} target="_blank" rel="noreferrer">{link.title}</a>
                <button onClick={() => editLink(section.sectionId, link.id)}>편집</button>
                <button
                  className={styles.deleteBtn}
                  aria-label="삭제"
                  onClick={() => deleteLink(section.sectionId, link.id)}
                >×</button>
              </li>
            ))}
          </ul>
          <form className={styles.linkForm} onSubmit={e => addLink(e, section.sectionId)}>
            <input
              className={styles.input}
              value={getLinkInput(section.sectionId).title}
              onChange={e => setLinkInput(section.sectionId, 'title', e.target.value)}
              placeholder="제목"
            />
            <input
              className={styles.input}
              value={getLinkInput(section.sectionId).url}
              onChange={e => setLinkInput(section.sectionId, 'url', e.target.value)}
              placeholder="URL"
            />
            <button type="submit">추가</button>
          </form>
          {linkErrors[section.sectionId] && (
            <div className={styles.error}>{linkErrors[section.sectionId]}</div>
          )}
        </section>
      ))}
      {toast && <div className={styles.toast}>{toast}</div>}
    </div>
  )
}
