import request from './request'

export const statisticsApi = {
  getOverview: () => request.get('/statistics/overview'),
  getEarthquakeStats: (params) => request.get('/statistics/earthquake', params),
  getAcademicStats: (params) => request.get('/statistics/academic', params),
  getCrawlStats: (params) => request.get('/statistics/crawl', params)
}

export const articleApi = {
  getList: (params) => request.get('/articles', params),
  getById: (id) => request.get(`/articles/${id}`),
  getWithTranslation: (id) => request.get(`/articles/${id}/detail`),
  translateContent: (id) => request.get(`/articles/${id}/translate`),
  translateTitle: (id) => request.get(`/articles/${id}/title`),
  search: (q, params) => request.get('/articles/search/', { q, ...params }),
  delete: (id) => request.delete(`/articles/${id}`),
  getSources: () => request.get('/articles/sources/list')
}

export const datasourceApi = {
  getList: (params) => request.get('/datasources', params),
  getById: (id) => request.get(`/datasources/${id}`),
  create: (data) => request.post('/datasources', data),
  update: (id, data) => request.put(`/datasources/${id}`, data),
  delete: (id) => request.delete(`/datasources/${id}`),
  triggerCrawl: (id) => request.post(`/datasources/${id}/crawl`),
  toggle: (id) => request.post(`/datasources/${id}/toggle`)
}

export const earthquakeApi = {
  getList: (params) => request.get('/earthquakes', params),
  getById: (id) => request.get(`/earthquakes/${id}`)
}
