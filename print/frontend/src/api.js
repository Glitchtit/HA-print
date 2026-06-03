import axios from 'axios'

// Derive the ingress base path from the injected meta tag (nginx sub_filter),
// falling back to parsing the URL. Outside HA ingress this is just ''.
function getIngressPath() {
  const meta = document.querySelector('meta[name="ingress-path"]')?.content
  if (meta) return meta
  const m = window.location.pathname.match(/^(\/api\/hassio_ingress\/[^/]+)/)
  return m ? m[1] : ''
}

const api = axios.create({ baseURL: `${getIngressPath()}/api` })

export const getHealth = () => api.get('/health').then((r) => r.data)

export const printImage = (body) => api.post('/print/image', body).then((r) => r.data)
export const printSvg = (body) => api.post('/print/svg', body).then((r) => r.data)

export const listTemplates = () => api.get('/templates').then((r) => r.data)
export const getTemplate = (id) => api.get(`/templates/${id}`).then((r) => r.data)
export const saveTemplate = (body) => api.post('/templates', body).then((r) => r.data)
export const deleteTemplate = (id) => api.delete(`/templates/${id}`).then((r) => r.data)
