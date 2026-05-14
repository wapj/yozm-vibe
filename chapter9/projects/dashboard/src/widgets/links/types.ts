export interface LinkItem {
  id: string
  title: string
  url: string
}

export interface LinkSection {
  sectionId: string
  name: string
  links: LinkItem[]
}
